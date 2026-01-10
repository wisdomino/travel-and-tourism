from django.urls import path
from . import portal_views

app_name = "portal"

urlpatterns = [
    path("", portal_views.portal_start, name="portal_start"),
    path("verify/", portal_views.portal_verify, name="portal_verify"),
    path("status/", portal_views.portal_status, name="portal_status"),
    path("case/<str:case_code>/", portal_views.portal_case_detail, name="case_detail"),
    path("logout/", portal_views.portal_logout, name="portal_logout"),
]
