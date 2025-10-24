const ws = new WebSocket(
  'ws://' + window.location.host + '/ws/interview/'
);

ws.onopen = function () {
  // Start interview session
  ws.send(JSON.stringify({ action: "next_question" }));
};

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.question) {
    addMessage("bot", data.question);
  } else if (data.message) {
    addMessage("bot", data.message);
  } else if (data.error) {
    addMessage("bot", data.error);
  }
};

function addMessage(sender, text) {
  const chatMessages = document.getElementById('chat-messages');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-bubble ' + sender;
  msgDiv.textContent = text;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.getElementById('chat-form').onsubmit = function (e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const answer = input.value.trim();
  if (answer) {
    addMessage("user", answer);
    ws.send(JSON.stringify({ action: "submit_answer", answer: answer }));
    input.value = '';
  }
};