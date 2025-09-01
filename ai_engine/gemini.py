import re
import logging
from django.conf import settings
from django.shortcuts import get_object_or_404
from .base import BaseAIResponder
import google.generativeai as genai  # مكتبة Gemini الرسمية
from .models import AIConfig


logger = logging.getLogger(__name__)

class GeminiResponder(BaseAIResponder):
    """مسؤول عن الرد عبر Gemini Flash API."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = settings.GEMINI_API_KEY 
        self.model   = settings.GEMINI_MODEL 
        if not self.api_key:
            raise RuntimeError("❌ GEMINI_API_KEY Unknown !")

        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)

    def _format_history(self, messages):
        """تهيئة سجل المحادثة."""
        items = []
        for m in messages:
            role = "👤 العميل" if m.direction == "in" else "🤖 الذكاء الاصطناعي"
            items.append(f"{role}: {m.content}")
        return "\n".join(items)

    def reply(self, conversation_or_user, user_msg: str, user_name: str | None = None) -> str:
        # ======= تجهيز Conversation =======
        if hasattr(conversation_or_user, "messages"):
            conv = conversation_or_user
        else:
            from whatsapp_app.models import Conversation
            conv, _ = Conversation.objects.get_or_create(
                user_number=str(conversation_or_user),
                defaults={"user_name": user_name or "مستخدم مجهول"}
            )

        # ======= تجهيز التاريخ =======
        history_qs = conv.messages.order_by("-timestamp")[: getattr(settings, "AI_HISTORY_SIZE", 10)]
        history = list(reversed(history_qs))
        formatted_history = self._format_history(history)

        try:
            # المحاولة الأولى: الحصول على البرومبت بالاسم
            config = AIConfig.objects.get(name="كريم")
        except AIConfig.DoesNotExist:
            # fallback: الحصول على آخر واحد تمت إضافته
            config = AIConfig.objects.last()

        # 🧩 تخزين الحقول في متغيرات
        config_name = config.name
        system_prompt = config.system_prompt
        user_prompt = config.user_prompt


        system_prompt = f"""
            {config_name}
            {system_prompt}
        """

        prompt = f"""
        يجب أن تكون ردودك بهذا الشكل : {user_prompt} .
         مع العلم أن هذا أخر 10 محادثات بينك وبين {user_name} : {formatted_history}.
        قم بالترحيب به فقط اذا لم يكن بينك وبين العميل محادثات قديمه .

        وهو الأن يسألك عن :
        {user_msg}
        """

        try:
            resp = self.client.generate_content(
                [system_prompt, prompt],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 400
                }
            )
            raw = resp.text.strip() if hasattr(resp, "text") else str(resp)
            return raw or "عذرًا، لم أستطع توليد ردّ مناسب الآن."
        except Exception as e:
            logger.exception("GeminiResponder failed")
            return "⚠️ عذرًا، حدث خطأ مؤقت في خدمة الذكاء الاصطناعي. حاول لاحقًا."
