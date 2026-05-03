# decides if it's right to schedule, if it is, also retrives available slots from SQL helper and passes to the main agent\router.
from dataclasses import dataclass
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import datetime as dt

from app.modules.Helpers.llm_helper import build_chat_llm
from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.sql_helper import (
    get_available_slots,
    get_exact_available_slot,
    get_schedule_reference_date,
)
from app.modules.Helpers.role_helper import normalize_role

# date extraction class from context
class ScheduleInterpretation(BaseModel):
    schedule_match: bool
    requested_time_text: str | None = None
    requested_slot_text: str | None = None
    rationale: str

# feedback schema for the schedule advisor
@dataclass(frozen=True)
class ScheduleAdvisorFeedback:
    schedule_match: bool
    requested_time_text: str | None
    requested_slot_text: str | None
    requested_slot_available: bool | None
    slots: list[str] | None
    reference_date_text: str | None
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
    structured_llm = llm.with_structured_output(ScheduleInterpretation)
    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    note_text = f"\nMain agent note: {main_agent_note}" if main_agent_note else ""

    normalized_role = normalize_role(role) # get role name that matches SQL DB

    # Get avaialble slots for this role, using SQL Helper.
    reference_date = (
        get_schedule_reference_date(normalized_role)
        if normalized_role
        else None
    )
    # Format reference date for prompt; if unavailable, indicate it's unknown.
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
                "Interpret time phrases relative to the provided SQL reference date and recent conversation context.\n"
                "Distinguish Tuesday from next Tuesday.\n"
                "Interpret tomorrow relative to the SQL reference date.\n"
                "If a concrete slot is inferred, return requested_slot_text in strict format YYYY-MM-DD HH:MM (24-hour).\n"
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
    #read ScheuldeInterpretation class from LLM result, handle both dict and object return types for flexibility
    if isinstance(result, dict): # in case return is a dict and not an object...
        schedule_match = result.get("schedule_match", False)
        requested_time_text = result.get("requested_time_text")
        requested_slot_text = result.get("requested_slot_text")
        rationale = result.get("rationale", "")
    else:
        schedule_match = result.schedule_match
        requested_time_text = result.requested_time_text
        requested_slot_text = result.requested_slot_text
        rationale = result.rationale

    requested_slot_available = None #initialize as none, only set to true or false if we have a requested slot to check against availability
    slots = None #initialize as none, only set if we have schedule_match and a normalized role to check against SQL for available slots

    if schedule_match and normalized_role: # LLM indicated a scheduleing event, and we have a normalized role - > go to SQL to get slots..
        if requested_slot_text: # if candidate asked for a specific slot\time, check if it's available
            # Accept strict "YYYY-MM-DD HH:MM"; tolerate legacy "YYYY-MM-DD at HH:MM".
            slot_text = requested_slot_text.replace(" at ", " ").strip()
            # Try to parse the exact requested slot, if it fails, just show nearby slots..
            try:
                requested_dt = dt.datetime.strptime(slot_text, "%Y-%m-%d %H:%M")
                requested_date = requested_dt.date()
                requested_time = requested_dt.time().replace(second=0, microsecond=0)

                # Canonicalize to strict format for downstream use.
                requested_slot_text = f"{requested_date.isoformat()} {requested_time.strftime('%H:%M')}"
                if not requested_time_text:
                    requested_time_text = requested_slot_text

                # check is there is exact match for requested slot, if so, set available to true, if not, use get_available_slots to find nearest slots
                exact_slot = get_exact_available_slot(normalized_role, requested_date, requested_time)
                if exact_slot is not None:
                    requested_slot_available = True
                    slots = [_format_slot(exact_slot)]
                else:
                    requested_slot_available = False
                    raw_slots = get_available_slots(
                        position=normalized_role,
                        target_date=requested_date,
                        target_time=requested_time,
                    )
                    slots = [_format_slot(slot) for slot in raw_slots]
            except ValueError:
                # If extraction format is invalid, gracefully fall back to default nearest slots.
                requested_slot_available = False
                raw_slots = get_available_slots(position=normalized_role)
                slots = [_format_slot(slot) for slot in raw_slots]
        # if no specific slot was requested, just get available slots for the role
        else:
            raw_slots = get_available_slots(position=normalized_role)
            slots = [_format_slot(slot) for slot in raw_slots]

    return ScheduleAdvisorFeedback(
        schedule_match=schedule_match,
        requested_time_text=requested_time_text,
        requested_slot_text=requested_slot_text,
        requested_slot_available=requested_slot_available,
        slots=slots,
        reference_date_text=reference_date_text,
        rationale=rationale,
    )

if __name__ == "__main__":
    fb = get_schedule_feedback("Can we schedule an interview?", role="Python Developer")
    print(fb)