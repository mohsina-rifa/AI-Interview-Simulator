from langchain_groq import ChatGroq
import time
from typing import Dict, List, TypedDict
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

load_dotenv()

class InterviewState(TypedDict):
    role: str
    questions: List[str]
    answers: List[str]
    requirements: str
    greeting_shown: bool
    question_weights: Dict[str, dict]
    user_score: float  # Added to TypedDict
    wrong_questions: List[str]  # Added to TypedDict
    total_possible_score: float  # Added to TypedDict

def safe_llm_invoke(llm, prompt, max_retries=3):
    """Safely invoke LLM with retry logic"""
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                raise e
    return None

def node_1_generate_questions(state: InterviewState) -> InterviewState:
    """Generates interview questions and weights only"""
    
    # Generate greeting-message
    if not state.get("greeting_shown", False):
        print("Hello, I am Anishom and I will be taking your interview today.")
        state["greeting_shown"] = True

    # Ask starting-questions: name, applied-position, requirements
    starting_questions = [
        "What is your name?",
        "What position have you applied for?", 
        "What were the requirements for that?"
    ]

    # Get answer from user
    answers = []
    for question in starting_questions:
        print(f"\n{question}")
        answer = input("Your answer: ")
        answers.append(answer)

    state["questions"] = starting_questions
    state["answers"] = answers
    state["requirements"] = answers[2]
    state["question_weights"] = {}
    state["user_score"] = 0.0
    state["wrong_questions"] = []
    state["total_possible_score"] = 0.0

    llm = ChatGroq(model="llama-3.1-8b-instant",
                   api_key=os.getenv("GROQ_API_KEY"))

    # Generate basic questions = 5
    basic_questions = [
        "Where are you currently living?",
        "Tell us about your previous work experience.",
        "Which university did you graduate from?", 
        "What was your major?",
        "What are your future career plans?"
    ]

    # Assign weight to answer - basic questions have weight 0
    for q in basic_questions:
        state["question_weights"][q] = {"type": "basic", "weight": 0}

    # Generate position-related questions = 23
    questions_prompt = f"""You are generating interview questions. Follow this EXACT format:

    QUESTION: What is {state['requirements']} used for?
    WEIGHT: 7

    QUESTION: How do you implement features in {state['requirements']}?
    WEIGHT: 8

    QUESTION: What are best practices in {state['requirements']}?
    WEIGHT: 6

    Generate exactly 23 questions following this format. Each question should test {state['requirements']} knowledge. Use weights 1-10 based on difficulty."""

    print("Generating questions...")
    response = safe_llm_invoke(llm, questions_prompt)

    if response is None:
        print("Failed to generate questions.")
        return state

    # Parse generated questions and weights
    questions_text = response.content.strip()
    print(f"Debug - LLM Response:\n{questions_text[:300]}...")  # Debug output
    lines = questions_text.split("\n")

    position_questions = []
    total_weight = 0

    i = 0
    while i < len(lines) and len(position_questions) < 23:
        line = lines[i].strip()
        
        # Handle both formats: "QUESTION:" and "1. QUESTION:" or numbered variations
        if "QUESTION:" in line:
            # Extract question text after "QUESTION:"
            question_part = line.split("QUESTION:")[1].strip()
            weight = 5  # Default weight
            
            # Look for weight in the same line or next line
            if "WEIGHT:" in line:
                # Weight is on same line
                parts = line.split("WEIGHT:")
                if len(parts) > 1:
                    try:
                        weight = float(parts[1].strip())
                        weight = max(1, min(10, weight))
                    except:
                        weight = 5
            elif i + 1 < len(lines) and "WEIGHT:" in lines[i + 1]:
                # Weight is on next line
                try:
                    weight_line = lines[i + 1].strip()
                    weight_part = weight_line.split("WEIGHT:")[1].strip()
                    weight = float(weight_part)
                    weight = max(1, min(10, weight))
                except:
                    weight = 5
            
            if question_part:  # Only add non-empty questions
                position_questions.append(question_part)
                state["question_weights"][question_part] = {
                    "type": "position-related", "weight": weight}
                total_weight += weight
                print(f"Added Q{len(position_questions)}: {question_part[:50]}... (Weight: {weight})")
        
        i += 1

    # If we didn't get enough questions from LLM, show warning
    if len(position_questions) < 5:
        print(f"Warning: Only generated {len(position_questions)} questions. Continuing with what we have...")

    state["total_possible_score"] = total_weight

    # personal = 2
    personal_questions = [
        "What activities do you pursue outside of work?",
        "Why do you think you are a good candidate for this position?"
    ]

    # Assign weight to answer - personal questions have weight 0
    for q in personal_questions:
        state["question_weights"][q] = {"type": "personal", "weight": 0}

    all_questions = basic_questions + position_questions + personal_questions
    state["questions"].extend(all_questions)

    print(f"✓ Basic: {len(basic_questions)}, Position-related: {len(position_questions)}, Personal: {len(personal_questions)}")

    return state

