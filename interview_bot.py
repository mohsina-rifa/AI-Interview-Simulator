from typing import Dict, List, TypedDict
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

load_dotenv()


class InterviewState(TypedDict):
    role: str
    questions: List[str]
    greeting_shown: bool


# Nodes

#node-1: Question generator
def node_1_generate_questions(state: InterviewState) -> InterviewState:
    """Generates interview questions based on the role"""
    
    # Show greeting only once
    if not state.get("greeting_shown", False):
        print("Hello, I am Anishom and I will be taking your interview today.")
        state["greeting_shown"] = True
    
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