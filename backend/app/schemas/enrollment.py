from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.course import CourseResponse

LessonStatus = Literal["completed", "failed", "pending"]


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    progress: float
    last_access_at: datetime
    completed_at: datetime | None = None
    course: CourseResponse | None = None

    model_config = {"from_attributes": True}


class LessonProgressCreate(BaseModel):
    lesson_id: int
    score: int | None = Field(default=None, ge=0, le=100)


class LessonProgressState(BaseModel):
    lesson_id: int
    status: LessonStatus
    best_score: int | None = None
    attempts: int = 0
    completed_at: datetime | None = None


class ProgressResponse(BaseModel):
    enrollment_id: int
    course_id: int
    progress: float
    completed_lessons: int
    total_lessons: int
    is_completed: bool
    passing_score: int
    lessons: list[LessonProgressState] = Field(default_factory=list)


class LessonCompleteResponse(BaseModel):
    enrollment_id: int
    course_id: int
    lesson_id: int
    status: LessonStatus
    score: int | None = None
    best_score: int | None = None
    passed: bool
    progress: float
    is_completed: bool
    passing_score: int
