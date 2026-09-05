from enum import Enum

from pydantic import BaseModel, Field, ValidationError


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class Review(BaseModel):
    sentiment: Sentiment
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1, max_length=3)


def main() -> None:
    print("=== VALID REVIEW ===")

    valid_review = Review(
        sentiment="mixed",
        score=0.8,
        reasons=[
            "The acting was superb",
            "The plot felt slow",
        ],
    )

    print(valid_review)
    print(f"Type: {type(valid_review).__name__}")
    print()

    print("=== INVALID REVIEW ===")

    try:
        Review(
            sentiment="excellent",
            score=1.5,
            reasons=[
                "Reason 1",
                "Reason 2",
                "Reason 3",
                "Reason 4",
            ],
        )
    except ValidationError as exc:
        print("Validation rejected invalid data.")
        print(exc)


if __name__ == "__main__":
    main()
