from django.contrib import admin
from .models import MessageTemplate, MessageLog


# -----------------------------
# MESSAGE TEMPLATES
# -----------------------------

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "channel",
        "is_active",
    )
    list_filter = ("organization", "channel", "is_active")
    search_fields = ("name", "body")
    ordering = ("organization", "name")

    fieldsets = (
        ("Template Info", {
            "fields": (
                "organization",
                "name",
                "channel",
                "is_active",
            )
        }),
        ("Message Content", {
            "fields": (
                "subject",
                "body",
            )
        }),
    )


# -----------------------------
# MESSAGE LOGS (AUDIT & DELIVERY)
# -----------------------------

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "client",
        "case",
        "channel",
        "provider",
        "recipient",
        "status",
        "created_at",
        "sent_at",
    )
    list_filter = (
        "organization",
        "channel",
        "provider",
        "status",
        "created_at",
    )
    search_fields = (
        "client__client_code",
        "client__full_name",
        "recipient",
        "case__case_code",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "organization",
        "client",
        "case",
        "channel",
        "provider",
        "recipient",
        "subject",
        "content",
        "status",
        "provider_message_id",
        "error",
        "created_at",
        "sent_at",
        "triggered_by",
    )
