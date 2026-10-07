from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.constants.enums import UserRole
from app.core.database import get_db
from app.models.user import User
from app.schemas.chapter import ChapterCreate, ChapterResponse
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.services.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    return LessonService.get_lesson(db, lesson_id)


@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
def create_chapter(
    payload: ChapterCreate,
    request: Request,
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return LessonService.create_chapter(db, user, payload, request.client.host if request.client else None)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(
    chapter_id: int,
    request: Request,
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    LessonService.delete_chapter(db, user, chapter_id, request.client.host if request.client else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    request: Request,
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return LessonService.create_lesson(db, user, payload, request.client.host if request.client else None)


@router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    request: Request,
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return LessonService.update_lesson(db, user, lesson_id, payload, request.client.host if request.client else None)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    request: Request,
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    LessonService.delete_lesson(db, user, lesson_id, request.client.host if request.client else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
