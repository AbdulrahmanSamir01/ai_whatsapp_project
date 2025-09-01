from django.db import models

# Create your models here.
class AIConfig(models.Model):
    name = models.CharField(max_length=100, unique=True)
    system_prompt = models.TextField()
    user_prompt = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
