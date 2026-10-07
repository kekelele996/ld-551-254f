from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.constants.enums import LessonType
from app.constants.rules import QUIZ_PASSING_SCORE
from app.exceptions.course import CourseNotFoundException
from app.exceptions.progress import InvalidQuizSubmissionException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.user import User
from app.schemas.enrollment import LessonCompleteResponse, LessonProgressState
from app.services.audit_service import AuditService


class EnrollmentService:
    @staticmethod
    def enroll(db: Session, user: User, course: Course, ip_address: str | None = None) -> Enrollment:
        existing = db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).first()
        if existing:
            return existing
        enrollment = Enrollment(user_id=user.id, course_id=course.id)
        db.add(enrollment)
        course.student_count += 1
        db.flush()
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Enrollment", entity_id=str(enrollment.id), after_data={"course_id": course.id}, ip_address=ip_address)
        return enrollment

    @staticmethod
    def list_user_enrollments(db: Session, user: User) -> list[Enrollment]:
        return (
            db.query(Enrollment)
            .options(joinedload(Enrollment.course).joinedload(Course.instructor))
            .filter(Enrollment.user_id == user.id)
            .order_by(Enrollment.last_access_at.desc())
            .all()
        )

    @staticmethod
    def complete_lesson(db: Session, user: User, lesson_id: int, score: int | None = None, ip_address: str | None = None) -> LessonCompleteResponse:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        course_id = lesson.chapter.course_id
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise CourseNotFoundException("尚未注册该课程")
        progress = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id, lesson_id=lesson_id).first()
        now = datetime.now(UTC)

        if lesson.type == LessonType.QUIZ:
            if score is None or not 0 <= score <= 100:
                raise InvalidQuizSubmissionException()
            if not progress:
                progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id, attempts=0)
                db.add(progress)
                db.flush()
                AuditService.record(db, user_id=user.id, action="CREATE", entity="LessonProgress", entity_id=str(progress.id), after_data={"lesson_id": lesson_id, "score": score}, ip_address=ip_address)
            else:
                AuditService.record(db, user_id=user.id, action="UPDATE", entity="LessonProgress", entity_id=str(progress.id), before_data={"score": progress.score, "attempts": progress.attempts}, after_data={"lesson_id": lesson_id, "score": score}, ip_address=ip_address)
            progress.attempts += 1
            # 按历史最高分计：重做考砸不会拉低分数与进度
            progress.score = max(progress.score or 0, score)
            if progress.score >= QUIZ_PASSING_SCORE and progress.completed_at is None:
                progress.completed_at = now
        else:
            if not progress:
                progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id, completed_at=now)
                db.add(progress)
                db.flush()
                AuditService.record(db, user_id=user.id, action="CREATE", entity="LessonProgress", entity_id=str(progress.id), after_data={"lesson_id": lesson_id}, ip_address=ip_address)
            elif progress.completed_at is None:
                progress.completed_at = now

        enrollment.last_access_at = now
        EnrollmentService.recalculate_progress(db, enrollment)
        db.commit()
        db.refresh(enrollment)
        passed = progress.completed_at is not None
        return LessonCompleteResponse(
            enrollment_id=enrollment.id,
            course_id=course_id,
            lesson_id=lesson_id,
            status="completed" if passed else "failed",
            score=score,
            best_score=progress.score,
            passed=passed,
            progress=enrollment.progress,
            is_completed=enrollment.completed_at is not None,
            passing_score=QUIZ_PASSING_SCORE,
        )

    @staticmethod
    def get_progress(db: Session, user: User, course_id: int) -> tuple[Enrollment, int, int, list[LessonProgressState]]:
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise CourseNotFoundException("尚未注册该课程")
        lessons = (
            db.query(Lesson)
            .join(Chapter)
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.sort_order, Lesson.sort_order, Lesson.id)
            .all()
        )
        records = {item.lesson_id: item for item in db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).all()}
        states: list[LessonProgressState] = []
        completed = 0
        for lesson in lessons:
            record = records.get(lesson.id)
            if record and record.completed_at is not None:
                status = "completed"
                completed += 1
            elif record and lesson.type == LessonType.QUIZ:
                # 有提交记录但未达到及格线：标为未及格，不计入已完成
                status = "failed"
            else:
                status = "pending"
            states.append(
                LessonProgressState(
                    lesson_id=lesson.id,
                    status=status,
                    best_score=record.score if record else None,
                    attempts=record.attempts if record else 0,
                    completed_at=record.completed_at if record else None,
                )
            )
        return enrollment, completed, len(lessons), states

    @staticmethod
    def recalculate_progress(db: Session, enrollment: Enrollment) -> None:
        db.flush()  # 会话为 autoflush=False，先落盘本次修改再统计
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == enrollment.course_id).count()
        # 只统计课时仍存在且已达到完成标准（completed_at 非空）的记录
        completed = (
            db.query(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(
                LessonProgress.enrollment_id == enrollment.id,
                Chapter.course_id == enrollment.course_id,
                LessonProgress.completed_at.isnot(None),
            )
            .count()
        )
        enrollment.progress = round((completed / total) * 100, 2) if total else 0
        if total > 0 and completed >= total:
            if enrollment.completed_at is None:
                enrollment.completed_at = datetime.now(UTC)
        else:
            enrollment.completed_at = None

    @staticmethod
    def recalculate_course_progress(db: Session, course_id: int) -> None:
        """课程课时增减后，重算该课程全部已注册学员的进度与结业状态。"""
        enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
        for enrollment in enrollments:
            EnrollmentService.recalculate_progress(db, enrollment)
