import streamlit as st

from app.modules.Helpers.sql_helper import get_available_slots
from app.modules.agent_router import Action, decide_action

# Simple Streamlit entrypoint for the first UI slice.
st.title("Recruiting Chatbot Stub")

# Collect one candidate message and route it through the existing advisors.
message = st.text_input("Enter a candidate message")

if st.button("Run"):
    if not message.strip():
        st.warning("Please enter a message.")
    else:
        # Reuse the same router that main.py uses for the smoke test.
        action = decide_action(message)
        st.write("Action:", action.value)

        if action == Action.SCHEDULE:
            # Show slots only when the router asks for scheduling.
            slots = get_available_slots()
            st.subheader("Available slots")
            for slot in slots:
                st.write(slot)