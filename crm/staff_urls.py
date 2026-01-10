from django.urls import path
from . import staff_views

urlpatterns = [
    path("", staff_views.staff_home, name="staff_home"),
    path("cases/", staff_views.case_list, name="staff_case_list"),
    path("cases/<int:case_id>/", staff_views.staff_case_detail, name="staff_case_detail"),
    path("cases/<int:case_id>/update/", staff_views.staff_case_update, name="staff_case_update"),
]
