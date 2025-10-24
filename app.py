import streamlit as st
import threading
import queue
import time
import interview_bot
from interview_bot import create_interview_graph, InterviewState

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_input_queue' not in st.session_state:
    st.session_state.user_input_queue = queue.Queue()
if 'bot_output_queue' not in st.session_state:
    st.session_state.bot_output_queue = queue.Queue()
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'waiting_for_input' not in st.session_state:
    st.session_state.waiting_for_input = False
if 'interview_thread' not in st.session_state:
    st.session_state.interview_thread = None
if 'interview_completed' not in st.session_state:
    st.session_state.interview_completed = False

# Page config
st.set_page_config(page_title="AI Interview Bot", page_icon="🤖", layout="wide")

# Custom CSS for better chat UI
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    div[data-testid="stChatMessageContent"] {
        padding: 1rem;
    }
    /* Auto-scroll to bottom */
    .main .block-container {
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 AI Interview Bot")
st.markdown("---")


def run_interview():
    """Run the interview in a separate thread"""
    try:
        initial_state: InterviewState = {
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

        app = create_interview_graph()
        result = app.invoke(initial_state)

        # Send completion message via the module-level queue (set by main thread)
        try:
            if interview_bot.bot_output_queue is not None:
                interview_bot.bot_output_queue.put(
                    "🎉 Interview process completed!")
            else:
                # fallback to printing if queue not available
                print("🎉 Interview process completed!")
        except Exception:
            # ensure background thread doesn't touch Streamlit session_state directly
            print("🎉 Interview process completed! (couldn't put into queue)")
    except Exception as e:
        try:
            if interview_bot.bot_output_queue is not None:
                interview_bot.bot_output_queue.put(f"❌ Error: {str(e)}")
            else:
                print(f"❌ Error: {str(e)}")
        except Exception:
            print(f"❌ Error: {str(e)}")


# Start interview button
if not st.session_state.interview_started:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.interview_started = True
            st.session_state.interview_completed = False
            st.session_state.messages = []
            st.session_state.waiting_for_input = False

            # Ensure interview_bot module-level queues point to the Streamlit queues
            interview_bot.user_input_queue = st.session_state.user_input_queue
            interview_bot.bot_output_queue = st.session_state.bot_output_queue

            # Start interview in background thread
            interview_thread = threading.Thread(
                target=run_interview, daemon=True)
            interview_thread.start()
            st.session_state.interview_thread = interview_thread
            st.rerun()

# Chat interface
if st.session_state.interview_started:
    # Check for new bot messages continuously
    message_received = False
    try:
        while True:
            bot_message = st.session_state.bot_output_queue.get_nowait()
            st.session_state.messages.append(
                {"role": "assistant", "content": bot_message})
            message_received = True

            # If worker sent the completion message, mark interview completed
            if "interview process completed" in bot_message.lower() or "🎉 interview process completed" in bot_message:
                st.session_state.interview_completed = True
                st.session_state.waiting_for_input = False

            # Check if this message is asking for input
            # Look for "Your answer:" prompt specifically
            if "your answer:" in bot_message.lower() or bot_message.strip().endswith("?"):
                st.session_state.waiting_for_input = True
            elif "noted" in bot_message.lower() or "correct" in bot_message.lower() or "incorrect" in bot_message.lower():
                # After feedback, wait for next question
                st.session_state.waiting_for_input = False
    except queue.Empty:
        pass

    # Force rerun if we received messages to update UI
    if message_received:
        time.sleep(0.1)  # Small delay to batch messages
        st.rerun()

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # (Processing indicator removed — background updates are shown via messages)

    # User input
    if st.session_state.waiting_for_input and not st.session_state.interview_completed:
        user_input = st.chat_input("Type your answer here...")

        if user_input:
            # Add user message to chat
            st.session_state.messages.append(
                {"role": "user", "content": user_input})

            # Send to bot
            st.session_state.user_input_queue.put(user_input)
            st.session_state.waiting_for_input = False

            st.rerun()
    elif st.session_state.interview_completed:
        st.chat_input("Interview completed!", disabled=True)
    else:
        # Show placeholder when not waiting for input
        st.chat_input("Waiting for next question...", disabled=True)

    # Auto-refresh to check for new messages
    if not st.session_state.interview_completed:
        time.sleep(0.5)
        st.rerun()

    # Restart button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Restart Interview", use_container_width=True):
            st.session_state.interview_started = False
            st.session_state.interview_completed = False
            st.session_state.messages = []
            st.session_state.waiting_for_input = False
            st.session_state.user_input_queue = queue.Queue()
            st.session_state.bot_output_queue = queue.Queue()
            st.rerun()
else:
    # Welcome message
    st.info(
        "👋 Welcome! Click 'Start Interview' to begin your AI-powered interview session.")

    with st.expander("ℹ️ How it works"):
        st.markdown("""
        1. **Start the Interview**: Click the button above
        2. **Answer Questions**: The bot will ask you various questions
        3. **Get Feedback**: Receive personalized feedback based on your performance
        
        **Tips:**
        - Be honest and thoughtful in your answers
        - Take your time to think before responding
        - If you don't know an answer, it's okay to say so
        
        **Interview Structure:**
        - 3 initial questions (name, position, requirements)
        - 5 basic background questions
        - 23 position-specific technical questions
        - 2 personal questions
        """)

    st.markdown("---")
    st.markdown(
        "**Note:** Make sure you have your `.env` file configured with `GEMINI_API_KEY`")
