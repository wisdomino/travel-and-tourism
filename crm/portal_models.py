import secrets
from django.db import models
from django.utils import timezone

from .models import Client


class OneTimePassword(models.Model):
    """
    OTP for client portal authentication.
    Sent via console in demo; later via WhatsApp/Email provider.
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(blank=True, null=True)

    # Anti-abuse (lightweight)
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_code() -> str:
        # 6-digit numeric code
        return f"{secrets.randbelow(1_000_000):06d}"
