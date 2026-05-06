# a tube that allows main app and streamlit app to call the same conversation logic without importing each other.

from dataclasses import dataclass

from app.modules.agent_router import TurnContext, run_turn

from app.modules.Helpers.role_helper import normalize_role


@dataclass
class CandidateTurnInput:
    message: str
    role: str | None = None
    history: list[str] | None = None
    first_name: str | None = None
    last_name: str | None = None
    reference_datetime_utc: str | None = None


@dataclass
class CandidateTurnResult:
    action: str
    assistant_message: str
    role: str | None
    normalized_role: str | None
    slots: list[str] | None = None
    show_slots: bool = False

def process_candidate_turn(turn: CandidateTurnInput) -> CandidateTurnResult:
    resolved_role = turn.role
    normalized_role = normalize_role(resolved_role)

    # build the advisor context with the candidate's message, role, conversation history, and name
    context = TurnContext(
        message=turn.message,
        role=resolved_role,
        history=turn.history or [],
        first_name=turn.first_name,
        last_name=turn.last_name,
        reference_datetime_utc=turn.reference_datetime_utc,
    )

    decision = run_turn(context) # run the agent router (basically initiate the turn)
    slots = decision.slots
    show_slots = bool(slots)

    return CandidateTurnResult(
        action=decision.action,
        assistant_message=decision.reply, # what is actually displayed for the candidate...
        role=resolved_role,
        normalized_role=normalized_role,
        slots=slots,
        show_slots=show_slots,
    )