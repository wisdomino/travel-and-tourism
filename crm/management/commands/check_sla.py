from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from crm.models import Case, CaseStatus
from messaging.models import Channel
from messaging.services import create_and_send_case_update


class Command(BaseCommand):
    help = "Check cases with no client update beyond SLA and notify staff (demo)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="SLA days without update")

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timezone.timedelta(days=days)

        qs = Case.objects.filter(
            Q(last_client_update_at__isnull=True) | Q(last_client_update_at__lt=cutoff),
        ).exclude(current_status__in=[CaseStatus.CLOSED, CaseStatus.APPROVED, CaseStatus.REFUSED])

        count = qs.count()
        self.stdout.write(self.style.WARNING(f"Found {count} case(s) beyond SLA ({days} days)."))

        # Demo: log to console by sending a standard message to the client
        # In production you might notify staff instead, or send a "we are still processing" update.
        for case in qs[:200]:
            create_and_send_case_update(
                case=case,
                template_name="SLA_REASSURANCE",
                channel=Channel.WHATSAPP,
                triggered_by=case.assigned_officer,
            )

        self.stdout.write(self.style.SUCCESS("SLA check completed."))
