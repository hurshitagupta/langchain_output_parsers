import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter

from schema_definition.schema_definition import Review


load_dotenv()

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
        Never omit any field.
        """,
    ),
    (
        "human",
        "Analyse this feedback: {feedback}",
    ),
])

chain = prompt | model_with_schema


def analyse_feedback(feedback: str) -> Review:
    if not feedback.strip():
        raise ValueError("Feedback cannot be empty.")

    if len(feedback) > MAX_INPUT_LENGTH:
        raise ValueError("Feedback exceeds the allowed input budget.")

    result = chain.invoke({"feedback": feedback})

    if not isinstance(result, Review):
        raise TypeError("Model output was not validated as Review.")

    return result


def main() -> None:
    ans = analyse_feedback(
        "The movie was nice, acting was good, enjoyed it."
    )

    print("=== STRUCTURED OUTPUT ===")
    print(ans)
    print(f"Type: {type(ans).__name__}")


if __name__ == "__main__":
    main()


