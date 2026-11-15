
from django.urls import path
from . import views

urlpatterns = [

    # Home
    path("", views.home, name="home"),

    # Authentication
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Student Profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Team Formation
    path("teams/", views.team_list, name="team_list"),
    path("teams/create/", views.create_team, name="create_team"),
    path("teams/my-team/", views.my_team, name="my_team"),

    path(
        "teams/<int:team_id>/",
        views.team_detail,
        name="team_detail"
    ),

    path(
        "teams/<int:team_id>/join/",
        views.join_team,
        name="join_team"
    ),

    path(
        "teams/<int:team_id>/requests/<int:request_id>/<str:action>/",
        views.handle_join_request,
        name="handle_join_request"
    ),

]
