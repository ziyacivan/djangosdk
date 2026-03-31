from django.urls import path
from . import views

urlpatterns = [
    path("extract/", views.extract, name="extract"),
    path("sample/", views.sample, name="sample"),
]
