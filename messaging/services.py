from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from django.utils import timezone

from crm.models import Case
from .models import MessageTemplate, MessageLog, Channel


@dataclass
class RenderContext:
    client_name: str
    client_code: str
    case_code: str
    status: str
    country: str
    app_type: str
    next_action: str
    last_update: str


def build_render_context(case: Case) -> RenderContext:
    client = case.client
    last_update = (case.last_client_update_at or timezone.now()).astimezone(timezone.get_current_timezone())
    return RenderContext(
        client_name=client.full_name,
        client_code=client.client_code,
        case_code=case.case_code,
        status=case.get_current_status_display(),
        country=case.destination_country_code,
        app_type=case.get_application_type_display(),
        next_action=case.next_action or "",
        last_update=last_update.strftime("%Y-%m-%d %H:%M"),
    )


def render_text(template_text: str, ctx: RenderContext) -> str:
    # Safe simple placeholder replacement
    return template_text.format(
        client_name=ctx.client_name,
        client_code=ctx.client_code,
        case_code=ctx.case_code,
        status=ctx.status,
        country=ctx.country,
        app_type=ctx.app_type,
        next_action=ctx.next_action,
        last_update=ctx.last_update,
    )


def get_template(*, organization_id: int, name: str, channel: str) -> Optional[MessageTemplate]:
    return (
        MessageTemplate.objects
        .filter(organization_id=organization_id, name=name, channel=channel, is_active=True)
        .first()
    )


# ----------------------------
# Provider (Demo): Console sender
# ----------------------------

def send_via_console(log: MessageLog) -> None:
    """
    Safe demo provider for Render/local: prints to logs (Render shows in deploy logs).
    """
    print("\n=== OUTGOING MESSAGE (DEMO) ===")
    print(f"CHANNEL: {log.channel}")
    print(f"TO: {log.recipient}")
    if log.subject:
        print(f"SUBJECT: {log.subject}")
    print("CONTENT:")
    print(log.content)
    print("=== END ===\n")


def create_and_send_case_update(*, case: Case, template_name: str, channel: str, triggered_by=None) -> MessageLog:
    tmpl = get_template(organization_id=case.organization_id, name=template_name, channel=channel)
    if not tmpl:
        # Create a log that records missing template to help debugging
        return MessageLog.objects.create(
            organization_id=case.organization_id,
            client=case.client,
            case=case,
            channel=channel,
            provider="console",
            recipient=case.client.phone_e164 if channel == Channel.WHATSAPP else (case.client.email or ""),
            subject="",
            content=f"[Missing template: {template_name} for {channel}]",
            status="FAILED",
            error="Template not found or inactive",
            triggered_by=triggered_by,
        )

    ctx = build_render_context(case)
    subject = render_text(tmpl.subject or "", ctx) if tmpl.subject else ""
    body = render_text(tmpl.body, ctx)

    recipient = case.client.phone_e164 if channel == Channel.WHATSAPP else (case.client.email or "")

    log = MessageLog.objects.create(
        organization_id=case.organization_id,
        client=case.client,
        case=case,
        channel=channel,
        provider="console",
        recipient=recipient,
        subject=subject,
        content=body,
        status="PENDING",
        triggered_by=triggered_by,
    )

    # Demo send
    try:
        send_via_console(log)
        log.status = "SENT"
        log.sent_at = timezone.now()
        log.save(update_fields=["status", "sent_at"])
    except Exception as e:
        log.status = "FAILED"
        log.error = str(e)
        log.save(update_fields=["status", "error"])

    return log
