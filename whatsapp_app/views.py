import json
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from .models import Conversation, Message
from django.conf import settings
from ai_engine.factory import get_ai_responder

# إعدادات
VERIFY_TOKEN = "As@#_32592285"

responder = get_ai_responder()  # ✅ مرن للتبديل


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        # ✅ التحقق عند ربط واتساب
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse("Invalid token", status=403)

    elif request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print("📩 Event:", json.dumps(data, indent=2, ensure_ascii=False))

        try:
            entry = data["entry"][0]["changes"][0]["value"]

            # 🟢 استقبال رسالة جديدة
            if "messages" in entry:
                phone_number_id = entry["metadata"]["phone_number_id"]
                incoming_msg    = entry["messages"][0]
                from_number     = incoming_msg["from"]
                message_body    = incoming_msg["text"]["body"]
                msg_id          = incoming_msg["id"]  # wamid
                contact         = entry.get("contacts", [{}])[0]
                user_name       = contact.get("profile", {}).get("name", "مستخدم مجهول")

                # 📌 إنشاء أو جلب المحادثة
                conv, _ = Conversation.objects.get_or_create(
                    user_number=from_number,
                    defaults={"user_name": user_name}
                )

                # 📝 تخزين الرسالة الواردة
                Message.objects.create(
                    conversation=conv,
                    direction="in",
                    content=message_body,
                    message_id=msg_id
                )

                # 👇 الرد باستخدام الذكاء الاصطناعي مع مراعاة سياق المحادثة
                try:
                    ai_reply = responder.reply(conv, message_body, user_name)
                except Exception as e:
                    ai_reply = "⚠️ حدث خطأ مؤقت في خدمة الذكاء الاصطناعي. حاول لاحقًا."
                    print("AI error:", e)

                # 📤 إرسال الرد عبر واتساب
                response = send_whatsapp_message(phone_number_id, from_number, ai_reply)

                # 📝 تخزين رد الذكاء الاصطناعي
                Message.objects.create(
                    conversation=conv,
                    direction="out",
                    content=ai_reply,
                    message_id=response.json().get("messages", [{}])[0].get("id"),  # نخزن الـ wamid اللي رجع من API
                    status="sent" if response.ok else "error"
                )

            # 🟠 تحديثات حالة الرسائل (sent – delivered – read)
            elif "statuses" in entry:
                for status in entry["statuses"]:
                    msg_id = status.get("id")  # ده الـ wamid
                    msg_status = status.get("status")
                    timestamp = status.get("timestamp")

                    # ✅ نحدث باستخدام message_id (مش id الداخلي)
                    Message.objects.filter(message_id=msg_id).update(
                        status=msg_status,
                        timestamp=now()
                    )
                    print(f"📊 Message status: {msg_id}: {msg_status} (⏰ {timestamp})")

        except Exception as e:
            print("⚠️ Error during processing:", e)

        return HttpResponse("EVENT_RECEIVED", status=200)


def send_whatsapp_message(phone_number_id, to_number, message):
    """📤 إرسال رسالة واتساب عبر Cloud API"""
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.PAGE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)

    if not response.ok:
        print("❌ WhatsApp API Error:", response.status_code, response.text)
    else:
        print("📤 Message sent successfully")

    return response
