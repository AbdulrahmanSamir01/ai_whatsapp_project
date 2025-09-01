from django.urls import path
from .views import telegram_webhook, telegram_button

urlpatterns = [
    path("", telegram_button, name="telegram_button"),
    path("webhook/", telegram_webhook),
]
