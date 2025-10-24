import streamlit as st
from interview_bot import create_interview_graph

st.title("AI Interview Simulator Chatbot")

# Interview questions (basic ones for demo, you can fetch/generate these dynamically)
STARTING_QUESTIONS = [
    "What is your name?",
    "What position have you applied for?",
    "What were the requirements for that?"
]

# Set up session state for tracking progress
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "result" not in st.session_state:
    st.session_state.result = None

# Logic for the interview process
if not st.session_state.interview_complete:
    # If there are questions left
    if st.session_state.current_q < len(STARTING_QUESTIONS):
        question = STARTING_QUESTIONS[st.session_state.current_q]
        st.write(f"**Question {st.session_state.current_q + 1}:** {question}")
        answer = st.text_input(
            "Your answer:", key=f"answer_{st.session_state.current_q}")

        if st.button("Submit", key=f"submit_{st.session_state.current_q}"):
            if answer.strip():
                st.session_state.answers.append(answer)
                st.session_state.current_q += 1
                st.experimental_rerun()
            else:
                st.warning("Please enter an answer before submitting.")
    else:
        # All answers collected, run the interview workflow
        st.write("Interview questions completed. Processing results...")

        # Build initial state for the interview bot
        initial_state = {
            "role": "",
            "questions": STARTING_QUESTIONS,
            "answers": st.session_state.answers,
            "requirements": st.session_state.answers[2] if len(st.session_state.answers) > 2 else "",
            "greeting_shown": True,
            "question_weights": {},
            "user_score": 0.0,
            "wrong_questions": [],
            "total_possible_score": 0.0
        }

        graph = create_interview_graph()
        result = graph.invoke(initial_state)
        st.session_state.result = result
        st.session_state.interview_complete = True
        st.experimental_rerun()
else:
    # Interview complete, show results
    result = st.session_state.result
    st.write("### Interview Complete!")
    st.write(
        f"**Score:** {result['user_score']} / {result['total_possible_score']}")
    if result.get("wrong_questions"):
        st.write("**Areas for improvement:**")
        for q in result["wrong_questions"]:
            st.write(f"- {q}")
    else:
        st.write("Great job! No improvement areas found.")
    st.write("Thank you for taking the interview!")
    if st.button("Restart Interview"):
        # Reset session state for restart
        for key in ["current_q", "answers", "interview_complete", "result"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()
