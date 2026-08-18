from datetime import datetime, timedelta

from app.domain.entities import ReviewRating, ScheduleSnapshot

RATING_QUALITY = {
    ReviewRating.AGAIN: 1,
    ReviewRating.HARD: 3,
    ReviewRating.GOOD: 4,
    ReviewRating.EASY: 5,
}


def apply_sm2(
    previous: ScheduleSnapshot, rating: ReviewRating, reviewed_at: datetime
) -> ScheduleSnapshot:
    """Return the next SM-2 schedule without mutating the prior snapshot."""
    quality = RATING_QUALITY[rating]
    ease_factor = max(
        1.3,
        previous.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
    )

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        repetitions = previous.repetitions + 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = round(previous.interval_days * previous.ease_factor)

    return ScheduleSnapshot(
        repetitions=repetitions,
        interval_days=interval_days,
        ease_factor=ease_factor,
        due_at=reviewed_at + timedelta(days=interval_days),
        last_reviewed_at=reviewed_at,
    )
