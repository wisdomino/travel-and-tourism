from django.conf import settings
from django.db import models
from django.utils import timezone
from crm.models import Case, Client, Organization


class Channel(models.TextChoices):
    WHATSAPP = "WHATSAPP", "WhatsApp"
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"


class MessageTemplate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="message_templates")
    name = models.CharField(max_length=120)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    is_active = models.BooleanField(default=True)

    subject = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()

    class Meta:
        unique_together = ("organization", "name", "channel")

    def __str__(self) -> str:
        return f"{self.organization.slug} - {self.name} ({self.channel})"


class MessageLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="message_logs")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="messages")
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")

    channel = models.CharField(max_length=20, choices=Channel.choices)
    provider = models.CharField(max_length=50, blank=True, null=True)  # twilio/wati/360dialog/smtp
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()

    status = models.CharField(max_length=30, default="PENDING", db_index=True)  # PENDING/SENT/FAILED
    provider_message_id = models.CharField(max_length=120, blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.organization.slug} {self.client.client_code} {self.channel} {self.status}"

