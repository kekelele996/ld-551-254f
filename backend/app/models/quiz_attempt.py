from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizAttempt(Base):
    """学员测验提交记录，每次提交一行，用于保留历史最高分与最近一次成绩。"""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    progress_id: Mapped[int] = mapped_column(ForeignKey("lesson_progress.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    progress = relationship("LessonProgress", back_populates="quiz_attempts")
