from django.db import models

# Create your models here.
class Conversation(models.Model):
    user_number = models.CharField(max_length=20)   # رقم المستخدم (wa_id)
    user_name = models.CharField(max_length=100, blank=True, null=True)  # الاسم من واتساب
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" Conversation With: {self.user_name or self.user_number}"


class Message(models.Model):
    id = models.AutoField(primary_key=True)  # رقم داخلي
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="معرّف الرسالة من واتساب (للتتبع فقط)")  # ID واتساب
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=10, choices=[("in", "Received"), ("out", "Sent")])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, blank=True, null=True)  # sent, delivered, read
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.direction}] {self.content[:30]}"

