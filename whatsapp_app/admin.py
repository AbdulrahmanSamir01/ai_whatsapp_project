from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("user_name", "user_number", "created_at", "view_messages", "message_count")
    search_fields = ("user_name", "user_number")
    ordering = ("-created_at",)
    readonly_fields = ("user_name", "user_number", "created_at")

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "عدد الرسائل"

    def view_messages(self, obj):
        url = (
            reverse("admin:whatsapp_app_message_changelist")
            + f"?conversation__id__exact={obj.id}"
        )
        return format_html(f"<a href='{url}'>📩 عرض الرسائل</a>")
    view_messages.short_description = "الرسائل"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # السماح بالحذف فقط إذا كان superuser
        return request.user.is_superuser


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "direction", "short_content", "status", "timestamp")
    list_filter = ("direction", "status", "timestamp")
    search_fields = ("content", "conversation__user_number", "conversation__user_name")
    ordering = ("-timestamp",)
    readonly_fields = ("conversation", "direction", "content", "timestamp", "status", "message_id")

    fieldsets = (
        (None, {
            "fields": ("conversation", "direction", "content", "status", "timestamp")
        }),
        ("Internal Info", {
            "fields": ("message_id",),
            "classes": ("collapse",),
        }),
    )

    def short_content(self, obj):
        return obj.content[:40] + ("..." if len(obj.content) > 40 else "")
    short_content.short_description = "Message"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # السماح بالحذف فقط إذا كان superuser
        return request.user.is_superuser
