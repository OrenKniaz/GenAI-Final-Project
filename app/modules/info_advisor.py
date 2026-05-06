from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.modules.Helpers.llm_helper import build_chat_llm
from app.modules.Helpers.history_helper import format_conversation_history


class InfoAdvisorFeedback(BaseModel):
    info_needed: bool
    draft_reply: str
    rationale: str


def generate_info_feedback(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    main_agent_note: str | None = None,
) -> InfoAdvisorFeedback:

    llm = build_chat_llm(temperature=0) # Should deterministically extract data from the job description.
    structured_llm = llm.with_structured_output(InfoAdvisorFeedback)
    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    candidate_name = " ".join(part for part in [first_name, last_name] if part) or "the candidate"
    note_text = f"\nMain agent note: {main_agent_note}" if main_agent_note else ""

    messages = [
        SystemMessage(content=(
            "You are a recruiting information advisor for a hiring workflow.\n"
            "Decide whether the candidate's message requires a role information response before scheduling.\n"
            "Prefer info_needed false unless the candidate asks a genuine information question.\n"
            "Set info_needed to true when the candidate asks about the role, responsibilities, requirements, process, tools, remote/hybrid setup, compensation, or other concrete job details.\n"
            "When info_needed is true, provide a brief, clear draft_reply answering the question.\n"
            "When info_needed is false, set draft_reply to an empty string.\n"
            "Do not invent company-specific facts. If unsure, say you do not have confirmed details.\n"
            "Always provide a short rationale explaining your decision.\n"
            "When a candidate first name is provided, you may use it naturally but not in every sentence.\n"
            "Set info_needed to false when the message is a greeting, acknowledgment, qualification answer, experience summary, scheduling intent, or exit intent.\n"
            "When info_needed is false, set draft_reply to an empty string.\n"
            "Always provide a short rationale explaining your decision.\n"
        )),

        # info_needed = true
        HumanMessage(content="Candidate: Alex\nRole: Python Developer\nCandidate question: What does this role focus on?"),
        AIMessage(content='{"info_needed": true, "draft_reply": "This role focuses on building Python-based software and collaborating with the team on development tasks.", "rationale": "Candidate asked a direct role question."}'),

        HumanMessage(content="Candidate: Alex\nRole: Python Developer\nCandidate question: Do I need to know every framework already?"),
        AIMessage(content='{"info_needed": true, "draft_reply": "Not necessarily — strong Python fundamentals and relevant experience are the most important starting point.", "rationale": "Candidate asked about role requirements."}'),

        HumanMessage(content="Candidate: Alex\nRole: Python Developer\nCandidate question: I have three years of experience, is that enough for this role?"),
        AIMessage(content='{"info_needed": true, "draft_reply": "Three years of relevant Python experience can be a strong fit depending on the projects you have built.", "rationale": "Candidate asked a concrete qualification question."}'),

        # info_needed = false
        HumanMessage(content="Candidate: Jordan\nRole: Python Developer\nCandidate question: Ok, sounds good!"),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Candidate acknowledged information, no role question asked."}'),

        HumanMessage(content="Candidate: Jordan\nRole: Python Developer\nCandidate question: I have several years of Python experience building backend tools."),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Candidate provided a qualification answer, not an information question."}'),

        HumanMessage(content="Candidate: Jordan\nRole: Python Developer\nCandidate question: I mostly work with Python and SQL."),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Candidate summarized experience without asking a question."}'),

        HumanMessage(content="Candidate: Sam\nRole: Python Developer\nCandidate question: Can we set up an interview?"),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Candidate is asking to schedule, not asking about role information."}'),

        HumanMessage(content="Candidate: Sam\nRole: Python Developer\nCandidate question: Can we set up an interview?"),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Candidate is requesting to schedule, not asking for role information."}'),

        HumanMessage(content="Candidate: Jordan\nRole: Python Developer\nCandidate question: Ok, sounds good!"),
        AIMessage(content='{"info_needed": false, "draft_reply": "", "rationale": "Acknowledgment message, no role question asked."}'),

        HumanMessage(content=(
            f"Candidate: {candidate_name}\n"
            f"Role: {role_text}\n"
            f"{history_text}"
            f"{note_text}\n"
            f"Candidate question: {message}"
        )),
    ]

    response = structured_llm.invoke(messages)
    if isinstance(response, dict):
        return InfoAdvisorFeedback(
            info_needed=response.get("info_needed", True),
            draft_reply=response.get("draft_reply", ""),
            rationale=response.get("rationale", ""),
        )
    return response


if __name__ == "__main__":
    print(generate_info_feedback("Can you tell me more about the Python Developer role?", role="Python Developer"))
