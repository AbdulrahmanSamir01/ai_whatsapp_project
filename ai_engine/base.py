# ai_engine/base.py
from abc import ABC, abstractmethod

class BaseAIResponder(ABC):
    """واجهة عامة لأي مزود ذكاء اصطناعي."""

    @abstractmethod
    def reply(self, conversation_or_user, user_msg: str, user_name: str | None = None) -> str:
        pass
