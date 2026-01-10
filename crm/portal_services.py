from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Client
from .models import OneTimePassword  # if placed in crm/models.py
from messaging.models import Channel
from messaging.services import create_and_send_case_update


OTP_TTL_MINUTES = 10
OTP_MAX_PER_HOUR = 5


def _recent_otp_count(client: Client) -> int:
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    return OneTimePassword.objects.filter(client=client, created_at__gte=one_hour_ago).count()


def request_portal_otp(*, client_code: str, phone_e164: str, request_ip: str | None, user_agent: str | None) -> OneTimePassword:
    client = Client.objects.filter(client_code=client_code, phone_e164=phone_e164).first()
    if not client:
        raise ValidationError("Client not found. Check Client ID and phone number.")

    if _recent_otp_count(client) >= OTP_MAX_PER_HOUR:
        raise ValidationError("Too many OTP requests. Please try again later.")

    code = OneTimePassword.generate_code()
    otp = OneTimePassword.objects.create(
        client=client,
        code=code,
        expires_at=timezone.now() + timezone.timedelta(minutes=OTP_TTL_MINUTES),
        request_ip=request_ip,
        user_agent=(user_agent or "")[:300],
    )

    # DEMO send: use messaging console output via MessageLog
    # We'll reuse messaging layer but send a portal OTP template.
    # Create a CASE-LESS message: we can log without case by calling MessageLog directly later;
    # simplest now: print to logs here.
    print("\n=== PORTAL OTP (DEMO) ===")
    print(f"Client: {client.client_code} - {client.full_name}")
    print(f"Phone: {client.phone_e164}")
    print(f"OTP Code: {code} (expires in {OTP_TTL_MINUTES} mins)")
    print("=== END OTP ===\n")

    return otp


def verify_portal_otp(*, client_code: str, phone_e164: str, code: str) -> Client:
    client = Client.objects.filter(client_code=client_code, phone_e164=phone_e164).first()
    if not client:
        raise ValidationError("Client not found.")

    otp = (
        OneTimePassword.objects
        .filter(client=client, code=code, used_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if not otp:
        raise ValidationError("Invalid OTP.")

    if otp.is_expired:
        raise ValidationError("OTP expired. Please request a new one.")

    otp.used_at = timezone.now()
    otp.save(update_fields=["used_at"])
    return client
