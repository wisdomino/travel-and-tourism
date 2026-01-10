from django.urls import path
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda r: redirect("/portal/")),
]
