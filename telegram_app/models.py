from django.db import models

class Conversation(models.Model):
    user_number = models.CharField(max_length=50)   # chat_id من Telegram
    user_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation With: {self.user_name or self.user_number}"


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    message_id = models.CharField(
        max_length=255,
        unique=False,   # Telegram message_id قد يتكرر على محادثات مختلفة
        null=True,
        blank=True
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=10, choices=[("in", "Received"), ("out", "Sent")])
    content = models.TextField()
    status = models.CharField(max_length=20, blank=True, null=True)  # sent / error
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.direction}] {self.content[:30]}"
