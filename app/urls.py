# app/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("menu.urls")),
    # Тестовая страница (опционально)
    path("", TemplateView.as_view(template_name="menu/show_menu.html")),
]
