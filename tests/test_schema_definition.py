import pytest
from pydantic import ValidationError

from schema_definition.schema_definition import Review, Sentiment


def test_valid_review() -> None:
    review = Review(
        sentiment="positive",
        score=0.9,
        reasons=["Strong acting"],
    )

    assert isinstance(review, Review)
    assert review.sentiment == Sentiment.POSITIVE
    assert review.score == 0.9
    assert len(review.reasons) == 1


def test_invalid_review() -> None:
    with pytest.raises(ValidationError):
        Review(
            sentiment="excellent",
            score=1.5,
            reasons=["A", "B", "C", "D"],
        )





