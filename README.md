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

---

## Task 3 — Repair Loop

### Objective

Handle schema validation failures by giving the model one opportunity to repair its output while keeping the total number of attempts strictly bounded.

### Implementation

Task 3 extends the structured output implementation from Task 2 with a validation repair loop.

The maximum number of attempts is:

```python id="bzf8j7"
MAX_ATTEMPTS = 2
```

This represents:

* Attempt 1 — initial model response.
* Attempt 2 — one repair attempt after validation failure.

If the first response satisfies the `Review` schema, it is returned immediately.

If Pydantic raises a `ValidationError`, the validation error is captured and appended to the next prompt. The model is then given one opportunity to correct its response.

### Repair Message

When validation fails, the error returned by Pydantic is included in the second request so that the model knows what was wrong with its previous output.

For example, an invalid score such as:

```text id="cblrtx"
score = 5
```

can produce a validation error because the schema only allows values between `0` and `1`.

The error is then included in the repair request rather than blindly repeating the original prompt.

### Retry Types

Two different retry mechanisms are used for different failure types:

* **Model retry** — `max_retries` handles transient API/provider failures.
* **Repair retry** — `MAX_ATTEMPTS` handles schema validation failures.

The repair loop is explicitly capped at two total attempts.

### Guardrails

* **Step limit** — The repair loop is capped at `MAX_ATTEMPTS = 2`.
* **Timeout** — Model calls use a configured per-call timeout.
* **Retry** — Transient model retries are capped.
* **Output limit** — Maximum model output tokens are limited.
* **Input validation** — Empty and oversized feedback is rejected.
* **Schema validation** — Every successful result must satisfy the `Review` Pydantic schema.
* **Safe failure** — After both validation attempts fail, the function raises a `RuntimeError` rather than returning invalid output.
* **Secret hygiene** — API configuration is loaded from environment variables.

Persistent quarantine of outputs that still fail after repair is introduced in Task 4.

### Run

```bash id="xbp2ur"
uv run python -m repair_loop.repair_loop
```

### Run Tests

```bash id="kxfrvr"
uv run pytest tests/test_repair_loop.py -v
```

### Evidence

Execution and test outputs are saved in:

```text id="56b5qk"
outputs/repair_loop_output.txt
outputs/repair_loop_test_output.txt
```

### Tests

Task 3 includes two automated paths:

* **Repair success** — The first response fails validation and the second response succeeds.
* **Repair failure** — Both attempts fail validation and the function stops with a `RuntimeError`.

The success test also verifies that exactly two calls were made, proving that one repair attempt occurred.

### Result

Task 3 implements a bounded validation-repair mechanism. Invalid structured output is never returned directly to the caller. A failed response receives one repair attempt using the original validation error, and execution stops safely if the corrected response still violates the schema.

---

## Task 4 — Quarantine

### Objective

Preserve model outputs that still fail validation after the bounded repair attempt instead of silently discarding them or returning invalid data to the caller.

### Implementation

Task 4 extends the repair loop from Task 3.

The validation flow remains the same:

```text
Attempt 1
   ↓
Pydantic Validation
   ↓
If invalid → append validation error
   ↓
Attempt 2
   ↓
Pydantic Validation
```

If the second attempt also fails, the failure is written to the `quarantine/` directory before the application raises the final error.

A dedicated quarantine function:

* Creates the quarantine directory when required.
* Generates a unique JSON filename.
* Stores failure information.
* Returns the generated file path.

This keeps failure persistence separate from the parsing and repair logic.

### Quarantine Record

A quarantined failure contains information such as:

```json
{
  "feedback": "The movie was good.",
  "error": "Validation error...",
  "attempts": 2,
  "timestamp": "..."
}
```

The generated files are stored under:

```text
quarantine/
```

Each failure uses a unique filename so that previous failures are not overwritten.

### Guardrails

* **Step limit** — Repair attempts remain capped.
* **Timeout** — Model calls use a configured timeout.
* **Retry** — Provider-level retries are capped.
* **Input limit** — Empty and oversized input is rejected before invocation.
* **Output limit** — Maximum model output tokens are limited.
* **Schema validation** — Every successful result must satisfy the `Review` schema.
* **Safe failure** — Invalid data is never returned after validation failure.
* **Quarantine** — Unrecoverable validation failures are persisted before raising the final error.
* **Secret hygiene** — API configuration is loaded only from environment variables.

### Run

```bash
uv run python -m quarantine.quarantine
```

### Run Tests

```bash
uv run pytest tests/test_quarantine.py -v
```

### Evidence

Execution and automated test outputs are saved in:

```text
outputs/quarantine_output.txt
outputs/quarantine_test_output.txt
```

Generated quarantine examples are stored in:

```text
quarantine/
```

### Tests

Task 4 includes two automated paths:

* **Success case** — A valid `Review` is returned and no quarantine file is created.
* **Failure case** — Validation fails across all allowed attempts, a JSON quarantine file is written, and a `RuntimeError` is raised.

The failure test also checks the contents of the generated quarantine record to confirm that meaningful failure information is preserved.

### Result

Task 4 adds persistent failure handling to the structured output pipeline. Responses that remain invalid after the bounded repair attempt are blocked from the caller and saved as quarantine evidence for debugging and traceability.
