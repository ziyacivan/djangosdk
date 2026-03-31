from django.urls import path, include

urlpatterns = [
    path("", include("docs_qa.urls")),
]
