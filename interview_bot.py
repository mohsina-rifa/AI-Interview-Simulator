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

from langchain_groq import ChatGroq

#node-1: Question generator
def node_1_generate_questions(state: InterviewState) -> InterviewState:
    """Generates interview questions based on the role"""
    
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
    
    requirements_list = [req.strip() for req in state["requirements"].split(",")]
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    
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
            state["question_weights"][q] = {"type": "basic", "weight": 0}
        
        # Generate position-related questions using LLM
        prompt = f"""Generate 23 interview questions for {requirement} skill in this exact format:
        SCENARIO: [question]
        SCENARIO: [question]
        (repeat 6 times)
        FOLLOWUP: [question]
        FOLLOWUP: [question]
        (repeat 13 times)
        INDEPENDENT: [question]
        INDEPENDENT: [question]
        (repeat 4 times)"""
        
        response = llm.invoke(prompt)
        questions_text = response.content.strip()
        
        scenario_questions = [q.replace("SCENARIO: ", "").strip() for q in questions_text.split("\n") if q.startswith("SCENARIO:")]
        followup_questions = [q.replace("FOLLOWUP: ", "").strip() for q in questions_text.split("\n") if q.startswith("FOLLOWUP:")]
        independent_questions = [q.replace("INDEPENDENT: ", "").strip() for q in questions_text.split("\n") if q.startswith("INDEPENDENT:")]
        
        for q in scenario_questions:
            state["question_weights"][q] = {"type": "scenario", "weight": 0}
        
        for q in followup_questions:
            state["question_weights"][q] = {"type": "followup", "weight": 0}
        
        for q in independent_questions:
            state["question_weights"][q] = {"type": "independent", "weight": 0}
        
        # Personal Questions (2) - weight: 0
        personal_questions = [
            "What activities do you pursue outside of work?",
            "Why do you think you are a good candidate for this position?"
        ]
        
        for q in personal_questions:
            state["question_weights"][q] = {"type": "personal", "weight": 0}
        
        all_questions = basic_questions + scenario_questions + followup_questions + independent_questions + personal_questions
        state["questions"].extend(all_questions)
        
        print(f"\n✓ Basic Questions: {len(basic_questions)} [weight=0]")
        print(f"✓ Scenario Based Questions: {len(scenario_questions)} [weight=dynamic]")
        print(f"✓ Follow-up Questions: {len(followup_questions)} [weight=dynamic]")
        print(f"✓ Independent Questions: {len(independent_questions)} [weight=dynamic]")
        print(f"✓ Personal Questions: {len(personal_questions)} [weight=0]")
        print(f"Total: {len(all_questions)} questions generated")
    
    return state
    

#node-2: Answer evaluator
#

#node-3: Feedback provider
#


# Graph setup
#


# Test function
#


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
    print("\n\n=== FINAL STATE ===")
    print(f"Name: {result['answers'][0]}")
    print(f"Position: {result['answers'][1]}")
    print(f"Requirements: {result['requirements']}")
    print(f"Total Questions: {len(result['questions'])}")
    print(f"Question Weights Keys: {len(result['question_weights'])}")