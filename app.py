import streamlit as st
import interview_bot

# --- Streamlit-based IO overrides ---


def input_user(prompt: str) -> str:
    # Display prompt & get answer using Streamlit form
    st.session_state.prompt = prompt
    input_key = f"input_{st.session_state.step}"
    st.text_area(prompt, key=input_key)
    submitted = st.button("Submit", key=f"submit_{st.session_state.step}")
    if submitted and st.session_state[input_key]:
        return st.session_state[input_key]
    else:
        st.stop()  # Wait until user submits


def output_user(message: str):
    # Display message using Streamlit
    st.write(message)


# Override interview_bot IO globally
interview_bot.input_user = input_user
interview_bot.output_user = output_user

st.title("AI Interview Simulator Chatbot")

# Session state initialization
if "step" not in st.session_state:
    st.session_state.step = 0
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "initial_state" not in st.session_state:
    # Setup initial interview state
    st.session_state.initial_state = {
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

if not st.session_state.interview_complete:
    if st.session_state.step == 0:
        st.write("Welcome! Click below to start your interview.")
        if st.button("Start Interview"):
            # Create and run the LangGraph workflow
            graph = interview_bot.create_interview_graph()
            result = graph.invoke(st.session_state.initial_state)
            st.session_state.result = result
            st.session_state.interview_complete = True
            st.experimental_rerun()
else:
    # Interview is complete, display feedback
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
