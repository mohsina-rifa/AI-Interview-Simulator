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


# Nodes

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
    
    requirements_list = [req.strip() for req in state["requirements"].split(",")]
    
    for requirement in requirements_list:
        print(f"\nInterview questionset for {requirement}.")
    
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
    pass