from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import InterviewSession
import uuid
import interview_bot


class InterviewBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
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
        InterviewSession.objects.create(
            session_id=self.session_id,
            user=None,
            current_state=self.state
        )
        await self.send(text_data=json.dumps({"message": "Interview started!", "session_id": self.session_id}))
        # Start the interview process by generating questions
        await self.run_interview_step("generate_questions")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        answer = data.get("answer")

        session = InterviewSession.objects.get(session_id=self.session_id)
        self.state = session.current_state

        # Store user answer if provided
        if action == "submit_answer" and answer is not None:
            self.state.setdefault("answers", []).append(answer)
            session.current_state = self.state
            session.save()
            await self.send(text_data=json.dumps({"message": "Answer received."}))
            await self.run_interview_step("evaluate_answers")
        else:
            await self.send(text_data=json.dumps({"error": "Invalid action or missing answer."}))

    async def run_interview_step(self, step):
        # Monkey-patch input_user and print_bot for async WebSocket communication
        def input_user(prompt):
            # Send question to frontend and wait for answer
            import asyncio
            future = asyncio.get_event_loop().create_future()
            self._pending_input = future
            self._pending_prompt = prompt
            self.send_sync({"question": prompt})
            return future

        def print_bot(message):
            self.send_sync({"message": message})

        # Patch interview_bot functions
        interview_bot.input_user = input_user
        interview_bot.print_bot = print_bot

        # Run the appropriate node
        if step == "generate_questions":
            new_state = interview_bot.node_1_generate_questions(self.state)
        elif step == "evaluate_answers":
            new_state = interview_bot.node_2_evaluate_answers(self.state)
            # After evaluation, provide feedback
            new_state = interview_bot.node_3_provide_feedback(new_state)
        else:
            new_state = self.state

        # Save updated state
        session = InterviewSession.objects.get(session_id=self.session_id)
        session.current_state = new_state
        session.save()
        self.state = new_state

    def send_sync(self, data):
        # Helper to send data from sync context
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self.send(text_data=json.dumps(data)))
