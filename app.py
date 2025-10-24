import streamlit as st
from interview_bot import get_bot_response  # Import your bot logic

st.title("AI Interview Simulator Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("You:", key="user_input")
if st.button("Send"):
    if user_input:
        st.session_state.chat_history.append(("You", user_input))
        bot_reply = get_bot_response(user_input)
        st.session_state.chat_history.append(("Bot", bot_reply))
        st.session_state.user_input = ""  # Clear input box

for sender, msg in st.session_state.chat_history:
    st.markdown(f"**{sender}:** {msg}")