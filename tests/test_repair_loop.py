import pytest
from pydantic import ValidationError

from repair_loop.repair_loop import analyse_feedback
from schema_definition.schema_definition import Review


class RepairSuccessChain:
    def __init__(self):
        self.calls = 0

    def invoke(self, inputs):
        self.calls += 1

        if self.calls == 1:
            Review(
                sentiment="positive",
                score=5,
                reasons=["Good acting"],
            )

        return Review(
            sentiment="positive",
            score=0.9,
            reasons=["Good acting"],
        )


class AlwaysFailChain:
    def invoke(self, inputs):
        return Review(
            sentiment="positive",
            score=5,
            reasons=["Good acting"],
        )


def test_repair_success_after_one_failure() -> None:
    fake_chain = RepairSuccessChain()

    result = analyse_feedback(
        "The movie was good.",
        repair_chain=fake_chain,
    )

    assert isinstance(result, Review)
    assert result.score == 0.9
    assert fake_chain.calls == 2


def test_repair_failure_after_max_attempts() -> None:
    fake_chain = AlwaysFailChain()

    with pytest.raises(
        RuntimeError,
        match="Parse failed after 2 attempts",
    ):
        analyse_feedback(
            "The movie was good.",
            repair_chain=fake_chain,
        )