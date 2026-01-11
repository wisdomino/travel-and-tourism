from django.db import transaction
from django.db.models import Max

from .models import Client, Case, Organization


def _next_code(prefix: str, latest: str | None) -> str:
    if not latest:
        return f"{prefix}-0001"
    try:
        n = int(latest.split("-")[1])
    except Exception:
        n = 0
    return f"{prefix}-{n+1:04d}"


@transaction.atomic
def create_client_with_code(*, organization: Organization, full_name: str, phone_e164: str,
                            email: str | None, timezone: str, preferred_language: str,
                            source: str | None) -> Client:
    latest = Client.objects.aggregate(m=Max("client_code"))["m"]
    code = _next_code("CL", latest)
    return Client.objects.create(
        organization=organization,
        client_code=code,
        full_name=full_name,
        phone_e164=phone_e164,
        email=email,
        timezone=timezone,
        preferred_language=preferred_language,
        source=source,
    )


@transaction.atomic
def create_case_with_code(*, organization, branch, program, client,
                          destination_country_code: str, application_type: str,
                          assigned_officer=None) -> Case:
    latest = Case.objects.aggregate(m=Max("case_code"))["m"]
    code = _next_code("APP", latest)
    return Case.objects.create(
        organization=organization,
        branch=branch,
        program=program,
        case_code=code,
        client=client,
        destination_country_code=destination_country_code,
        application_type=application_type,
        assigned_officer=assigned_officer,
    )
