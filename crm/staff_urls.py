from django.urls import path
from . import staff_views

urlpatterns = [
    path("", staff_views.staff_home, name="staff_home"),
    # cases
    path("cases/", staff_views.case_list, name="staff_case_list"),
    path("cases/<int:case_id>/", staff_views.staff_case_detail, name="staff_case_detail"),
    path("cases/<int:case_id>/update/", staff_views.staff_case_update, name="staff_case_update"),
    # clients
    path("clients/", staff_views.client_list, name="staff_client_list"),
    path("clients/new/", staff_views.client_create, name="staff_client_create"),
    path("clients/<int:client_id>/", staff_views.client_detail, name="staff_client_detail"),
    path("clients/<int:client_id>/cases/new/", staff_views.case_create_for_client, name="staff_case_create_for_client"),
]