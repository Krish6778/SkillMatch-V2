
from django.urls import path
from . import views

app_name = "os_lab"

urlpatterns = [
    path("", views.os_lab_home, name="home"),
]
