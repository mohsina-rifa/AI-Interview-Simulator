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
        
        # Assign dynamic weights based on LLM evaluation
        for q in scenario_questions:
            weight_prompt = f"""Based on how many times this question appeared on the internet for {requirement}, what should be the weight for this question within 1 to 10?
            Question: {q}
            Reply with only a number between 1 and 10."""
            weight_response = llm.invoke(weight_prompt)
            try:
                weight = float(weight_response.content.strip())
                weight = max(1, min(10, weight))
            except:
                weight = 5
            state["question_weights"][q] = {"type": "scenario", "weight": weight}
        
        for q in followup_questions:
            weight_prompt = f"""Based on how many times this question appeared on the internet for {requirement}, what should be the weight for this question within 1 to 10?
            Question: {q}
            Reply with only a number between 1 and 10."""
            weight_response = llm.invoke(weight_prompt)
            try:
                weight = float(weight_response.content.strip())
                weight = max(1, min(10, weight))
            except:
                weight = 5
            state["question_weights"][q] = {"type": "followup", "weight": weight}
        
        for q in independent_questions:
            weight_prompt = f"""Based on how many times this question appeared on the internet for {requirement}, what should be the weight for this question within 1 to 10?
            Question: {q}
            Reply with only a number between 1 and 10."""
            weight_response = llm.invoke(weight_prompt)
            try:
                weight = float(weight_response.content.strip())
                weight = max(1, min(10, weight))
            except:
                weight = 5
            state["question_weights"][q] = {"type": "independent", "weight": weight}
        
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
    
    # Map scores of all questions with 0 initially
    for question in questions:
        if "score" not in state["question_weights"].get(question, {}):
            state["question_weights"][question]["score"] = 0
    
    # Generate answers for position-related questions
    print("\nGenerating expected answers for position-related questions...")
    for question in questions:
        q_type = state["question_weights"].get(question, {}).get("type", "unknown")
        
        # Only generate answers for position-related questions (not basic/personal)
        if q_type in ["scenario", "followup", "independent"]:
            answer_prompt = f"""Generate a comprehensive correct answer for this {state['requirements']} interview question:
            Question: {question}
            
            Provide a detailed answer that demonstrates expertise in {state['requirements']}."""
            
            answer_response = llm.invoke(answer_prompt)
            expected_answer = answer_response.content.strip()
            
            # Store expected answer in question weights
            state["question_weights"][question]["expected_answer"] = expected_answer
    
    print("Expected answers generated. Starting interview evaluation...\n")
    
    # Ask questions one by one and evaluate only position-related questions
    for question in questions:
        print(f"\n{question}")
        user_answer = input("Your answer: ")
        
        q_type = state["question_weights"].get(question, {}).get("type", "unknown")
        weight = state["question_weights"].get(question, {}).get("weight", 0)
        
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
        expected_answer = state["question_weights"][question].get("expected_answer", "")
        eval_prompt = f"""Compare the user's answer with the expected answer for this {state['requirements']} question:
        
        Question: {question}
        Expected Answer: {expected_answer}
        User Answer: {user_answer}
        
        Is the user's answer correct and demonstrates good understanding?
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
            
            # Second chance
            print("Please try again (or say 'don't know' to pass):")
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
                
                retry_response = llm.invoke(retry_prompt)
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
    result = node_2_evaluate_answers(result)
    
    print("\n\n=== FINAL INTERVIEW RESULTS ===")
    print(f"Total Score: {result.get('user_score', 0)}")