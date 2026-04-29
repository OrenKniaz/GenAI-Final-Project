# Dfine a dataclass that represents the results of a candidate's turn in the conversation
# Define a dataclass that represents the Candidate Turn input
# Define a function that proesses a candidate's message.

from dataclasses import dataclass, field
from typing import Optional

from app.modules.Helpers.sql_helper import get_available_slots
from app.modules.agent_router import Action, route_message

from app.modules.info_advisor import generate_info_response


@dataclass(frozen=True) 
class CandidateTurnInput:
    message: str  # The  last message from the candidate that we want to process. 
    history: list[str] = field(default_factory=list) # Conversation history up to this point.
    role: str | None = None # The role of the candidate to help agents provide the correct info\schedule the correct interview type.
    first_name: str | None = None # Candidate first name from the intake flow.
    last_name: str | None = None # Candidate last name from the intake flow.

@dataclass(frozen=True) # immutable to ensure consistency in the conversation\response.
class CandidateTurnResult:
    action: str # The action decided by the agent router (CONTINUE (and find more info), SCHEDULE, END)
    assistant_message: str # The message that the assistant would respond with based on the decided action.
    role: str | None = None # The role of the candidate to help agents provide the correct info\schedule the correct interview type.
    normalized_role: str | None = None # The normalized role extracted from the message to help with slot filling and info retrieval (match SQL).
    slots: list[str] | None = None # Optional list of available slots if the action is SCHEDULE.
    show_slots: bool = False # A flag to indicate whether the UI should show the available slots (if schedule)


def personalize_assistant_message(message: str, first_name: str | None) -> str:
    if not first_name:
        return message

    return f"{first_name}, {message}"



# Simple and temp role detection based on keywords in the message.
def detect_role(message: str) -> str | None:
    text = message.lower()

    if "python developer" in text or "python dev" in text:
        return "Python Developer"

    return None

# A simple normalization function to map different variations of role names to the SQL fields in db.
# For now , just Python Dev . later needs to be agentic...
def normalize_role(role: str | None) -> str | None:
    if role is None:
        return None

    role_map = {
        "Python Developer": "Python Dev",
    }

    return role_map.get(role)

# Based on the action decided by the agenr router, construct the class CandidateTurnResult written above
def process_candidate_turn(turn: CandidateTurnInput) -> CandidateTurnResult:
    resolved_role = detect_role(turn.message) or turn.role or detect_role_from_history(turn.history)# either get role from message (first priority) or use role from history
    action = route_message(turn.message, resolved_role, turn.history)
    normalized_role = normalize_role(resolved_role) # normalize role to match SQL fields if needed.
    if action == Action.END:
        return CandidateTurnResult(
            action=action.value,
            assistant_message=personalize_assistant_message(
                "Understood. We will end the conversation.",
                turn.first_name,
            ),
            role=resolved_role,
            normalized_role=normalized_role,
            show_slots=False,
        )

    if action == Action.SCHEDULE:
        slots = get_available_slots()
        slot_text = [str(slot) for slot in slots]
        return CandidateTurnResult(
            action=action.value,
            assistant_message=personalize_assistant_message(
                "Great, here are some available interview slots.",
                turn.first_name,
            ),
            role=resolved_role,
            normalized_role=normalized_role,
            slots=slot_text,
            show_slots=True,
        )
    # Actual LLM response function call to get the reposnse where "more info \ continue " is needed.
    info_response = generate_info_response(
        message=turn.message,
        role=resolved_role,
        history=turn.history,
        first_name=turn.first_name,
        last_name=turn.last_name,
    )

    return CandidateTurnResult(
        action=action.value,
        assistant_message=info_response,
        role=resolved_role,
        normalized_role=normalized_role,
        show_slots=False,
)

# make sure role detection from single message is part of the context for future turns.
def detect_role_from_history(history: list[str]) -> str | None:
    for entry in reversed(history):
        detected_role = detect_role(entry)
        if detected_role:
            return detected_role
    return None

