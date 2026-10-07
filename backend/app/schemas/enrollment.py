from datetime import datetime

from pydantic import BaseModel, Field

from app.constants.lesson import QUIZ_PASS_SCORE, QUIZ_SCORE_POLICY
from app.schemas.course import CourseResponse


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    progress: float
    is_completed: bool = False
    completed_at: datetime | None = None
    last_access_at: datetime
    course: CourseResponse | None = None

    model_config = {"from_attributes": True}


class CompleteLessonCreate(BaseModel):
    """标记视频/文本课时完成。"""

    lesson_id: int


class QuizSubmitCreate(BaseModel):
    """提交测验，score 由测验评分结果给出（0-100）。"""

    lesson_id: int
    score: int = Field(ge=0, le=100)


class LessonProgressItem(BaseModel):
    lesson_id: int
    completed: bool
    passed: bool
    score: int | None = None
    best_score: int | None = None
    latest_score: int | None = None
    attempts: int = 0
    completed_at: datetime | None = None


class ProgressResponse(BaseModel):
    enrollment_id: int
    course_id: int
    progress: float
    is_completed: bool
    completed_lessons: int
    total_lessons: int
    passed_lessons: int
    failed_quiz_count: int
    quiz_pass_score: int = QUIZ_PASS_SCORE
    quiz_score_policy: str = QUIZ_SCORE_POLICY.value
    lesson_progress: list[LessonProgressItem] = []
