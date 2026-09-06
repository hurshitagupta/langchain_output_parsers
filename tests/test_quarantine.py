import json

import pytest
from pydantic import ValidationError

import quarantine.quarantine as module
from schema_definition.schema_definition import Review


class SuccessChain:
    def invoke(self, inputs):
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


def test_quarantine_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        module,
        "QUARANTINE_DIR",
        tmp_path,
    )

    result = module.analyse_feedback(
        "The movie was good.",
        active_chain=SuccessChain(),
    )

    assert isinstance(result, Review)

    files = list(tmp_path.iterdir())

    assert len(files) == 0


def test_quarantine_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        module,
        "QUARANTINE_DIR",
        tmp_path,
    )

    with pytest.raises(
        RuntimeError,
        match="quarantined",
    ):
        module.analyse_feedback(
            "The movie was good.",
            active_chain=AlwaysFailChain(),
        )

    files = list(tmp_path.glob("*.json"))

    assert len(files) == 1

    data = json.loads(
        files[0].read_text(encoding="utf-8")
    )

    assert data["feedback"] == "The movie was good."
    assert data["attempts"] == 2
    assert "score" in data["error"]