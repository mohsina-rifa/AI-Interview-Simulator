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


# Nodes


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


# node-1: Question generator
def node_1_generate_questions(state: InterviewState) -> InterviewState:
    """Generates interview questions AND answers based on the role"""

    # Show greeting only once
    if not state.get("greeting_shown", False):
        print("Hello, I am Anishom and I will be taking your interview today.")
        state["greeting_shown"] = True

    starting_questions = [
        "What is your name?",
        "What position have you applied for?",
        "What were the requirements for that?"
    ]

    answers = []
    for question in starting_questions:
        print(f"\n{question}")
        answer = input("Your answer: ")
        answers.append(answer)

    state["questions"] = starting_questions
    state["answers"] = answers
    state["requirements"] = answers[2]
    state["question_weights"] = {}

    requirements_list = [req.strip()
                         for req in state["requirements"].split(",")]

    llm = ChatGroq(model="llama-3.1-8b-instant",
                   api_key=os.getenv("GROQ_API_KEY"))

    for requirement in requirements_list:
        print(f"\nInterview questionset for {requirement}.")

        # Basic Questions (5) - weight: 0
        basic_questions = [
            "Where are you currently living?",
            "Tell us about your previous work experience.",
            "Which university did you graduate from?",
            "What was your major?",
            "What are your future career plans?"
        ]

        for q in basic_questions:
            state["question_weights"][q] = {
                "type": "basic", "weight": 0, "expected_answer": ""}

        # Generate position-related questions WITH answers using single LLM call
        combined_prompt = f"""Generate 23 interview questions for {requirement} skill with their expected answers in this exact format:

SCENARIO: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

SCENARIO: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

(repeat 7 times for SCENARIO)

FOLLOWUP: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

FOLLOWUP: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

(repeat 14 times for FOLLOWUP)

INDEPENDENT: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

INDEPENDENT: [question]
ANSWER: [detailed answer demonstrating {requirement} expertise]
WEIGHT: [number 1-10 based on importance]

(repeat 6 times for INDEPENDENT)

Generate practical, relevant questions that test real {requirement} knowledge."""

        print("Generating questions and answers...")
        response = safe_llm_invoke(llm, combined_prompt)

        if response is None:
            print("Failed to generate questions. Using fallback.")
            continue

        questions_text = response.content.strip()
        lines = questions_text.split("\n")

        scenario_questions = []
        followup_questions = []
        independent_questions = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("SCENARIO:"):
                question = line.replace("SCENARIO: ", "").strip()
                answer = ""
                weight = 5

                # Get answer and weight from next lines
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("ANSWER:"):
                    answer = lines[i + 1].replace("ANSWER: ", "").strip()
                if i + 2 < len(lines) and lines[i + 2].strip().startswith("WEIGHT:"):
                    try:
                        weight = float(
                            lines[i + 2].replace("WEIGHT: ", "").strip())
                        weight = max(1, min(10, weight))
                    except:
                        weight = 5

                scenario_questions.append(question)
                state["question_weights"][question] = {
                    "type": "scenario",
                    "weight": weight,
                    "expected_answer": answer
                }
                i += 3

            elif line.startswith("FOLLOWUP:"):
                question = line.replace("FOLLOWUP: ", "").strip()
                answer = ""
                weight = 5

                if i + 1 < len(lines) and lines[i + 1].strip().startswith("ANSWER:"):
                    answer = lines[i + 1].replace("ANSWER: ", "").strip()
                if i + 2 < len(lines) and lines[i + 2].strip().startswith("WEIGHT:"):
                    try:
                        weight = float(
                            lines[i + 2].replace("WEIGHT: ", "").strip())
                        weight = max(1, min(10, weight))
                    except:
                        weight = 5

                followup_questions.append(question)
                state["question_weights"][question] = {
                    "type": "followup",
                    "weight": weight,
                    "expected_answer": answer
                }
                i += 3

            elif line.startswith("INDEPENDENT:"):
                question = line.replace("INDEPENDENT: ", "").strip()
                answer = ""
                weight = 5

                if i + 1 < len(lines) and lines[i + 1].strip().startswith("ANSWER:"):
                    answer = lines[i + 1].replace("ANSWER: ", "").strip()
                if i + 2 < len(lines) and lines[i + 2].strip().startswith("WEIGHT:"):
                    try:
                        weight = float(
                            lines[i + 2].replace("WEIGHT: ", "").strip())
                        weight = max(1, min(10, weight))
                    except:
                        weight = 5

                independent_questions.append(question)
                state["question_weights"][question] = {
                    "type": "independent",
                    "weight": weight,
                    "expected_answer": answer
                }
                i += 3
            else:
                i += 1

        # Personal Questions (2) - weight: 0
        personal_questions = [
            "What activities do you pursue outside of work?",
            "Why do you think you are a good candidate for this position?"
        ]

        for q in personal_questions:
            state["question_weights"][q] = {
                "type": "personal", "weight": 0, "expected_answer": ""}

        all_questions = basic_questions + scenario_questions + \
            followup_questions + independent_questions + personal_questions
        state["questions"].extend(all_questions)

        print(f"\n✓ Basic Questions: {len(basic_questions)} [weight=0]")
        print(
            f"✓ Scenario Based Questions: {len(scenario_questions)} [weight=dynamic]")
        print(
            f"✓ Follow-up Questions: {len(followup_questions)} [weight=dynamic]")
        print(
            f"✓ Independent Questions: {len(independent_questions)} [weight=dynamic]")
        print(f"✓ Personal Questions: {len(personal_questions)} [weight=0]")
        print(f"Total: {len(all_questions)} questions generated")

    return state


