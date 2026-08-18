from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.domain.entities import ReviewRating, ReviewStatus
from app.schemas.common import ApiModel
from app.schemas.flashcards import FlashcardResponse, ScheduleSnapshotResponse


class ReviewStart(ApiModel):
    model_config = ConfigDict(extra="forbid")

    deck_id: UUID


class ReviewRatingCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    command_id: UUID
    card_id: UUID
    rating: ReviewRating


class ReviewSessionResponse(ApiModel):
    id: str
    deck_id: str
    category_id_snapshot: str | None
    status: ReviewStatus
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ReviewEventResponse(ApiModel):
    id: str
    command_id: str
    review_session_id: str
    card_id: str
    sequence: int
    rating: ReviewRating
    quality: int
    reviewed_at: datetime
    previous_schedule: ScheduleSnapshotResponse
    new_schedule: ScheduleSnapshotResponse


class ReviewProgressResponse(ApiModel):
    session: ReviewSessionResponse
    reviewed_card_count: int
    remaining_due_card_count: int
    next_card: FlashcardResponse | None


class ReviewRatingResultResponse(ApiModel):
    event: ReviewEventResponse
    progress: ReviewProgressResponse
