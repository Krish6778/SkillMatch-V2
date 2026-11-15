
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
    path("os-lab/", include("os_lab.urls")),
    path("dbms-lab/", include("dbms_lab.urls")),
]
