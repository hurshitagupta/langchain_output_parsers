import time

from quarantine.quarantine import analyse_feedback
from schema_definition.schema_definition import Review


TOTAL_RUNS = 50

TEST_FEEDBACK = (
    "The movie was enjoyable, the acting was strong, "
    "but some scenes felt slow."
)


def measure_parse_success(parser=analyse_feedback, runs=TOTAL_RUNS):
    if runs <= 0:
        raise ValueError("Runs must be greater than 0.")

    successes = 0
    failures = 0
    total_latency = 0

    for run_number in range(1, runs + 1):
        print(f"Run {run_number}/{runs}")

        start = time.perf_counter()

        try:
            result = parser(TEST_FEEDBACK)

            if not isinstance(result, Review):
                raise TypeError("Parser returned an invalid result.")

            successes += 1
            print("Parse successful.")

        except Exception as exc:
            failures += 1
            print(f"Parse failed: {exc}")

        total_latency += time.perf_counter() - start

    success_rate = (successes / runs) * 100
    average_latency = total_latency / runs

    return {
        "total_runs": runs,
        "successes": successes,
        "failures": failures,
        "success_rate": success_rate,
        "average_latency": average_latency,
    }


def main():
    metrics = measure_parse_success()

    print()
    print("=== FAILURE METRICS ===")
    print(f"Total runs: {metrics['total_runs']}")
    print(f"Successful parses: {metrics['successes']}")
    print(f"Failed parses: {metrics['failures']}")
    print(f"Parse success rate: {metrics['success_rate']:.2f}%")
    print(f"Average latency: {metrics['average_latency']:.3f} seconds")


if __name__ == "__main__":
    main()