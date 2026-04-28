from pydantic import BaseModel

from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.llm_helper import build_chat_llm
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage



# class that creates a schema for the router decision.
class ExitAdvisorDecision(BaseModel):
    exit_match: bool

def should_end(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
) -> ExitAdvisorDecision:

    llm = build_chat_llm(temperature=0)
    structured_llm = llm.with_structured_output(ExitAdvisorDecision)
    history_text = format_conversation_history(history or [])
    role_text = role or "the role"

    messages = [
        SystemMessage(
            content=(
                    "You are an exit advisor for a recruiting workflow.\n"
                    "Decide whether the candidate's latest message means the conversation should end.\n"
                    "Set exit_match to true only when the candidate clearly wants to stop, opt out, reject the process, or end the conversation.\n"
                    "Set exit_match to false when the candidate is still engaged, asking questions, expressing interest, delaying politely, or may want to continue later.\n"
                    "Use the recent conversation history when helpful.\n"
                    "If the message is ambiguous, prefer false."
            )
        ),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: What does this role focus on?"
            )
        ),
        AIMessage(content='{"exit_match": false}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: I still have questions about the role."
                )
            ),
            AIMessage(content='{"exit_match": false}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: Maybe later, can you tell me more first?"
                )
            ),
            AIMessage(content='{"exit_match": false}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: I'm interested but not ready yet."
                )
            ),
            AIMessage(content='{"exit_match": false}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: Not interested anymore, thanks."
                )
            ),
            AIMessage(content='{"exit_match": true}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: Please stop messaging me."
                )
            ),
            AIMessage(content='{"exit_match": true}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: Goodbye, remove me from the process."
                )
            ),
            AIMessage(content='{"exit_match": true}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: Thanks, bye for now."
                )
            ),
            AIMessage(content='{"exit_match": true}'),

            HumanMessage(
                content=(
                    "Role: Python Developer\n"
                    "Candidate question: I do not think this is for me."
                )
            ),
            AIMessage(content='{"exit_match": true}'),

        HumanMessage(
            content=(
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"Candidate question: {message}"
            )
        ),
    ]
    response = structured_llm.invoke(messages)
    
    # make sure response is in expected format, if it's a dict, and missing the key, default to false.
    if isinstance(response, dict):
        decision_text = response.get("exit_match", False)
    else:
        decision_text = response.exit_match

    return ExitAdvisorDecision(exit_match=decision_text)


if __name__ == "__main__":
    examples = [
        "Bye, I am done.",
        "I am not interested anymore.",
        "I still have questions about the role.",
    ]

    for example in examples:
        print(example, "->", should_end(example))