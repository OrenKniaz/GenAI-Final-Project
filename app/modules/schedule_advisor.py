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

# build the feedback from the schedule advisor
def get_schedule_feedback(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
    main_agent_note: str | None = None,
    reference_datetime_utc: str | None = None,
) -> ScheduleAdvisorFeedback:
    
    llm = build_chat_llm(temperature=0) # determanstic decision, can't make up slots...
    structured_llm = llm.with_structured_output(ScheduleInterpretation)
    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    note_text = f"\nMain agent note: {main_agent_note}" if main_agent_note else ""
    normalized_role = normalize_role(role) # get role name that matches SQL DB
    # use SQL time or json eval time and get slots
    reference_date = None
    if reference_datetime_utc:
        try:
            reference_date = dt.date.fromisoformat(reference_datetime_utc[:10])
        except ValueError:
            reference_date = None
    else:
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

    # start prompt..
    messages = [
        SystemMessage(
            content=(
                "You are a scheduling advisor for a recruiting workflow.\n"
                "You are called after the router has already selected the scheduling path.\n"
                "Your main job is to extract requested time details and provide SQL-backed interview slots.\n"
                "Prefer schedule_match true unless it is 90% clear the candidate is asking a genuine information question or wants to end.\n"
                "Set schedule_match to true for qualification answers, experience summaries, positive reactions, readiness, interest, availability problems, rejected slots, and direct scheduling requests.\n"
                "Set schedule_match to false only when the candidate asks a concrete role/process/requirements question that should be answered before scheduling, or clearly opts out.\n"
                "This demo uses a seeded SQL schedule calendar.\n"
                "Interpret time phrases relative to the provided schedule reference date and recent conversation context.\n"
                "Distinguish Tuesday from next Tuesday.\n"
                "Interpret tomorrow relative to the provided schedule reference date.\n"
                "If a concrete slot is inferred, return requested_slot_text in strict format YYYY-MM-DD HH:MM (24-hour).\n"
                f"Schedule reference date for this role: {reference_date_text}\n"
                "If the message is ambiguous, prefer true and offer slots.\n"
                "Always provide a short rationale explaining your decision.\n"
            )
        ),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: What does this role focus on?"),
        AIMessage(content='{"schedule_match": false, "rationale": "Candidate asked a role question, not requesting a time."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: I am interested, but what tools does the team use?"),
        AIMessage(content='{"schedule_match": false, "rationale": "Candidate asked a concrete information question before scheduling."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: Can we set up an interview?"),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate explicitly asked to set up an interview."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: What times are available?"),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate asked about available times — clear scheduling intent."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: I would like to book the next step."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate explicitly said they want to book the next step."}'),

        # Qualification answers should move to scheduling unless they ask a real question.
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter asked what Python projects the candidate has worked on.\nCandidate prompt: I have several years of Python experience building dashboards and automation."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate answered the recruiter screening question and stayed engaged, so offer interview slots."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: I mostly work with backend services and SQL."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate provided relevant qualifications without asking for more information."}'),

        HumanMessage(content="Role: Python Developer\nCandidate prompt: Sounds interesting, I can handle it."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate reacted positively and did not ask a blocking question."}'),

        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered a few interview times.\nCandidate prompt: None of those times work for me."),
        AIMessage(content='{"schedule_match": true, "rationale": "Candidate rejected the proposed slots but did not opt out, so offer new slots."}'),

        # Loopback
        HumanMessage(content=(
            "Role: Python Developer\n"
            "Conversation history: Candidate previously said they are interested and have no more questions.\n"
            "Main agent note: Candidate said they are ready but intent is unclear — please check history for scheduling signal.\n"
            "Candidate prompt: I think I'm ready."
        )),
        AIMessage(content='{"schedule_match": true, "rationale": "Conversation history shows no remaining questions and readiness — scheduling intent is likely."}'),
        HumanMessage(
            content=(
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"{note_text}\n"
                f"Candidate prompt: {message}"
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
                raw_slots = get_available_slots(position=normalized_role, from_date=reference_date)
                slots = [_format_slot(slot) for slot in raw_slots]
        # if no specific slot was requested, just get available slots for the role
        else:
            raw_slots = get_available_slots(position=normalized_role, from_date=reference_date)
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
