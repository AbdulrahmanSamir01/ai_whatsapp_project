from django.contrib import admin
from .models import AIConfig

@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")   # يظهر الاسم والحالة
    list_editable = ("is_active",)         # تقدر تغيّر الحالة من الجدول مباشرة
    search_fields = ("name",)
