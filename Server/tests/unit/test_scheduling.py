from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities import ReviewRating, ScheduleSnapshot
from app.domain.scheduling import RATING_QUALITY, apply_sm2

REVIEWED_AT = datetime(2026, 8, 17, 14, 31, tzinfo=UTC)


def schedule(
    *, repetitions: int = 0, interval_days: int = 0, ease_factor: float = 2.5
) -> ScheduleSnapshot:
    return ScheduleSnapshot(
        repetitions=repetitions,
        interval_days=interval_days,
        ease_factor=ease_factor,
        due_at=REVIEWED_AT - timedelta(minutes=1),
        last_reviewed_at=None,
    )


@pytest.mark.parametrize(
    ("rating", "quality", "expected_ease"),
    [
        (ReviewRating.AGAIN, 1, 1.96),
        (ReviewRating.HARD, 3, 2.36),
        (ReviewRating.GOOD, 4, 2.5),
        (ReviewRating.EASY, 5, 2.6),
    ],
)
def test_sm2_rating_matrix(rating: ReviewRating, quality: int, expected_ease: float) -> None:
    result = apply_sm2(schedule(), rating, REVIEWED_AT)

    assert RATING_QUALITY[rating] == quality
    assert result.ease_factor == pytest.approx(expected_ease)
    assert result.interval_days == 1
    assert result.repetitions == (0 if rating is ReviewRating.AGAIN else 1)
    assert result.due_at == REVIEWED_AT + timedelta(days=1)
    assert result.last_reviewed_at == REVIEWED_AT


@pytest.mark.parametrize(
    ("previous", "expected_repetitions", "expected_interval"),
    [
        (schedule(repetitions=0), 1, 1),
        (schedule(repetitions=1, interval_days=1), 2, 6),
        (schedule(repetitions=2, interval_days=6), 3, 15),
    ],
)
def test_sm2_successful_interval_progression(
    previous: ScheduleSnapshot, expected_repetitions: int, expected_interval: int
) -> None:
    result = apply_sm2(previous, ReviewRating.GOOD, REVIEWED_AT)

    assert result.repetitions == expected_repetitions
    assert result.interval_days == expected_interval
    assert result.due_at == REVIEWED_AT + timedelta(days=expected_interval)


def test_sm2_failed_review_resets_repetitions_and_interval() -> None:
    result = apply_sm2(schedule(repetitions=8, interval_days=90), ReviewRating.AGAIN, REVIEWED_AT)

    assert result.repetitions == 0
    assert result.interval_days == 1


def test_sm2_ease_has_a_1_3_floor_and_does_not_mutate_previous() -> None:
    previous = schedule(repetitions=5, interval_days=20, ease_factor=1.3)

    result = apply_sm2(previous, ReviewRating.AGAIN, REVIEWED_AT)

    assert result.ease_factor == 1.3
    assert previous.ease_factor == 1.3
    assert previous.last_reviewed_at is None
