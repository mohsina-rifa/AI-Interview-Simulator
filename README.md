# LLM-Powered Automation & Productivity with LangChain, N8N & RA



The task is to build an interview bot using LangGraph nodes

    Node-1  : generates Questions based on role
    Node-2  : evaluates Answers
    Node-3  : gives Feedback



## DESCRIPTION

**node-1**:
• Generate greeting-message
• Ask starting-questions:
    ◦ name
    ◦ applied-position
    ◦ requirements
• Get answer from user
• Generate questions with "requirement(s)":
    ◦ basic                 =   5
    ◦ position-related      =   23
    ◦ personal              =   2
• Assign weight to answer
_____________________________________________________________________________
______________________________________▼______________________________________

**node-2**:
• receieve question-set
• generate answer for position-related questions
• map scores of all questions with 0 initially.
• ask one by one and evaluate only the position-related questions:
    ◦ correct   :   score += weight
    ◦ incorrect :   score -= 1
                    second chance   :   correct     :   score += weight / 2
                                        incorrect   :   score -= 2
                                                        save the question
                                        pass        :   score -= 3
                                                        save the question
    ◦ pass      :   score -= 2
                    save the question
_____________________________________________________________________________
______________________________________▼______________________________________

**node-3**:
• receieve saved-question
• congratulate if score >= 80%
• not enough score:
    ◦ generate feedback with questions of wrong answers
    ◦ send user the area of improvement
