from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import InterviewSession
import uuid


class InterviewBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Create a new interview session for this connection
        self.session_id = str(uuid.uuid4())
        self.state = {
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
        # Save session to DB
        InterviewSession.objects.create(
            session_id=self.session_id,
            user=None,  # You can set user if using authentication
            current_state=self.state
        )
        await self.send(text_data=json.dumps({"message": "Interview started!", "session_id": self.session_id}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        answer = data.get("answer")

        # Load session from DB
        session = InterviewSession.objects.get(session_id=self.session_id)
        self.state = session.current_state

        if action == "next_question":
            # Send next question to frontend
            questions = self.state.get("questions", [])
            answers = self.state.get("answers", [])
            if not self.state.get("greeting_shown", False):
                question = "Hello, I am Anishom and I will be taking your interview today."
                self.state["greeting_shown"] = True
            elif len(answers) < len(questions):
                question = questions[len(answers)]
            else:
                question = "Interview complete."
            session.current_state = self.state
            session.save()
            await self.send(text_data=json.dumps({"question": question}))

        elif action == "submit_answer" and answer is not None:
            # Save answer and send next question
            self.state.setdefault("answers", []).append(answer)
            session.current_state = self.state
            session.save()
            await self.send(text_data=json.dumps({"message": "Answer received."}))
            # Optionally, send next question automatically
            questions = self.state.get("questions", [])
            answers = self.state.get("answers", [])
            if len(answers) < len(questions):
                next_question = questions[len(answers)]
                await self.send(text_data=json.dumps({"question": next_question}))
            else:
                await self.send(text_data=json.dumps({"message": "Interview complete."}))

        else:
            await self.send(text_data=json.dumps({"error": "Invalid action or missing answer."}))
