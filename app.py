import interview_bot
import streamlit as st
from interview_bot import InterviewState, node_1_generate_questions, node_2_evaluate_answers, node_3_provide_feedback

# Initialize Streamlit session state
if "interview_state" not in st.session_state:
    st.session_state.interview_state = {
        "role": "",
        "questions": [],
        "answers": [],
        "requirements": "",
        "greeting_shown": False,
        "question_weights": {},
        "user_score": 0.0,
        "wrong_questions": [],
        "total_possible_score": 0.0
    }
if "step" not in st.session_state:
    st.session_state.step = 0  # 0: greet/generate, 1: ask questions, 2: feedback
if "history" not in st.session_state:
    st.session_state.history = []  # list of (speaker, message)
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0


def input_user_streamlit(prompt: str) -> str:
    st.session_state.history.append(("bot", prompt))
    st.markdown(f"**{prompt}**")
    user_input = st.text_input(
        "Your answer:", key=f"user_input_{st.session_state.current_question_index}")
    if st.button("Submit", key=f"submit_{st.session_state.current_question_index}"):
        st.session_state.history.append(("user", user_input))
        st.session_state.current_question_index += 1
        return user_input
    st.stop()  # Wait for user input


def print_bot_streamlit(message: str) -> None:
    st.session_state.history.append(("bot", message))
    st.markdown(message)


# Patch interview_bot.py functions
interview_bot.input_user = input_user_streamlit
interview_bot.print_bot = print_bot_streamlit


def main():
    st.title("Interview Bot")
    st.markdown("Welcome to the interactive interview bot. Please answer each question. Scroll below to see your full conversation history.")

    # Display history for scrollable chat
    for speaker, msg in st.session_state.history:
        if speaker == "bot":
            st.markdown(
                f"<div style='background-color:#f0f2f6;padding:8px;border-radius:6px'><b>Bot:</b> {msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='background-color:#e7ffdb;padding:8px;border-radius:6px'><b>You:</b> {msg}</div>", unsafe_allow_html=True)

    interview_state = st.session_state.interview_state

    if st.session_state.step == 0:
        # Node 1: generate questions and collect requirements
        interview_state = node_1_generate_questions(interview_state)
        st.session_state.step = 1
        st.experimental_rerun()

    elif st.session_state.step == 1:
        # Node 2: ask each question one by one
        total_questions = interview_state["questions"][3:]  # Skip initial 3
        if st.session_state.current_question_index < len(total_questions):
            # Ask next question
            question = total_questions[st.session_state.current_question_index]
            user_answer = input_user_streamlit(question)
            interview_state["answers"].append(user_answer)
            # Add score/weight logic if needed (but main evaluation will be after all are answered)
            st.experimental_rerun()
        else:
            # All questions answered, run evaluation
            interview_state = node_2_evaluate_answers(interview_state)
            st.session_state.step = 2
            st.experimental_rerun()

    elif st.session_state.step == 2:
        # Node 3: feedback
        interview_state = node_3_provide_feedback(interview_state)
        st.markdown("🏁 Interview process completed!")
        st.session_state.step = 3

    # Scrollable UI
    st.markdown("""
        <style>
        .stMarkdown {overflow-y: auto; max-height: 60vh;}
        </style>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
