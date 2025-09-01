# ai_engine/factory.py
from django.conf import settings
from .groq import GroqResponder
from .gemini import GeminiResponder
# من الممكن إضافة مزودين آخرين: OpenAIResponder, GeminiResponder ...

def get_ai_responder():
    """اختيار مزود الذكاء الاصطناعي من الإعدادات."""
    model = getattr(settings, "AI_MODEL", "groq")

    if model == "groq":
        return GroqResponder()
    elif model == "gemini":
        return GeminiResponder()
    # elif model == "openai":
    #     return OpenAIResponder()

    raise ValueError(f"❌ Unknown AI model: {model}")
