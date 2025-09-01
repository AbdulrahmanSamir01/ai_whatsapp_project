from django.urls import path
from whatsapp_app import views

urlpatterns = [
    path("webhook/", views.webhook, name="webhook"),

]
