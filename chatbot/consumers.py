from channels.generic.websocket import AsyncWebsocketConsumer
import json


class InterviewBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to InterviewBot!"}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data.get("message")
        # Here, call your interview_bot logic and get bot response
        bot_response = f"Echo: {user_message}"  # Replace with actual bot logic
        await self.send(text_data=json.dumps({"message": bot_response}))
