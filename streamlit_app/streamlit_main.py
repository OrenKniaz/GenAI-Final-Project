import streamlit as st

from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput

# Simple Streamlit entrypoint for the first UI slice.
st.title("Recruiting Chatbot Stub")

# Collect one candidate message and route it through the existing advisors.
message = st.text_input("Enter a candidate message")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_role" not in st.session_state:
    st.session_state.current_role = None
    
# display chat history for the user supporting roles destinction
for turn_entry in st.session_state.chat_history:
    chat_role = "user" if turn_entry["speaker"] == "candidate" else "assistant"
    with st.chat_message(chat_role):
        st.write(f"{turn_entry['speaker'].title()}: {turn_entry['text']}")
        if turn_entry.get("slots"):
            for slot in turn_entry["slots"]:
                st.write(slot)

if st.button("Run"):
    if not message.strip():
        st.warning("Please enter a message.")
    else:
        # Extract the history of the messages for context.
        history = [entry["text"] for entry in st.session_state.chat_history]

        # Create a CandidateTurnInput object with the message, history, and current role from session state.
        turn = CandidateTurnInput(
            message=message,
            history=history,
            role=st.session_state.current_role,
        )

        # use conversation_service to check the message and decide what to respond.
        result = process_candidate_turn(turn)

        # Append to chat history for context in future turns.
        new_entries = [
            {"speaker": "candidate", "text": message, "slots": None},
            {
                "speaker": "assistant",
                "text": result.assistant_message,
                "slots": result.slots if result.show_slots else None,
            },
        ]

        st.session_state.chat_history.extend(new_entries)
        st.session_state.current_role = result.role
        st.rerun()
        