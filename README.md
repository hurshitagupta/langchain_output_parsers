# LangChain Output Parsers

This assessment focuses on making LLM outputs machine-safe using structured output, schema validation, repair, quarantine, and failure measurement.

The implementation is built progressively across five tasks.

## Task 1 — Schema Definition

### Objective

Define a Pydantic schema with strict types, ranges, and enum constraints so that invalid data is rejected before it can be used by the application.

### Implementation

The `Review` schema contains:

* `sentiment` — restricted to `positive`, `negative`, `neutral`, or `mixed` using an Enum.
* `score` — a float restricted to the range `0` to `1`.
* `reasons` — a list of strings containing between 1 and 3 items.

The script demonstrates both:

* Successful creation of a valid `Review`.
* Rejection of invalid data using Pydantic validation.

### Run

```bash
uv run python -m schema_definition.schema_definition
```

### Run Tests

```bash
uv run pytest tests/test_schema_definition.py -v
```

### Evidence

Execution and test outputs are saved in:

```text
outputs/schema_definition_output.txt
outputs/schema_definition_test_output.txt
```

### Tests

Task 1 includes automated tests for:

* Successful validation of a correctly structured review.
* Failure when the review violates the defined schema constraints.

### Guardrails

Task 1 performs only local Pydantic schema validation and does not make any model or network calls.

The applicable guardrail at this stage is strict validation: invalid data is rejected with a `ValidationError` and is never treated as a valid `Review`.

API-specific controls such as timeout, retry, token budget, and API-call limits are introduced in later tasks when model calls are added.

### Task 1 Result

The schema successfully establishes a strict contract for review data. This provides the validation layer that later tasks will use to ensure that raw model output is never returned directly to the caller.
