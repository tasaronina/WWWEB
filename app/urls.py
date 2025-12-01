from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from menu.views import ShowMenuView 

urlpatterns = [
    path("", ShowMenuView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("menu.urls")), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
