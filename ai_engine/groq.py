# ai_engine/groq_responder.py
import re
import logging
from groq import Groq
from django.conf import settings
from .base import BaseAIResponder
from .models import AIConfig
from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)

class GroqResponder(BaseAIResponder):
    """مسؤول عن الرد عبر Groq API."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model   = model   or settings.GROQ_MODEL
        if not self.api_key:
            raise RuntimeError("❌ GROQ_API_KEY Unknown !")
        self.client = Groq(api_key=self.api_key)

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
            config = AIConfig.objects.get(name="نور")
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
        هذه هي المعلومات التي تحتاج الي معرفتها {user_prompt} .
        و هذا أخر 10 محادثات بينك وبين العميل  : {formatted_history}.
        وهو الأن يسألك عن : {user_msg}

        من المعلومات الأخري التي يجب ان تعرفها هو ان هذا {user_name} اسم العميل أو كما يسمي نفسه سواء علي تليجرام او واتساب ، 
        ولا يجب ذكر هذه المعلومه إلا إذا سأل عنها حتي لا يتعجب العميل أو يقلق .
        و عندما يسال لا تنسي توضيح انه هكذا سمي نفسه علي التطبيق الذي تتواصلون به (واتس اب أو تليجرام).

        تجنب إستعمال الرموز مثل ** ﻷنها لن تظهر في الشات الخاص بتليجرام او واتس اب
        """

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            raw = resp.choices[0].message.content.strip()
            clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            return clean or "عذرًا، لم أستطع توليد ردّ مناسب الآن."
        except Exception as e:
            logger.exception("GroqResponder failed")
            return "⚠️ عذرًا، حدث خطأ مؤقت في خدمة الذكاء الاصطناعي. حاول لاحقًا."
