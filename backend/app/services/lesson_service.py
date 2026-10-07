from sqlalchemy.orm import Session

from app.constants.enums import UserRole
from app.exceptions.course import CourseNotFoundException, CoursePermissionException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.quiz_attempt import QuizAttempt
from app.schemas.chapter import ChapterCreate
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService


def _ensure_course_owner(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise CourseNotFoundException("课程不存在")
    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise CoursePermissionException()
    return course


class LessonService:
    @staticmethod
    def create_chapter(db: Session, user: User, payload: ChapterCreate, ip_address: str | None = None) -> Chapter:
        _ensure_course_owner(db, payload.course_id, user)
        chapter = Chapter(**payload.model_dump())
        db.add(chapter)
        db.flush()
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Chapter", entity_id=str(chapter.id), after_data={"course_id": chapter.course_id, "title": chapter.title}, ip_address=ip_address)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def create_lesson(db: Session, user: User, payload: LessonCreate, ip_address: str | None = None) -> Lesson:
        chapter = db.get(Chapter, payload.chapter_id)
        if not chapter:
            raise CourseNotFoundException("章节不存在")
        _ensure_course_owner(db, chapter.course_id, user)
        lesson = Lesson(**payload.model_dump())
        db.add(lesson)
        db.flush()
        CourseService.recalculate_course_stats(db, chapter.course_id)
        EnrollmentService.recalculate_course_enrollments(db, chapter.course_id)
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Lesson", entity_id=str(lesson.id), after_data={"chapter_id": lesson.chapter_id, "title": lesson.title, "type": lesson.type.value}, ip_address=ip_address)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def get_lesson(db: Session, lesson_id: int) -> Lesson:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        return lesson

    @staticmethod
    def update_lesson(db: Session, user: User, lesson_id: int, payload: LessonUpdate, ip_address: str | None = None) -> Lesson:
        lesson = LessonService.get_lesson(db, lesson_id)
        _ensure_course_owner(db, lesson.chapter.course_id, user)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(lesson, key, value)
        db.flush()
        CourseService.recalculate_course_stats(db, lesson.chapter.course_id)
        AuditService.record(db, user_id=user.id, action="UPDATE", entity="Lesson", entity_id=str(lesson.id), after_data=payload.model_dump(exclude_unset=True), ip_address=ip_address)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def delete_lesson(db: Session, user: User, lesson_id: int, ip_address: str | None = None) -> None:
        lesson = LessonService.get_lesson(db, lesson_id)
        course_id = lesson.chapter.course_id
        _ensure_course_owner(db, course_id, user)
        LessonService._delete_progress_for_lessons(db, [lesson_id])
        db.delete(lesson)
        db.flush()
        CourseService.recalculate_course_stats(db, course_id)
        # 课时减少后，已注册学员的进度与结业状态跟着重算
        EnrollmentService.recalculate_course_enrollments(db, course_id)
        AuditService.record(db, user_id=user.id, action="DELETE", entity="Lesson", entity_id=str(lesson_id), before_data={"course_id": course_id}, ip_address=ip_address)
        db.commit()

    @staticmethod
    def delete_chapter(db: Session, user: User, chapter_id: int, ip_address: str | None = None) -> None:
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            raise CourseNotFoundException("章节不存在")
        course_id = chapter.course_id
        _ensure_course_owner(db, course_id, user)
        lesson_ids = [lesson.id for lesson in chapter.lessons]
        if lesson_ids:
            LessonService._delete_progress_for_lessons(db, lesson_ids)
        db.delete(chapter)
        db.flush()
        CourseService.recalculate_course_stats(db, course_id)
        # 章节下的课时一并删除，已注册学员进度跟着重算
        EnrollmentService.recalculate_course_enrollments(db, course_id)
        AuditService.record(db, user_id=user.id, action="DELETE", entity="Chapter", entity_id=str(chapter_id), before_data={"course_id": course_id}, ip_address=ip_address)
        db.commit()

    @staticmethod
    def _delete_progress_for_lessons(db: Session, lesson_ids: list[int]) -> None:
        progress_ids = [row[0] for row in db.query(LessonProgress.id).filter(LessonProgress.lesson_id.in_(lesson_ids)).all()]
        if progress_ids:
            # 先删测验提交记录，再删课时完成记录（bulk delete 不触发 ORM 级联）
            db.query(QuizAttempt).filter(QuizAttempt.progress_id.in_(progress_ids)).delete(synchronize_session=False)
            db.query(LessonProgress).filter(LessonProgress.id.in_(progress_ids)).delete(synchronize_session=False)
