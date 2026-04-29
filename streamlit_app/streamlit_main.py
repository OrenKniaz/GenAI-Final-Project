import streamlit as st

from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput

# set page title rules (banner) using css
st.markdown(
    """
    <style>
    .sticky-banner {
        position: fixed;
        top: 2.75rem;
        left: 0;
        right: 0;
        z-index: 999;
        background: rgba(255, 255, 255, 0.98);
        border-bottom: 1px solid #e6e6e6;
        padding: 0.85rem 1rem;
        font-size: 1.35rem;
        font-weight: 700;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
    }
    .page-offset {
        height: 7rem;
    }
    </style>
    <div class="sticky-banner">Recruiting Chatbot Stub</div>
    <div class="page-offset"></div>
    """,
    unsafe_allow_html=True,
)



if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_role" not in st.session_state:
    st.session_state.current_role = None

if "first_name" not in st.session_state:
    st.session_state.first_name = "Test"

if "last_name" not in st.session_state:
    st.session_state.last_name = "Candidate"

if "intake_complete" not in st.session_state:
    st.session_state.intake_complete = False

if not st.session_state.intake_complete:
    st.subheader("Application form")
    with st.form("intake_form"):
        first_name = st.text_input("First name", value=st.session_state.first_name)
        last_name = st.text_input("Last name", value=st.session_state.last_name)
        selected_role = st.selectbox(
            "Select the role you are applying for",
            ["Python Developer"],
        )
        submitted = st.form_submit_button("Start chat")

    if submitted:
        if not first_name.strip() or not last_name.strip():
            st.warning("Please enter first and last name.")
        else:
            st.session_state.first_name = first_name.strip()
            st.session_state.last_name = last_name.strip()
            st.session_state.current_role = selected_role
            st.session_state.intake_complete = True
            st.rerun()
else:
    

    for turn_entry in st.session_state.chat_history:
        chat_role = "user" if turn_entry["speaker"] == "candidate" else "assistant"
        with st.chat_message(chat_role):
            st.write(turn_entry["text"])
            if turn_entry.get("slots"):
                for slot in turn_entry["slots"]:
                    st.write(slot)

    # option to change role during chat (for example pythong and ml engineer not sure if he wants to apply for the one or the other..)
    st.sidebar.title("Recruiting Chatbot")
    available_roles = ["Python Developer"]
    current_index = available_roles.index(st.session_state.current_role) if st.session_state.current_role in available_roles else 0
    selected_role_in_chat = st.sidebar.selectbox("Applying for", available_roles, index=current_index, key="role_change_select")
    if selected_role_in_chat != st.session_state.current_role:
        st.session_state.current_role = selected_role_in_chat
        st.rerun()

    message = st.chat_input("Enter a candidate message")
    

    if message:
        history = [entry["text"] for entry in st.session_state.chat_history]

        turn = CandidateTurnInput(
            message=message,
            history=history,
            role=st.session_state.current_role,
            first_name=st.session_state.first_name,
            last_name=st.session_state.last_name,
        )

        with st.chat_message("user"):
            st.write(message)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = process_candidate_turn(turn)

            st.write(result.assistant_message)

            if result.show_slots and result.slots:
                for slot in result.slots:
                    st.write(slot)

        new_entries = [
            {"speaker": "candidate", "text": message, "slots": None},
            {
                "speaker": "assistant",
                "text": result.assistant_message,
                "slots": result.slots if result.show_slots else None,
            },
        ]

        st.session_state.chat_history.extend(new_entries)
        st.rerun()