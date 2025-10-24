from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
import interview_bot
import asyncio


class InterviewBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from .models import InterviewSession  # Import here
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
        await self.start_interview_flow()

    async def receive(self, text_data):
        from .models import InterviewSession  # Import here
        data = json.loads(text_data)
        answer = data.get("answer")
        # Resume interview flow with user's answer
        if hasattr(self, "_pending_input") and self._pending_input:
            self._pending_input.set_result(answer)

    async def start_interview_flow(self):
        # Monkey-patch input_user and print_bot for async WebSocket communication
        async def input_user(prompt):
            await self.send(text_data=json.dumps({"question": prompt}))
            self._pending_input = asyncio.get_event_loop().create_future()
            answer = await self._pending_input
            return answer

        async def print_bot(message):
            await self.send(text_data=json.dumps({"message": message}))

        interview_bot.input_user = input_user
        interview_bot.print_bot = print_bot

        # Run interview nodes step by step
        # 1. Generate questions
        self.state = await interview_bot.node_1_generate_questions(self.state)
        self.save_state()

        # 2. Evaluate answers
        self.state = await interview_bot.node_2_evaluate_answers(self.state)
        self.save_state()

        # 3. Provide feedback
        self.state = await interview_bot.node_3_provide_feedback(self.state)
        self.save_state()

        await self.send(text_data=json.dumps({"message": "Interview complete."}))

    def save_state(self):
        from .models import InterviewSession  # Import here
        session = InterviewSession.objects.get(session_id=self.session_id)
        session.current_state = self.state
        session.save()
