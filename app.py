import streamlit as st
from interview_bot import create_interview_graph, InterviewState

st.title("AI Interview Simulator Chatbot")

if "state" not in st.session_state:
    # Initialize interview state
    st.session_state.state = {
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
    st.session_state.interview_started = False
    st.session_state.current_question_index = 0
    st.session_state.questions_to_ask = []
    st.session_state.graph = create_interview_graph()


def next_question():
    idx = st.session_state.current_question_index
    if idx < len(st.session_state.questions_to_ask):
        return st.session_state.questions_to_ask[idx]
    return None


def run_interview():
    # Step 1: Generate questions
    state = st.session_state.state
    state = st.session_state.graph.invoke(state)
    st.session_state.questions_to_ask = state["questions"]
    st.session_state.state = state
    st.session_state.interview_started = True


if not st.session_state.interview_started:
    st.write("Welcome! Click below to start your interview.")
    if st.button("Start Interview"):
        run_interview()
        st.experimental_rerun()
else:
    question = next_question()
    if question:
        st.write(
            f"**Question {st.session_state.current_question_index + 1}:** {question}")
        user_answer = st.text_input(
            "Your answer:", key=f"answer_{st.session_state.current_question_index}")
        if st.button("Submit Answer", key=f"submit_{st.session_state.current_question_index}"):
            st.session_state.state["answers"].append(user_answer)
            st.session_state.current_question_index += 1
            st.experimental_rerun()
    else:
        st.write("Interview completed! Generating feedback...")
        # Run feedback node
        state = st.session_state.state
        feedback_state = st.session_state.graph.invoke(state)
        st.write("**Feedback:**")
        st.write(
            f"Score: {feedback_state['user_score']}/{feedback_state['total_possible_score']}")
        if feedback_state.get("wrong_questions"):
            st.write("Areas for improvement:")
            for q in feedback_state["wrong_questions"]:
                st.write(f"- {q}")
