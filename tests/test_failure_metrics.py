from failure_metrics.failure_metrics import measure_parse_success
from schema_definition.schema_definition import Review


call_count = 0


def fake_mixed_parser(feedback):
    global call_count

    call_count += 1

    if call_count in (2, 4):
        raise RuntimeError("Simulated parse failure.")

    return Review(
        sentiment="positive",
        score=0.9,
        reasons=["Good acting"],
    )


def fake_failed_parser(feedback):
    raise RuntimeError("Simulated parse failure.")


def test_success_rate():
    global call_count
    call_count = 0

    metrics = measure_parse_success(
        parser=fake_mixed_parser,
        runs=5,
    )

    assert metrics["total_runs"] == 5
    assert metrics["successes"] == 3
    assert metrics["failures"] == 2
    assert metrics["success_rate"] == 60.0


def test_failure_rate():
    metrics = measure_parse_success(
        parser=fake_failed_parser,
        runs=5,
    )

    assert metrics["total_runs"] == 5
    assert metrics["successes"] == 0
    assert metrics["failures"] == 5
    assert metrics["success_rate"] == 0.0