from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import Client, Case
from .forms import ClientCreateForm, CaseCreateForm
from .services import create_client_with_code, create_case_with_code

from .models import Case, CaseStatus, StatusHistory

User = get_user_model()

@login_required
def staff_home(request):
    return render(request, "staff/home.html")


@login_required
def case_list(request):
    qs = Case.objects.select_related("client", "program", "branch").order_by("-updated_at")

    status = request.GET.get("status")
    country = request.GET.get("country")
    q = request.GET.get("q")

    if status:
        qs = qs.filter(current_status=status)
    if country:
        qs = qs.filter(destination_country_code=country.upper())
    if q:
        qs = qs.filter(client__full_name__icontains=q) | qs.filter(case_code__icontains=q)

    return render(request, "staff/case_list.html", {"cases": qs, "CaseStatus": CaseStatus})


@login_required
def staff_case_detail(request, case_id: int):
    case = (
        Case.objects
        .select_related("client", "program", "branch")
        .filter(id=case_id)
        .first()
    )
    if not case:
        messages.error(request, "Case not found.")
        return redirect("staff_case_list")

    timeline = StatusHistory.objects.filter(case=case).order_by("-changed_at")[:50]
    return render(request, "staff/case_detail.html", {"case": case, "timeline": timeline, "CaseStatus": CaseStatus})


@login_required
def staff_case_update(request, case_id: int):
    case = Case.objects.select_related("client").filter(id=case_id).first()
    if not case:
        messages.error(request, "Case not found.")
        return redirect("staff_case_list")

    if request.method == "POST":
        new_status = request.POST.get("current_status")
        next_action = request.POST.get("next_action", "").strip()
        notes = request.POST.get("notes", "").strip()

        if new_status not in CaseStatus.values:
            messages.error(request, "Invalid status selected.")
            return redirect("staff_case_detail", case_id=case.id)

        case.current_status = new_status
        case.next_action = next_action
        case.notes = notes
        case.assigned_officer = request.user  # record who updated
        case.save()  # triggers Phase 2 signals + message logs

        messages.success(request, "Case updated and client notified (demo sender).")
        return redirect("staff_case_detail", case_id=case.id)

    return render(request, "staff/case_update.html", {"case": case, "CaseStatus": CaseStatus})

@login_required
def client_list(request):
    q = request.GET.get("q", "").strip()
    qs = Client.objects.select_related("organization").order_by("-created_at")
    if q:
        qs = qs.filter(full_name__icontains=q) | qs.filter(client_code__icontains=q) | qs.filter(phone_e164__icontains=q)
    return render(request, "staff/clients_list.html", {"clients": qs})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientCreateForm(request.POST)
        if form.is_valid():
            org = form.cleaned_data["organization"]
            client = create_client_with_code(
                organization=org,
                full_name=form.cleaned_data["full_name"],
                phone_e164=form.cleaned_data["phone_e164"],
                email=form.cleaned_data.get("email"),
                timezone=form.cleaned_data["timezone"],
                preferred_language=form.cleaned_data["preferred_language"],
                source=form.cleaned_data.get("source"),
            )
            messages.success(request, f"Client created: {client.client_code}")
            return redirect("staff_client_detail", client_id=client.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientCreateForm()

    return render(request, "staff/client_create.html", {"form": form})


@login_required
def client_detail(request, client_id: int):
    client = Client.objects.select_related("organization").filter(id=client_id).first()
    if not client:
        messages.error(request, "Client not found.")
        return redirect("staff_client_list")

    cases = Case.objects.filter(client=client).select_related("program", "branch").order_by("-updated_at")
    return render(request, "staff/client_detail.html", {"client": client, "cases": cases})


@login_required
def case_create_for_client(request, client_id: int):
    client = Client.objects.select_related("organization").filter(id=client_id).first()
    if not client:
        messages.error(request, "Client not found.")
        return redirect("staff_client_list")

    if request.method == "POST":
        form = CaseCreateForm(request.POST)
        if form.is_valid():
            branch = form.cleaned_data.get("branch")
            program = form.cleaned_data.get("program")

            officer_id = form.cleaned_data.get("assigned_officer_id")
            officer = User.objects.filter(id=officer_id).first() if officer_id else None

            case = create_case_with_code(
                organization=client.organization,
                branch=branch,
                program=program,
                client=client,
                destination_country_code=form.cleaned_data["destination_country_code"],
                application_type=form.cleaned_data["application_type"],
                assigned_officer=officer or request.user,
            )
            messages.success(request, f"Case created: {case.case_code}")
            return redirect("staff_case_detail", case_id=case.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CaseCreateForm()

    return render(request, "staff/case_create.html", {"form": form, "client": client})