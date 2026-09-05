import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter
from pydantic import ValidationError

from schema_definition.schema_definition import Review


load_dotenv()

MAX_ATTEMPTS = 2
MAX_INPUT_LENGTH = 2000


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


def analyse_feedback(
    feedback: str,
    repair_chain=None,
    max_attempts: int = MAX_ATTEMPTS,
) -> Review:
    if not feedback.strip():
        raise ValueError("Feedback cannot be empty.")

    if len(feedback) > MAX_INPUT_LENGTH:
        raise ValueError("Feedback exceeds the allowed input budget.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    active_chain = repair_chain or chain
    repair_message = ""
    last_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}")

        try:
            result = active_chain.invoke(
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

        except ValidationError as exc:
            last_error = exc

            print("Validation failed.")
            print(exc)

            if attempt < max_attempts:
                repair_message = (
                    "The previous output failed schema validation.\n"
                    f"Validation error:\n{exc}\n\n"
                    "Correct the output and return all required fields."
                )

                print("Retrying once with validation error appended.")

    raise RuntimeError(
        f"Parse failed after {max_attempts} attempts: {last_error}"
    )


def main() -> None:
    result = analyse_feedback(
        "The movie was nice, acting was good, enjoyed it."
    )

    print()
    print("=== FINAL RESULT ===")
    print(result)
    print(f"Type: {type(result).__name__}")


if __name__ == "__main__":
    main()