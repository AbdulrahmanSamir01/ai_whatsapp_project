import json
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import render

from .models import Conversation, Message
from django.conf import settings
from ai_engine.factory import get_ai_responder

def telegram_button(request):
    """عرض صفحة زر تيليجرام المستقبلي"""
    return render(request, "telegram.html")



BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

responder = get_ai_responder()  # ✅ مرن للتبديل


@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print("📩 Event:", json.dumps(data, indent=2, ensure_ascii=False))

        try:
            if "message" in data:
                incoming_msg = data["message"]
                chat_id      = incoming_msg["chat"]["id"]
                user_name    = incoming_msg["chat"].get("first_name", "مستخدم مجهول")
                message_body = incoming_msg.get("text", "")
                msg_id       = incoming_msg.get("message_id")

                # 📌 إنشاء أو جلب المحادثة
                conv, _ = Conversation.objects.get_or_create(
                    user_number=chat_id,
                    defaults={"user_name": user_name}
                )

                # 📝 تخزين الرسالة الواردة
                Message.objects.create(
                    conversation=conv,
                    direction="in",
                    content=message_body,
                    message_id=msg_id
                )

                # 👇 الرد باستخدام الذكاء الاصطناعي
                try:
                    ai_reply = responder.reply(conv, message_body, user_name)
                except Exception as e:
                    ai_reply = "⚠️ حدث خطأ مؤقت في خدمة الذكاء الاصطناعي."
                    print("AI error:", e)

                # 📤 إرسال الرد عبر Telegram
                response = send_telegram_message(chat_id, ai_reply)

                # 📝 تخزين رد الذكاء الاصطناعي
                if response.ok:
                    resp_json = response.json()
                    Message.objects.create(
                        conversation=conv,
                        direction="out",
                        content=ai_reply,
                        message_id=resp_json.get("result", {}).get("message_id"),
                        status="sent"
                    )

        except Exception as e:
            print("⚠️ Error during processing:", e)

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("Invalid method", status=405)


def send_telegram_message(chat_id, message):
    """📤 إرسال رسالة عبر Telegram Bot API"""
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(TELEGRAM_URL, data=payload)

    if not response.ok:
        print("❌ Telegram API Error:", response.status_code, response.text)
    else:
        print("📤 Message sent successfully")

    return response
