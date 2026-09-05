import pytest

import structured_output.structured_output as module
from schema_definition.schema_definition import Review, Sentiment


class FakeChain:
    def invoke(self, inputs: dict) -> Review:
        return Review(
            sentiment="positive",
            score=0.9,
            reasons=["Good acting"],
        )


def test_structured_output_success(monkeypatch) -> None:
    monkeypatch.setattr(module, "chain", FakeChain())

    result = module.analyse_feedback(
        "The movie was nice and the acting was good."
    )

    assert isinstance(result, Review)
    assert result.sentiment == Sentiment.POSITIVE
    assert result.score == 0.9
    assert result.reasons == ["Good acting"]


def test_structured_output_failure_empty_input() -> None:
    with pytest.raises(ValueError, match="Feedback cannot be empty"):
        module.analyse_feedback("")