from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Case
from .portal_services import request_portal_otp, verify_portal_otp


SESSION_KEY = "portal_client"


def portal_start(request):
    if request.method == "POST":
        client_code = request.POST.get("client_code", "").strip().upper()
        phone_e164 = request.POST.get("phone_e164", "").strip()

        try:
            request_portal_otp(
                client_code=client_code,
                phone_e164=phone_e164,
                request_ip=_get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            request.session["portal_client_code"] = client_code
            request.session["portal_phone"] = phone_e164
            return redirect("portal_verify")
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, "portal/start.html")


def portal_verify(request):
    client_code = request.session.get("portal_client_code")
    phone_e164 = request.session.get("portal_phone")
    if not client_code or not phone_e164:
        return redirect("portal_start")

    if request.method == "POST":
        code = request.POST.get("otp", "").strip()
        try:
            client = verify_portal_otp(client_code=client_code, phone_e164=phone_e164, code=code)
            request.session[SESSION_KEY] = client.id
            return redirect("portal_status")
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, "portal/verify.html", {"client_code": client_code, "phone_e164": phone_e164})


def portal_status(request):
    client_id = request.session.get(SESSION_KEY)
    if not client_id:
        return redirect("portal_start")

    cases = (
        Case.objects
        .select_related("program", "branch")
        .filter(client_id=client_id)
        .order_by("-updated_at")
    )
    return render(request, "portal/status.html", {"cases": cases})


def portal_logout(request):
    request.session.pop(SESSION_KEY, None)
    request.session.pop("portal_client_code", None)
    request.session.pop("portal_phone", None)
    messages.info(request, "You have been logged out.")
    return redirect("portal_start")


def _get_ip(request):
    # Basic proxy-safe-ish extraction
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
