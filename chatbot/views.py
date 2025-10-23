from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import InterviewSession
import interview_bot
import uuid
import json

# Create your views here.


@csrf_exempt
def start_interview(request):
    # Starts a new interview session and saves it to the database
    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        session_id = str(uuid.uuid4())
        session = InterviewSession.objects.create(
            session_id=session_id,
            user=user,
            current_state={
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
        )
        request.session['interview_session_id'] = session_id
        return JsonResponse({"session_id": session_id})
    return HttpResponseBadRequest("Invalid request method.")


@csrf_exempt
def next_question(request):
    # Returns the next interview question for the current session
    session_id = request.session.get('interview_session_id')
    if not session_id:
        return HttpResponseBadRequest("No active session.")
    session = InterviewSession.objects.get(session_id=session_id)
    state = session.current_state

    # If greeting not shown, show greeting first
    if not state.get("greeting_shown", False):
        question = "Hello, I am Anishom and I will be taking your interview today."
        state["greeting_shown"] = True
    else:
        # Otherwise, return the next unanswered question
        questions = state.get("questions", [])
        answers = state.get("answers", [])
        if len(answers) < len(questions):
            question = questions[len(answers)]
        else:
            question = "Interview complete."
    session.current_state = state
    session.save()
    return JsonResponse({"question": question})


@csrf_exempt
def submit_answer(request):
    # Receives and saves the user's answer for the current question
    session_id = request.session.get('interview_session_id')
    if not session_id:
        return HttpResponseBadRequest("No active session.")
    session = InterviewSession.objects.get(session_id=session_id)
    state = session.current_state

    data = json.loads(request.body)
    answer = data.get("answer")
    if answer is None:
        return HttpResponseBadRequest("No answer provided.")

    state.setdefault("answers", []).append(answer)
    session.current_state = state
    session.save()
    return JsonResponse({"success": True})


def test_view(request):
    # Simple test endpoint to verify the bot file path
    return JsonResponse({"success": True, "file": interview_bot.__file__})
