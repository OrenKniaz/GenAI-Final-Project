# Dfine a dataclass that represents the results of a candidate's turn in the conversation
# Define a function that proesses a candidate's message.

from dataclasses import dataclass
from typing import Optional

from app.modules.Helpers.sql_helper import get_available_slots
from app.modules.agent_router import Action, decide_action

@dataclass(frozen=True) # immutable to ensure consistency in the conversation\response.
class CandidateTurnResult:
    action: str # The action decided by the agent router (CONTINUE (and find more info), SCHEDULE, END)
    assistant_message: str # The message that the assistant would respond with based on the decided action.
    slots: list[str] | None = None # Optional list of available slots if the action is SCHEDULE.
    show_slots: bool = False # A flag to indicate whether the UI should show the available slots (if schedule)

# Based on the action decided by the agenr router, construct the class CandidateTurnResult written above
def process_candidate_turn(message: str) -> CandidateTurnResult:
    action = decide_action(message)

    if action == Action.END:
        return CandidateTurnResult(
            action=action.value,
            assistant_message="Understood. We will end the conversation.",
            show_slots=False,
        )

    if action == Action.SCHEDULE:
        slots = get_available_slots()
        slot_text = [str(slot) for slot in slots]
        return CandidateTurnResult(
            action=action.value,
            assistant_message="Great, here are some available interview slots.",
            slots=slot_text,
            show_slots=True,
        )

    return CandidateTurnResult(
        action=action.value,
        assistant_message="Thanks. Let me keep the conversation going and gather more details.",
        show_slots=False,
    )