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
if 'flag' not in st.session_state:
    # Simple flag to control showing the welcome/info block
    # (user requested a boolean named `flag` that hides the welcome
    # section once the interview starts)
    st.session_state.flag = True

# Page config
st.set_page_config(page_title="AI Interview Simulator", page_icon="🤖", layout="wide")

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
    /* Sticky header and content spacing */
    /* Keep room at top so the fixed header doesn't cover content */
    .main .block-container {
        padding-top: 6.5rem; /* space for the fixed title and top app bar */
        padding-bottom: 5rem;
    }

    /* Fixed title that remains visible at top of viewport */
    #sticky-title {
        position: fixed;
        /* place below Streamlit top bar (adjust if your top bar height differs) */
        top: 60px;
        left: 50%;
        transform: translateX(-50%);
        /* very high z-index to ensure visibility above Streamlit UI */
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.6rem 1rem;
        font-size: 1.6rem;
        font-weight: 700;
        max-width: 1700px;
        width: calc(100% - 4rem);
        border-radius: 6px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        color: #111; /* default text color for light themes */
        /* Use a semi-opaque background to play nice with themes */
        background: #0e1117;
        backdrop-filter: blur(4px);
        border-bottom: 1px solid rgba(0,0,0,0.06);
        /* Ensure it doesn't block clicks to the page when not needed */
        pointer-events: auto;
    }

    /* Slight adjustment for dark mode - fallbacks will apply if theme overrides */
    @media (prefers-color-scheme: dark) {
        #sticky-title {
            background: rgba(18, 18, 18, 0.92);
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: #fff;
        }
    }
</style>
""", unsafe_allow_html=True)

# Title (sticky)
st.markdown('<div id="sticky-title">🤖 AI Interview Simulator</div>', unsafe_allow_html=True)
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


# Start interview button (always rendered; disabled when interview already running)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    def _start_interview():
        """Callback to start the interview (used with st.button on_click).

        Using an explicit callback avoids missing the button click across
        reruns and ensures state is set atomically.
        """
        st.session_state.interview_started = True
        st.session_state.interview_completed = False
        st.session_state.messages = []
        st.session_state.waiting_for_input = False
        # hide the welcome/info block
        st.session_state.flag = False

        # Ensure interview_bot module-level queues point to the Streamlit queues
        interview_bot.user_input_queue = st.session_state.user_input_queue
        interview_bot.bot_output_queue = st.session_state.bot_output_queue

        # Start interview in background thread
        interview_thread = threading.Thread(target=run_interview, daemon=True)
        interview_thread.start()
        st.session_state.interview_thread = interview_thread

        # Trigger a rerun so the UI updates immediately
        try:
            st.experimental_rerun()
        except Exception:
            try:
                st.rerun()
            except Exception:
                pass

    # Show the Start button only when the interview has not started.
    # This makes the button disappear once the interview begins.
    if not st.session_state.get("interview_started", False):
        st.button(
            "🚀 Start Interview",
            type="primary",
            use_container_width=True,
            on_click=_start_interview,
        )

# Chat interface
if st.session_state.interview_started:
    # Check for new bot messages continuously
    message_received = False
    try:
        while True:
            bot_message = st.session_state.bot_output_queue.get_nowait()
            # Skip rendering any helper/welcome text that might have been emitted
            lower_msg = bot_message.lower()
            # If the bot greeting is emitted, hide the welcome/info block
            # immediately so the welcome panel cannot appear anymore.
            if "hello, i am" in lower_msg and "taking your interview" in lower_msg:
                st.session_state.flag = False
            skip_keywords = ["welcome", "start interview", "how it works"]
            if any(k in lower_msg for k in skip_keywords):
                # do not add welcome/how-it-works helper text to chat messages
                pass
            else:
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
            # show the welcome/info block again after restart
            st.session_state.flag = True
            st.rerun()
else:
    # Welcome message (only show when allowed)
    # Use the explicit `flag` to decide whether to render the welcome/info
    # block. Additionally only show it when there are no chat messages yet
    # to avoid the welcome box reappearing while the chat is active.
    # Additionally ensure the bot output queue is empty so the welcome
    # panel doesn't briefly reappear while the background interview
    # thread has already enqueued messages (prevents flicker).
    bot_queue_empty = True
    try:
        bot_queue_empty = st.session_state.bot_output_queue.empty()
    except Exception:
        # If the queue isn't available for any reason, treat as empty
        bot_queue_empty = True

    if st.session_state.flag and not st.session_state.messages and bot_queue_empty:
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
