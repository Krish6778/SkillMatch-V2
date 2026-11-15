
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q, Count

from .forms import (
    RegistrationForm,
    StudentProfileForm,
    TeamCreateForm,
    JoinRequestForm
)

from .models import (
    User,
    StudentProfile,
    Skill,
    Team,
    TeamMembership,
    JoinRequest
)


# ==========================================
# HOME PAGE
# ==========================================

def home(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "home.html")


# ==========================================
# REGISTRATION
# ==========================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                user = form.save()

                StudentProfile.objects.create(
                    user=user,
                    full_name=f"{user.first_name} {user.last_name}".strip()
                )

            login(request, user)

            messages.success(
                request,
                "Your account has been created successfully!"
            )

            return redirect("dashboard")

    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})


# ==========================================
# LOGIN
# ==========================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.first_name or user.username}!"
            )

            return redirect("dashboard")

    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form})


# ==========================================
# LOGOUT
# ==========================================

@require_POST
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def dashboard(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": (
                f"{request.user.first_name} "
                f"{request.user.last_name}"
            ).strip()
        }
    )

    membership = TeamMembership.objects.filter(
        user=request.user
    ).select_related("team").first()

    return render(
        request,
        "dashboard.html",
        {
            "profile": profile,
            "membership": membership
        }
    )


# ==========================================
# VIEW STUDENT PROFILE
# ==========================================

@login_required
def profile_view(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "profile.html",
        {"profile": profile}
    )


# ==========================================
# EDIT STUDENT PROFILE
# ==========================================

@login_required
def edit_profile(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = StudentProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your profile has been updated successfully!"
            )

            return redirect("profile")

    else:

        form = StudentProfileForm(instance=profile)

    return render(
        request,
        "edit_profile.html",
        {"form": form}
    )


# ==========================================
# DISCOVER TEAMS
# ==========================================

