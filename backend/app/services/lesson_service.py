from sqlalchemy.orm import Session

from app.exceptions.course import CourseNotFoundException
from app.models.chapter import Chapter
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.schemas.chapter import ChapterCreate
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.services.audit_service import AuditService
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService


class LessonService:
    @staticmethod
    def create_chapter(db: Session, payload: ChapterCreate) -> Chapter:
        chapter = Chapter(**payload.model_dump())
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def create_lesson(db: Session, payload: LessonCreate) -> Lesson:
        chapter = db.get(Chapter, payload.chapter_id)
        if not chapter:
            raise CourseNotFoundException("章节不存在")
        lesson = Lesson(**payload.model_dump())
        db.add(lesson)
        db.flush()
        CourseService.recalculate_course_stats(db, chapter.course_id)
        EnrollmentService.recalculate_course_progress(db, chapter.course_id)
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
    def update_lesson(db: Session, lesson_id: int, payload: LessonUpdate) -> Lesson:
        lesson = LessonService.get_lesson(db, lesson_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(lesson, key, value)
        db.flush()
        CourseService.recalculate_course_stats(db, lesson.chapter.course_id)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def delete_lesson(db: Session, lesson_id: int, user_id: int | None = None, ip_address: str | None = None) -> None:
        lesson = LessonService.get_lesson(db, lesson_id)
        course_id = lesson.chapter.course_id
        # 清理该课时的学员进度记录，避免残留数据计入进度
        db.query(LessonProgress).filter(LessonProgress.lesson_id == lesson_id).delete()
        AuditService.record(db, user_id=user_id, action="DELETE", entity="Lesson", entity_id=str(lesson_id), before_data={"title": lesson.title, "course_id": course_id}, ip_address=ip_address)
        db.delete(lesson)
        db.flush()
        CourseService.recalculate_course_stats(db, course_id)
        EnrollmentService.recalculate_course_progress(db, course_id)
        db.commit()
