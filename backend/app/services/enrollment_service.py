from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.constants.enums import LessonType
from app.constants.lesson import QUIZ_PASS_SCORE, QUIZ_SCORE_POLICY, QuizScorePolicy
from app.exceptions.course import CourseNotFoundException
from app.exceptions.lesson import LessonValidationException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.services.audit_service import AuditService


def is_passed_quiz(lesson: Lesson, score: int | None) -> bool:
    """测验课时是否通过：分数达到及格线。视频/文本课时不按分数判定。"""
    return lesson.type == LessonType.QUIZ and score is not None and score >= QUIZ_PASS_SCORE


def is_progress_completed(lesson: Lesson, progress: LessonProgress | None) -> bool:
    """课时是否计入已完成：视频/文本有记录即完成；测验需历史最高分及格。"""
    if not progress:
        return False
    if lesson.type == LessonType.QUIZ:
        return is_passed_quiz(lesson, progress.score)
    return True


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
    def _get_enrollment_for_lesson(db: Session, user: User, lesson: Lesson) -> Enrollment:
        course_id = lesson.chapter.course_id
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise CourseNotFoundException("尚未注册该课程")
        return enrollment

    @staticmethod
    def complete_lesson(db: Session, user: User, lesson_id: int, ip_address: str | None = None) -> Enrollment:
        """标记视频/文本课时完成。测验课时必须走 submit_quiz。"""
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        if lesson.type == LessonType.QUIZ:
            raise LessonValidationException("测验课时需提交答卷评分，不能直接标记完成")
        enrollment = EnrollmentService._get_enrollment_for_lesson(db, user, lesson)
        progress = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id, lesson_id=lesson_id).first()
        if not progress:
            progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id)
            db.add(progress)
            db.flush()
            AuditService.record(db, user_id=user.id, action="CREATE", entity="LessonProgress", entity_id=str(progress.id), after_data={"lesson_id": lesson_id}, ip_address=ip_address)
        enrollment.last_access_at = datetime.now(UTC)
        EnrollmentService.recalculate_progress(db, enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def submit_quiz(db: Session, user: User, lesson_id: int, score: int, ip_address: str | None = None) -> Enrollment:
        """提交测验。

        计分口径：历史最高分（QUIZ_SCORE_POLICY=HIGHEST）——重做考砸进度不掉。
        每次提交都记录 QuizAttempt；LessonProgress.score 始终保存历史最高分。
        最高分达到 60 分才算该测验课时通过并计入已完成/结业。
        """
        if not 0 <= score <= 100:
            raise LessonValidationException("测验分数必须在 0-100 之间")
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        if lesson.type != LessonType.QUIZ:
            raise LessonValidationException("非测验课时不能提交测验分数")
        enrollment = EnrollmentService._get_enrollment_for_lesson(db, user, lesson)
        progress = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id, lesson_id=lesson_id).first()
        if not progress:
            progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id, score=score)
            db.add(progress)
            db.flush()
        # 历史最高分口径：新分数只在高于历史最高分时更新
        if QUIZ_SCORE_POLICY == QuizScorePolicy.HIGHEST:
            effective_score = score if progress.score is None else max(progress.score, score)
        else:
            effective_score = score
        progress.score = effective_score
        attempt = QuizAttempt(progress_id=progress.id, score=score)
        db.add(attempt)
        db.flush()
        AuditService.record(
            db,
            user_id=user.id,
            action="CREATE",
            entity="QuizAttempt",
            entity_id=str(attempt.id),
            after_data={"lesson_id": lesson_id, "score": score, "best_score": effective_score, "passed": effective_score >= QUIZ_PASS_SCORE},
            ip_address=ip_address,
        )
        enrollment.last_access_at = datetime.now(UTC)
        EnrollmentService.recalculate_progress(db, enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_course_lessons(db: Session, course_id: int) -> list[Lesson]:
        return (
            db.query(Lesson)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.sort_order, Lesson.sort_order, Lesson.id)
            .all()
        )

    @staticmethod
    def get_progress_detail(db: Session, user: User, course_id: int):
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise CourseNotFoundException("尚未注册该课程")
        lessons = EnrollmentService.get_course_lessons(db, course_id)
        progress_map = {
            item.lesson_id: item
            for item in db.query(LessonProgress)
            .options(joinedload(LessonProgress.quiz_attempts))
            .filter(LessonProgress.enrollment_id == enrollment.id)
            .all()
        }
        items = []
        completed = 0
        failed_quiz_count = 0
        for lesson in lessons:
            record = progress_map.get(lesson.id)
            attempts = list(record.quiz_attempts) if record else []
            latest_score = attempts[-1].score if attempts else None
            passed = is_progress_completed(lesson, record)
            if passed:
                completed += 1
            if lesson.type == LessonType.QUIZ and record is not None and not passed:
                failed_quiz_count += 1
            items.append(
                {
                    "lesson_id": lesson.id,
                    "completed": passed,
                    "passed": passed,
                    "score": record.score if record else None,
                    "best_score": record.score if record else None,
                    "latest_score": latest_score,
                    "attempts": len(attempts),
                    "completed_at": record.completed_at if (record and passed) else None,
                }
            )
        return enrollment, len(lessons), completed, failed_quiz_count, items

    @staticmethod
    def get_progress(db: Session, user: User, course_id: int):
        return EnrollmentService.get_progress_detail(db, user, course_id)

    @staticmethod
    def recalculate_progress(db: Session, enrollment: Enrollment) -> None:
        """按当前课程课时与每条课时完成情况重算总进度与结业状态。

        测验课时以历史最高分判定是否通过（60 分及格），未及格不计入已完成。
        """
        lessons = EnrollmentService.get_course_lessons(db, enrollment.course_id)
        progress_map = {
            item.lesson_id: item
            for item in db.query(LessonProgress).filter_by(enrollment_id=enrollment.id).all()
        }
        total = len(lessons)
        completed = sum(1 for lesson in lessons if is_progress_completed(lesson, progress_map.get(lesson.id)))
        was_completed = enrollment.is_completed
        enrollment.progress = round((completed / total) * 100, 2) if total else 0
        enrollment.is_completed = total > 0 and completed == total
        if enrollment.is_completed and not was_completed:
            enrollment.completed_at = datetime.now(UTC)
        if not enrollment.is_completed:
            enrollment.completed_at = None

    @staticmethod
    def recalculate_course_enrollments(db: Session, course_id: int) -> None:
        """课程课时增减/删除后，重算该课程全部已注册学员的进度与结业状态。"""
        enrollments = db.query(Enrollment).filter_by(course_id=course_id).all()
        for enrollment in enrollments:
            EnrollmentService.recalculate_progress(db, enrollment)
