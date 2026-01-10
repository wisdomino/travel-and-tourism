from django.urls import path
from . import portal_views

urlpatterns = [
    path("", portal_views.portal_start, name="portal_start"),
    path("verify/", portal_views.portal_verify, name="portal_verify"),
    path("status/", portal_views.portal_status, name="portal_status"),
    path("logout/", portal_views.portal_logout, name="portal_logout"),
]
