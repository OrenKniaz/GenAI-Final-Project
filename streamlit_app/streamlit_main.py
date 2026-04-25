import streamlit as st

from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput

# Simple Streamlit entrypoint for the first UI slice.
st.title("Recruiting Chatbot Stub")

# Collect one candidate message and route it through the existing advisors.
message = st.text_input("Enter a candidate message")


if st.button("Run"):
    if not message.strip():
        st.warning("Please enter a message.")
    else:
        # use conversation_service to check the message and decide what to respond.
        turn = CandidateTurnInput(message=message)
        result = process_candidate_turn(turn)

        st.write("Action:", result.action)
        st.write("Assistant Message:", result.assistant_message)

        if result.show_slots and result.slots:
            # Show slots only when the router asks for scheduling.
            st.subheader("Available slots")
            for slot in result.slots:
                st.write(slot)