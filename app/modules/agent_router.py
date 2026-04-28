# This router defines all the 3 main agent actions: CONTINUE, SCHEDULE, and END.
# and decides which action to take based on advisors response.
# Defines a router decision class
from enum import Enum
from typing import Literal

# import advisors to help decide action.
from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.llm_helper import build_chat_llm
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel


# Define an enumeration for the possible actions the agent can take.
class Action(str, Enum):
    CONTINUE = "continue"
    SCHEDULE = "schedule"
    END = "end"


# class that creates a schema for the router decision.
class RouteSelection(BaseModel):
    action: Literal["continue", "schedule", "end"]

# Function to decide if need to return more info, for now basic decision not agentic decision yet.
def route_message(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
) -> Action:
    llm = build_chat_llm(temperature=0)
    structured_llm = llm.with_structured_output(RouteSelection)

    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    
    messages = [
        SystemMessage(
            content=(
                "You are a recruiting router for a hiring workflow.\n"
                "Classify the candidate's latest message into exactly one routing action.\n"
                "Use 'continue' for general conversation, role-information questions, or interest that does not request scheduling.\n"
                "Use 'schedule' when the candidate is trying to arrange an interview, asking about available times, asking about schedule or availability, or trying to book the next step.\n"
                "Use 'end' when the candidate clearly wants to stop or is no longer interested.\n"
                "If a message contains both scheduling language and a clear desire to stop, choose 'end'.\n"
                "If unsure, choose 'continue'."
            )
        ),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: What does this role focus on?"
            )
        ),
        AIMessage(content='{"action": "continue"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Do I need to know every framework already?"
            )
        ),
        AIMessage(content='{"action": "continue"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Not interested anymore, thanks"
            )
        ),
        AIMessage(content='{"action": "end"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: I'm interested"
            )
        ),
        AIMessage(content='{"action": "continue"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: I'm interested in interviewing for this role"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: I'm interested, but I still want to understand the role better"
            )
        ),
        AIMessage(content='{"action": "continue"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: I'm interested, goodbye"
            )
        ),
        AIMessage(content='{"action": "end"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Bye, can we schedule an interview?"
            )
        ),
        AIMessage(content='{"action": "end"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: I am not interested anymore, even if there are interview slots available"
            )
        ),
        AIMessage(content='{"action": "end"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Can we set up an interview for next week?"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: What's your schedule?"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: What times do you have available?"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Do you have interview slots this week?"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Can we find a time to talk?"
            )
        ),
        AIMessage(content='{"action": "schedule"}'),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: This sounds good, but I have one more question first"
            )
        ),
        AIMessage(content='{"action": "continue"}'),

        HumanMessage(
            content=(
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"Candidate question: {message}"
            )
        ),
    ]

    response = structured_llm.invoke(messages)

    # make sure response is in expected format, if it's a dict, and missing the key, default to "continue".
    if isinstance(response, dict):
        decision_text = response.get("action", "continue")
    else:
        decision_text = response.action

    if decision_text == "end":
        return Action.END
    if decision_text == "schedule":
        return Action.SCHEDULE
    return Action.CONTINUE




# Example usage of the decide_action function with some test messages.
if __name__ == "__main__":
    examples = [
        "Can we schedule an interview?",
        "Bye, I am not interested anymore.",
        "I have some questions about the role.",
    ]

    for example in examples:
        print(example, "->", route_message(example))