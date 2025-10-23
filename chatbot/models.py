from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class InterviewSession(models.Model):
    session_id = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='interview_sessions')
    current_state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id} for {self.user}"
