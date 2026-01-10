from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Case


@login_required
def staff_home(request):
    return render(request, "staff/home.html")


@login_required
def case_list(request):
    qs = Case.objects.select_related("client", "program", "branch").order_by("-updated_at")

    status = request.GET.get("status")
    country = request.GET.get("country")

    if status:
        qs = qs.filter(current_status=status)
    if country:
        qs = qs.filter(destination_country_code=country.upper())

    return render(request, "staff/case_list.html", {"cases": qs})
