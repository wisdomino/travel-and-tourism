from __future__ import annotations

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Case, StatusHistory
from messaging.models import Channel
from messaging.services import create_and_send_case_update


@receiver(pre_save, sender=Case)
def store_old_status(sender, instance: Case, **kwargs):
    if not instance.pk:
        instance._old_status = None
        return
    try:
        old = Case.objects.get(pk=instance.pk)
        instance._old_status = old.current_status
    except Case.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=Case)
def case_status_change_handler(sender, instance: Case, created: bool, **kwargs):
    old_status = getattr(instance, "_old_status", None)

    # On create: optionally log initial status
    if created:
        StatusHistory.objects.create(
            case=instance,
            old_status=instance.current_status,
            new_status=instance.current_status,
            changed_by=instance.assigned_officer,
            comment="Case created",
        )
        # Optional: notify client on creation
        instance.last_client_update_at = timezone.now()
        Case.objects.filter(pk=instance.pk).update(last_client_update_at=instance.last_client_update_at)
        return

    # No status change
    if old_status == instance.current_status:
        return

    # 1) log status history
    StatusHistory.objects.create(
        case=instance,
        old_status=old_status or instance.current_status,
        new_status=instance.current_status,
        changed_by=instance.assigned_officer,
        comment="Status updated",
    )

    # 2) mark last client update timestamp
    instance.last_client_update_at = timezone.now()
    Case.objects.filter(pk=instance.pk).update(last_client_update_at=instance.last_client_update_at)

    # 3) send notification (DEMO: console)
    # Use one template name globally for now: "CASE_STATUS_UPDATE"
    create_and_send_case_update(
        case=instance,
        template_name="CASE_STATUS_UPDATE",
        channel=Channel.WHATSAPP,
        triggered_by=instance.assigned_officer,
    )

    # Optionally email too (if client has email)
    if instance.client.email:
        create_and_send_case_update(
            case=instance,
            template_name="CASE_STATUS_UPDATE_EMAIL",
            channel=Channel.EMAIL,
            triggered_by=instance.assigned_officer,
        )
