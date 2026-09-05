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
---
## Task 2 — Structured Output

### Objective

Use LangChain structured output to ensure that model responses are returned as validated `Review` objects instead of unstructured text.

### Implementation

The `Review` schema created in Task 1 is connected to the OpenRouter model using:

```python id="osr0sv"
model.with_structured_output(Review)
```

A `ChatPromptTemplate` provides the feedback to the model, while the schema ensures that the response contains:

* `sentiment`
* `score` between 0 and 1
* `reasons` containing 1 to 3 items

The application also verifies that the final result is a `Review` object before returning it.

Invalid model responses are rejected rather than being returned to the caller.

During execution, schema validation successfully caught cases where the model produced an out-of-range score or omitted the required `reasons` field.

### Guardrails

* **Timeout** — A per-call timeout is configured for the model.
* **Retry** — Model retries are capped.
* **Output limit** — Maximum output tokens are limited.
* **Input validation** — Empty and oversized feedback is rejected before the model call.
* **Schema validation** — Model output must satisfy the `Review` Pydantic schema.
* **Secret hygiene** — API key, model name, and base URL are loaded from environment variables only.

The validation repair mechanism and quarantine handling are implemented in later tasks.

### Run

```bash id="3if7io"
uv run python -m structured_output.structured_output
```

### Run Tests

```bash id="7foycf"
uv run pytest tests/test_structured_output.py -v
```

### Evidence

Execution and test outputs are saved in the `outputs/` directory:

```text id="egk6ab"
outputs/structured_output.txt
outputs/structured_output_test_output.txt
```

### Tests

Task 2 includes:

* A success case confirming that a valid `Review` object is returned.
* A failure case confirming that empty feedback is rejected.

The unit test uses a deterministic fake chain to avoid depending on an external API call, while the runnable script demonstrates the real OpenRouter integration.

### Result

Task 2 successfully converts model responses into validated Pydantic objects using LangChain structured output. Raw or schema-invalid model output is not returned directly to the caller.
