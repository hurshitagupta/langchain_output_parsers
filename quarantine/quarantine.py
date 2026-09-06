import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from pydantic import ValidationError

from schema_definition.schema_definition import Review


load_dotenv()

MAX_ATTEMPTS = 2
MAX_INPUT_LENGTH = 2000
QUARANTINE_DIR = Path("quarantine")


model = ChatOpenRouter(
    api_key=os.environ["OPENROUTER_API_KEY"],
    model=os.environ["MODEL_NAME"],
    base_url=os.environ["BASE_URL"],
    timeout=20_000,
    max_retries=3,
    max_tokens=100,
)

model_with_schema = model.with_structured_output(Review)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a feedback reviewer.

        Always return all required fields:
        sentiment, score, reasons.

        sentiment must be one of:
        positive, negative, neutral, mixed

        score must be between 0 and 1.

        reasons must contain between 1 and 3 short strings.
        """,
    ),
    (
        "human",
        """
        Analyse this feedback:

        {feedback}

        {repair_message}
        """,
    ),
])

chain = prompt | model_with_schema


def write_quarantine(
    feedback: str,
    error: Exception,
    attempts: int,
) -> Path:
    QUARANTINE_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    file_path = QUARANTINE_DIR / f"failure_{timestamp}.json"

    record = {
        "feedback": feedback,
        "error": str(error),
        "attempts": attempts,
        "timestamp": datetime.now().isoformat(),
    }

    file_path.write_text(
        json.dumps(record, indent=2),
        encoding="utf-8",
    )

    return file_path


def analyse_feedback(
    feedback: str,
    active_chain=None,
    max_attempts: int = MAX_ATTEMPTS,
) -> Review:
    if not feedback.strip():
        raise ValueError("Feedback cannot be empty.")

    if len(feedback) > MAX_INPUT_LENGTH:
        raise ValueError("Feedback exceeds the allowed input budget.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    current_chain = active_chain or chain
    repair_message = ""
    last_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}")

        try:
            result = current_chain.invoke(
                {
                    "feedback": feedback,
                    "repair_message": repair_message,
                }
            )

            if not isinstance(result, Review):
                raise TypeError(
                    "Model output was not validated as Review."
                )

            print("Validation successful.")
            return result

        except (ValidationError, TypeError) as exc:
            last_error = exc

            print("Validation failed.")
            print(exc)

            if attempt < max_attempts:
                repair_message = (
                    "The previous output failed validation.\n"
                    f"Validation error:\n{exc}\n\n"
                    "Correct the output and return all required fields."
                )

                print("Retrying once with validation error appended.")

    quarantine_file = write_quarantine(
        feedback=feedback,
        error=last_error,
        attempts=max_attempts,
    )

    print(f"Parse failed after {max_attempts} attempts.")
    print(f"Failure quarantined: {quarantine_file}")

    raise RuntimeError(
        f"Parse failed after {max_attempts} attempts; "
        f"quarantined at {quarantine_file}"
    )

class DemoFailChain:
    def invoke(self, inputs):
        return Review(
            sentiment="positive",
            score=5,
            reasons=["Good acting"],
        )

def main() -> None:
    try:
        analyse_feedback(
            "The movie was good.",
            active_chain=DemoFailChain(),
        )
    except RuntimeError as exc:
        print()
        print("=== QUARANTINE RESULT ===")
        print(exc)

# def main() -> None:
#     result = analyse_feedback(
#         "The movie was enjoyable and the acting was excellent."
#     )

#     print()
#     print("=== FINAL RESULT ===")
#     print(result)


if __name__ == "__main__":
    main()