def node_2_evaluate_answers(state: InterviewState) -> InterviewState:
    """Evaluates answers using LLM evaluation"""
    
    # receive question-set
    questions = state["questions"][3:]  # Skip the first 3 starter questions
    user_score = 0
    wrong_questions = []

    llm = ChatGroq(model="llama-3.1-8b-instant",
                   api_key=os.getenv("GROQ_API_KEY"))

    # map scores of all questions with 0 initially
    for question in questions:
        if "score" not in state["question_weights"].get(question, {}):
            state["question_weights"][question]["score"] = 0

    print("Starting interview evaluation...\n")

    # ask one by one and evaluate only the position-related questions
    for question in questions:
        print(f"\n{question}")
        user_answer = input("Your answer: ")

        q_type = state["question_weights"].get(
            question, {}).get("type", "unknown")
        weight = state["question_weights"].get(question, {}).get("weight", 0)

        # pass = score -= 2, save the question
        if "don't" in user_answer.lower() and "know" in user_answer.lower():
            print("✗ Moving to next question.")
            user_score -= 2
            state["question_weights"][question]["score"] = -2
            wrong_questions.append(question)
            state["answers"].append(user_answer)
            continue

        # For basic and personal questions, just record
        if q_type in ["basic", "personal"]:
            print("✓ Noted.")
            state["question_weights"][question]["score"] = 0
            state["answers"].append(user_answer)
            continue

        # evaluate only the position-related questions using LLM
        eval_prompt = f"""Evaluate this {state['requirements']} interview answer:

        Question: {question}
        User Answer: {user_answer}

        Is this answer technically correct for {state['requirements']}?
        Reply with only "CORRECT" or "INCORRECT"."""

        eval_response = safe_llm_invoke(llm, eval_prompt)
        if eval_response is None:
            print("✗ Evaluation failed. Skipping.")
            wrong_questions.append(question)
            continue

        is_correct = "CORRECT" in eval_response.content.upper()

        if is_correct:
            # correct = score += weight
            print("✓ Correct! Well done.")
            user_score += weight
            state["question_weights"][question]["score"] = weight
        else:
            # incorrect = score -= 1
            print("✗ Incorrect.")
            user_score -= 1
            state["question_weights"][question]["score"] = -1
            wrong_questions.append(question)

            # second chance
            print("Please try again:")
            retry_answer = input("Your answer: ")

            if "don't" in retry_answer.lower() and "know" in retry_answer.lower():
                # pass = score -= 3, save the question
                print("✗ Passed on second chance.")
                user_score -= 3
                state["question_weights"][question]["score"] = -3
            else:
                # Evaluate second attempt
                retry_prompt = f"""Evaluate this {state['requirements']} retry answer:
                
                Question: {question}
                User Answer: {retry_answer}
                
                Is this answer correct?
                Reply with only "CORRECT" or "INCORRECT"."""

                retry_response = safe_llm_invoke(llm, retry_prompt)
                if retry_response is None:
                    print("✗ Evaluation failed.")
                    continue

                is_retry_correct = "CORRECT" in retry_response.content.upper()

                if is_retry_correct:
                    # correct = score += weight/2
                    print("✓ Correct! Good effort.")
                    user_score += (weight / 2)
                    state["question_weights"][question]["score"] = weight / 2
                    # Remove since retry was correct
                    wrong_questions.remove(question)
                else:
                    # incorrect = score -= 2
                    print("✗ Incorrect again.")
                    user_score -= 2
                    state["question_weights"][question]["score"] = -2

        # Store original answer, not retry
        state["answers"].append(user_answer)

    state["user_score"] = user_score
    state["wrong_questions"] = wrong_questions

    print(f"\nEvaluation complete. Total score: {user_score}")
    print(f"Questions couldn't answer: {len(wrong_questions)}")

    return state

def node_3_provide_feedback(state: InterviewState) -> InterviewState:
    """Provides feedback based on performance"""
    
    user_score = state.get("user_score", 0)
    wrong_questions = state.get("wrong_questions", [])
    requirements = state.get("requirements", "")
    total_possible_score = state.get("total_possible_score", 0)

    print("\n" + "="*50)
    print("           INTERVIEW FEEDBACK")
    print("="*50)

    # congratulate if score >= 80%
    if total_possible_score > 0:
        percentage = (user_score / total_possible_score) * 100
        print(
            f"Your Score: {user_score:.1f}/{total_possible_score} ({percentage:.1f}%)")

        if percentage >= 80:
            print("\n🎉 CONGRATULATIONS! 🎉")
            print("We look forward to working with you!")
        else:
            print("\n📚 You need some improvement")
    else:
        print("No scored questions available for evaluation.")

    # not enough score: generate feedback with questions of wrong answers
    if wrong_questions:
        print(f"\nAreas for Improvement ({len(wrong_questions)} questions):")
        print("-" * 40)

        llm = ChatGroq(model="llama-3.1-8b-instant",
                       api_key=os.getenv("GROQ_API_KEY"))

        feedback_prompt = f"""Generate study feedback for someone who couldn't answer these {requirements} questions:

{chr(10).join(f"- {q}" for q in wrong_questions)}

Provide study tips."""

        print("Generating feedback...")
        feedback_response = safe_llm_invoke(llm, feedback_prompt)

        if feedback_response:
            print("\n" + feedback_response.content)
        else:
            print("\nReview these topics:")
            for i, question in enumerate(wrong_questions, 1):
                print(f"{i}. {question}")

    print("\n" + "="*50)
    print("Thank you for taking the interview!")
    print("="*50)

    return state

def create_interview_graph():
    """Create and configure the LangGraph workflow"""
    
    workflow = StateGraph(InterviewState)
    
    # Add nodes
    workflow.add_node("generate_questions", node_1_generate_questions)
    workflow.add_node("evaluate_answers", node_2_evaluate_answers)  
    workflow.add_node("provide_feedback", node_3_provide_feedback)
    
    # Define the flow
    workflow.set_entry_point("generate_questions")
    workflow.add_edge("generate_questions", "evaluate_answers")
    workflow.add_edge("evaluate_answers", "provide_feedback")
    workflow.add_edge("provide_feedback", END)
    
    return workflow.compile()

if __name__ == "__main__":
    # Initialize state with all required fields
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

    # Create and run the LangGraph workflow
    app = create_interview_graph()
    result = app.invoke(initial_state)
    
    print("\n🏁 Interview process completed!")