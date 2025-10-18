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
def node_2_evaluate_answers(state: InterviewState) -> InterviewState:
    """Evaluates answers based on the questionset"""
    
    questions = state["questions"][3:]
    user_score = 0
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    
    for question in questions:
        print(f"\n{question}")
        user_answer = input("Your answer: ")
        
        q_type = state["question_weights"].get(question, {}).get("type", "unknown")
        weight = state["question_weights"].get(question, {}).get("weight", 0)
        
        # Check for "don't know" response
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
        
        # Evaluate answer using LLM for other question types
        eval_prompt = f"""Is this answer correct and relevant for the question?
        Question: {question}
        Answer: {user_answer}
        Reply with only "CORRECT" or "INCORRECT"."""
        
        eval_response = llm.invoke(eval_prompt)
        is_correct = "CORRECT" in eval_response.content.upper()
        
        if is_correct:
            print("✓ Correct! Well done.")
            user_score += weight
            state["question_weights"][question]["score"] = weight
        else:
            print("✗ Incorrect.")
            user_score -= 1
            state["question_weights"][question]["score"] = -1
            
            # Ask to try again
            print("Please try again:")
            retry_answer = input("Your answer: ")
            
            retry_prompt = f"""Is this answer correct and relevant for the question?
            Question: {question}
            Answer: {retry_answer}
            Reply with only "CORRECT" or "INCORRECT"."""
            
            retry_response = llm.invoke(retry_prompt)
            is_retry_correct = "CORRECT" in retry_response.content.upper()
            
            if is_retry_correct:
                print("✓ Correct! Good effort.")
                user_score += (weight / 2)
                state["question_weights"][question]["score"] = weight / 2
            else:
                print("✗ Moving to next question.")
                user_score -= 2
                state["question_weights"][question]["score"] = -2
        
        state["answers"].append(user_answer)
    
    state["user_score"] = user_score
    return state


#node-3: Feedback provider
#



# Graph setup
#


# Test function
#


if __name__ == "__main__":
    pass