# decides if it's right to schedule, if it is, also retrives available slots from SQL helper and passes to the main agent\router.
from dataclasses import dataclass

from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.modules.Helpers.llm_helper import build_chat_llm
from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.sql_helper import get_available_slots, get_schedule_reference_date
from app.modules.Helpers.role_helper import normalize_role

# feedback schema for the schedule advisor
@dataclass(frozen=True)
class ScheduleAdvisorFeedback:
    schedule_match: bool
    slots: list[str] | None
    rationale: str

# class (schema) that answers to schedule or not.
class ScheduleMatch(BaseModel):
    schedule_match: bool
    rationale: str

# schema for displaying the available slots
def _format_slot(slot) -> str:
    slot_date = slot[1]
    slot_time = slot[2]
    weekday = slot_date.strftime("%A")
    time_text = slot_time.strftime("%H:%M")
    return f"{weekday}, {slot_date.isoformat()} at {time_text}"

# get the slots
def get_schedule_feedback(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
    main_agent_note: str | None = None,
) -> ScheduleAdvisorFeedback:
    
    llm = build_chat_llm(temperature=0) # determanstic decision, can't make up slots...
    structured_llm = llm.with_structured_output(ScheduleMatch)
    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    note_text = f"\nMain agent note: {main_agent_note}" if main_agent_note else ""

    normalized_role = normalize_role(role)
    reference_date = (
        get_schedule_reference_date(normalized_role)
        if normalized_role
        else None
    )
    reference_date_text = (
        reference_date.isoformat()
        if reference_date is not None
        else "unknown"
    )

    messages = [
        SystemMessage(
            content=(
                "You are a scheduling advisor for a recruiting workflow.\n"
                "Decide whether the candidate's latest message indicates they want to schedule an interview.\n"
                "Set schedule_match to true when the candidate asks about times, availability, booking, or next steps that imply scheduling.\n"
                "Set schedule_match to false when the candidate is asking role questions, expressing general interest, or wants more info first.\n"
                "This demo uses a seeded SQL schedule calendar.\n"
                "Interpret scheduling relative to the provided schedule reference date, not the real current date.\n"
                f"Schedule reference date for this role: {reference_date_text}\n"
                "If the message is ambiguous, prefer false.\n"
                "Always provide a short rationale explaining your decision.\n"
            )
        ),
        HumanMessage(content="Role: Python Developer\nCandidate question: What does this role focus on?"),
        AIMessage(content='{"schedule_match": false, "rationale": "Candidate asked a role question, not requesting a time."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: I am interested but need more info first."),
        AIMessage(content='{"schedule_match": false, "rationale": "Candidate wants more info before scheduling."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Can we set up an interview?"),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate explicitly asked to set up an interview."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: What times are available?"),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate asked about available times — clear scheduling intent."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: I would like to book the next step."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate explicitly said they want to book the next step."}'),
        # Ambiguous
        HumanMessage(content="Role: Python Developer\nCandidate question: I think I'm ready."),
        AIMessage(content='{"schedule_match": false, "rationale": "Ambiguous — readiness expressed but no explicit scheduling request. Defaulting to false."}'),

        # Loopback
        HumanMessage(content=(
            "Role: Python Developer\n"
            "Conversation history: Candidate previously said they are interested and have no more questions.\n"
            "Main agent note: Candidate said they are ready but intent is unclear — please check history for scheduling signal.\n"
            "Candidate question: I think I'm ready."
        )),
        AIMessage(content='{"schedule_match": true, "rationale": "Conversation history shows no remaining questions and readiness — scheduling intent is likely."}'),
        HumanMessage(
            content=(
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"{note_text}\n"
                f"Candidate question: {message}"
            )
        ),
    ]

    result = structured_llm.invoke(messages)
    if isinstance(result, dict):
        schedule_match = result.get("schedule_match", False)
        rationale = result.get("rationale", "")
    else:
        schedule_match = result.schedule_match
        rationale = result.rationale

    normalized_role = normalize_role(role)
    slots = None # default to None, only populate if schedule_match is true
    if schedule_match and normalized_role:
        raw_slots = get_available_slots(position=normalized_role)
        slots = [_format_slot(slot) for slot in raw_slots]

    return ScheduleAdvisorFeedback(
        schedule_match=schedule_match,
        slots=slots,
        rationale=rationale,
        )

if __name__ == "__main__":
    fb = get_schedule_feedback("Can we schedule an interview?", role="Python Developer")
    print(fb)