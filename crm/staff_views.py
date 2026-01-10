from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Case, CaseStatus, StatusHistory


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

