from django.urls import path
from . import staff_views

urlpatterns = [
    path("", staff_views.staff_home, name="staff_home"),
    path("cases/", staff_views.case_list, name="staff_case_list"),
]