# node-2: Answer evaluator
def node_2_evaluate_answers(state: InterviewState) -> InterviewState:
    """Evaluates answers based on the pre-generated questionset"""

    questions = state["questions"][3:]
    user_score = 0

    llm = ChatGroq(model="llama-3.1-8b-instant",
                   api_key=os.getenv("GROQ_API_KEY"))

    # Map scores of all questions with 0 initially
    for question in questions:
        if "score" not in state["question_weights"].get(question, {}):
            state["question_weights"][question]["score"] = 0

    print("Starting interview evaluation...\n")

    # Ask questions one by one and evaluate
    for question in questions:
        print(f"\n{question}")
        user_answer = input("Your answer: ")

        q_type = state["question_weights"].get(
            question, {}).get("type", "unknown")
        weight = state["question_weights"].get(question, {}).get("weight", 0)
        expected_answer = state["question_weights"].get(
            question, {}).get("expected_answer", "")

        # Check for "don't know" response (pass)
        if "don't" in user_answer.lower() and "know" in user_answer.lower():
            print("✗ Moving to next question.")
            user_score -= 2
            state["question_weights"][question]["score"] = -2
            state["answers"].append(user_answer)
            continue

        # For basic and personal questions, just record with 0
        if q_type in ["basic", "personal"]:
            state["question_weights"][question]["score"] = 0
            state["answers"].append(user_answer)
            continue

        # Evaluate answer using LLM for position-related questions only
        eval_prompt = f"""You are strictly evaluating a {state['requirements']} technical interview answer. Be very strict in your evaluation.

        Question: {question}
        Expected Answer: {expected_answer}
        User Answer: {user_answer}

        Does the user's answer demonstrate correct understanding of {state['requirements']} concepts and match the expected answer's technical accuracy?

        IMPORTANT: 
        - If the user answer contradicts best practices, mark as INCORRECT
        - If the user answer is technically wrong, mark as INCORRECT
        - Only mark CORRECT if the answer shows proper understanding

        Reply with only "CORRECT" or "INCORRECT"."""

        eval_response = safe_llm_invoke(llm, eval_prompt)
        if eval_response is None:
            print("✗ Evaluation failed. Skipping.")
            continue

        is_correct = "CORRECT" in eval_response.content.upper()

        if is_correct:
            print("✓ Correct! Well done.")
            user_score += weight
            state["question_weights"][question]["score"] = weight
        else:
            print("✗ Incorrect.")
            user_score -= 1
            state["question_weights"][question]["score"] = -1

            # Second chance
            print("Please try again:")
            retry_answer = input("Your answer: ")

            # Check if user passes on second chance
            if "don't" in retry_answer.lower() and "know" in retry_answer.lower():
                print("✗ Passed on second chance.")
                user_score -= 3
                state["question_weights"][question]["score"] = -3
            else:
                # Evaluate second attempt
                retry_prompt = f"""Compare the user's retry answer with the expected answer:
                
                Question: {question}
                Expected Answer: {expected_answer}
                User Retry Answer: {retry_answer}
                
                Is the user's retry answer correct?
                Reply with only "CORRECT" or "INCORRECT"."""

                retry_response = safe_llm_invoke(llm, retry_prompt)
                if retry_response is None:
                    print("✗ Evaluation failed. Moving on.")
                    continue

                is_retry_correct = "CORRECT" in retry_response.content.upper()

                if is_retry_correct:
                    print("✓ Correct! Good effort.")
                    user_score += (weight / 2)
                    state["question_weights"][question]["score"] = weight / 2
                else:
                    print("✗ Incorrect again. Moving to next question.")
                    user_score -= 2
                    state["question_weights"][question]["score"] = -2

        state["answers"].append(user_answer)

    state["user_score"] = user_score
    print(f"\nEvaluation complete. Total score: {user_score}")

    return state


if __name__ == "__main__":
    initial_state = {
        "role": "",
        "questions": [],
        "answers": [],
        "requirements": "",
        "greeting_shown": False,
        "question_weights": {}
    }

    result = node_1_generate_questions(initial_state)
    result = node_2_evaluate_answers(result)

    print("\n\n=== FINAL INTERVIEW RESULTS ===")
    print(f"Total Score: {result.get('user_score', 0)}")
