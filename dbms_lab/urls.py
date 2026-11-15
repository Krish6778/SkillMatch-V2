
from django.urls import path
from . import views

app_name = "dbms_lab"

urlpatterns = [
    path("", views.dbms_lab_home, name="home"),
]