@login_required
def team_list(request):

    search_query = request.GET.get("q", "").strip()
    selected_skill = request.GET.get("skill", "").strip()

    teams = Team.objects.annotate(
        total_members=Count("members")
    ).filter(
        is_open=True
    )

    if search_query:

        teams = teams.filter(
            Q(name__icontains=search_query) |
            Q(project_title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if selected_skill:

        if selected_skill.isdigit():

            teams = teams.filter(
                required_skills__id=int(selected_skill)
            )

    teams = teams.distinct().select_related(
        "leader"
    ).prefetch_related(
        "required_skills"
    )

    skills = Skill.objects.all()

    membership = TeamMembership.objects.filter(
        user=request.user
    ).select_related("team").first()

    return render(
        request,
        "team_list.html",
        {
            "teams": teams,
            "skills": skills,
            "search_query": search_query,
            "selected_skill": selected_skill,
            "membership": membership
        }
    )


# ==========================================
# CREATE TEAM
# ==========================================

@login_required
def create_team(request):

    if TeamMembership.objects.filter(user=request.user).exists():

        messages.warning(
            request,
            "You are already a member of a team. Leave your current team before creating another."
        )

        return redirect("my_team")

    if request.method == "POST":

        form = TeamCreateForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    # Lock the user row to prevent simultaneous team creation.
                    User.objects.select_for_update().get(
                        pk=request.user.pk
                    )

                    if TeamMembership.objects.filter(
                        user=request.user
                    ).exists():

                        messages.error(
                            request,
                            "You already belong to a team."
                        )

                        return redirect("my_team")

                    team = form.save(commit=False)

                    team.leader = request.user
                    team.save()

                    form.save_m2m()

                    # Leader automatically becomes the first member.
                    TeamMembership.objects.create(
                        user=request.user,
                        team=team,
                        role=TeamMembership.LEADER
                    )

                messages.success(
                    request,
                    "Your team has been created successfully!"
                )

                return redirect("my_team")

            except Exception:
                messages.error(
                    request,
                    "Something went wrong while creating the team."
                )

    else:

        form = TeamCreateForm()

    return render(
        request,
        "create_team.html",
        {"form": form}
    )


# ==========================================
# TEAM DETAILS
# ==========================================

@login_required
def team_detail(request, team_id):

    team = get_object_or_404(
        Team.objects.select_related("leader").prefetch_related(
            "required_skills"
        ),
        pk=team_id
    )

    members = TeamMembership.objects.filter(
        team=team
    ).select_related("user")

    membership = TeamMembership.objects.filter(
        user=request.user
    ).select_related("team").first()

    user_request = JoinRequest.objects.filter(
        team=team,
        user=request.user
    ).first()

    pending_requests = []

    if team.leader_id == request.user.id:

        pending_requests = JoinRequest.objects.filter(
            team=team,
            status=JoinRequest.PENDING
        ).select_related(
            "user"
        )

    return render(
        request,
        "team_detail.html",
        {
            "team": team,
            "members": members,
            "membership": membership,
            "user_request": user_request,
            "pending_requests": pending_requests
        }
    )


# ==========================================
# SEND JOIN REQUEST
# ==========================================

@login_required
@require_POST
def join_team(request, team_id):

    with transaction.atomic():

        User.objects.select_for_update().get(
            pk=request.user.pk
        )

        if TeamMembership.objects.filter(
            user=request.user
        ).exists():

            messages.error(
                request,
                "You are already a member of a team."
            )

            return redirect("my_team")

        team = get_object_or_404(
            Team.objects.select_for_update(),
            pk=team_id
        )

        member_count = TeamMembership.objects.filter(
            team=team
        ).count()

        if not team.is_open or member_count >= team.max_members:

            messages.error(
                request,
                "This team is no longer accepting applications."
            )

            return redirect("team_detail", team_id=team.id)

        if team.leader_id == request.user.id:

            messages.error(
                request,
                "You cannot apply to your own team."
            )

            return redirect("team_detail", team_id=team.id)

        form = JoinRequestForm(request.POST)

        if not form.is_valid():

            messages.error(
                request,
                "Please correct the join request form."
            )

            return redirect("team_detail", team_id=team.id)

        existing_request = JoinRequest.objects.filter(
            team=team,
            user=request.user
        ).first()

        if existing_request:

            if existing_request.status == JoinRequest.PENDING:

                messages.warning(
                    request,
                    "You already have a pending request for this team."
                )

                return redirect("team_detail", team_id=team.id)

            if existing_request.status == JoinRequest.ACCEPTED:

                messages.warning(
                    request,
                    "Your request has already been accepted."
                )

                return redirect("team_detail", team_id=team.id)

            # Reuse the rejected request rather than creating
            # a duplicate row for the same student and team.
            existing_request.message = form.cleaned_data["message"]
            existing_request.status = JoinRequest.PENDING
            existing_request.save()

        else:

            join_request = form.save(commit=False)

            join_request.team = team
            join_request.user = request.user
            join_request.save()

    messages.success(
        request,
        "Your join request has been sent to the team leader!"
    )

    return redirect("team_detail", team_id=team.id)


# ==========================================
# ACCEPT OR REJECT JOIN REQUEST
# ==========================================

@login_required
@require_POST
def handle_join_request(request, team_id, request_id, action):

    if action not in ["accept", "reject"]:

        messages.error(request, "Invalid action.")

        return redirect("team_detail", team_id=team_id)

    with transaction.atomic():

        team = get_object_or_404(
            Team.objects.select_for_update(),
            pk=team_id
        )

        if team.leader_id != request.user.id:

            messages.error(
                request,
                "Only the team leader can manage join requests."
            )

            return redirect("team_detail", team_id=team.id)

        join_request = get_object_or_404(
            JoinRequest.objects.select_for_update(),
            pk=request_id,
            team=team
        )

        if join_request.status != JoinRequest.PENDING:

            messages.warning(
                request,
                "This request has already been processed."
            )

            return redirect("team_detail", team_id=team.id)

        if action == "reject":

            join_request.status = JoinRequest.REJECTED
            join_request.save()

            messages.success(
                request,
                "The join request has been rejected."
            )

        else:

            # Lock the applicant's user row. This helps prevent
            # simultaneous acceptance into two different teams.
            User.objects.select_for_update().get(
                pk=join_request.user_id
            )

            if TeamMembership.objects.filter(
                user=join_request.user
            ).exists():

                join_request.status = JoinRequest.REJECTED
                join_request.save()

                messages.warning(
                    request,
                    "This student has already joined another team."
                )

                return redirect("team_detail", team_id=team.id)

            member_count = TeamMembership.objects.filter(
                team=team
            ).count()

            if member_count >= team.max_members:

                team.is_open = False
                team.save(update_fields=["is_open"])

                messages.error(
                    request,
                    "The team is already full."
                )

                return redirect("team_detail", team_id=team.id)

            TeamMembership.objects.create(
                user=join_request.user,
                team=team,
                role=TeamMembership.MEMBER
            )

            join_request.status = JoinRequest.ACCEPTED
            join_request.save()

            if member_count + 1 >= team.max_members:

                team.is_open = False
                team.save(update_fields=["is_open"])

                # Close other outstanding applications.
                JoinRequest.objects.filter(
                    team=team,
                    status=JoinRequest.PENDING
                ).exclude(
                    pk=join_request.pk
                ).update(
                    status=JoinRequest.REJECTED
                )

            messages.success(
                request,
                f"{join_request.user.username} has been added to your team!"
            )

    return redirect("team_detail", team_id=team_id)


# ==========================================
# MY TEAM
# ==========================================

@login_required
def my_team(request):

    membership = TeamMembership.objects.filter(
        user=request.user
    ).select_related(
        "team",
        "team__leader"
    ).first()

    if not membership:

        return render(
            request,
            "my_team.html",
            {"membership": None}
        )

    team = membership.team

    members = TeamMembership.objects.filter(
        team=team
    ).select_related("user")

    pending_requests_count = 0

    if membership.role == TeamMembership.LEADER:

        pending_requests_count = JoinRequest.objects.filter(
            team=team,
            status=JoinRequest.PENDING
        ).count()

    return render(
        request,
        "my_team.html",
        {
            "membership": membership,
            "team": team,
            "members": members,
            "pending_requests_count": pending_requests_count
        }
    )
