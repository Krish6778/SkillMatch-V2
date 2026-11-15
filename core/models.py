
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


# =====================================================
# CUSTOM USER MODEL
# =====================================================

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


# =====================================================
# SKILLS
# =====================================================

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =====================================================
# STUDENT PROFILE
# =====================================================

class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    full_name = models.CharField(max_length=150, blank=True)
    introduction = models.TextField(blank=True, max_length=1000)
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="students"
    )
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# =====================================================
# TEAM
# =====================================================

class Team(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    project_title = models.CharField(max_length=200, blank=True)

    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="led_teams"
    )

    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="teams"
    )

    max_members = models.PositiveSmallIntegerField(
        default=4,
        validators=[
            MinValueValidator(2),
            MaxValueValidator(10)
        ]
    )

    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_members__gte=2),
                name="team_minimum_two_members"
            ),
            models.CheckConstraint(
                condition=models.Q(max_members__lte=10),
                name="team_maximum_ten_members"
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    @property
    def available_slots(self):
        return max(0, self.max_members - self.member_count)

    @property
    def is_full(self):
        return self.member_count >= self.max_members


# =====================================================
# TEAM MEMBERSHIP
# =====================================================

class TeamMembership(models.Model):
    LEADER = "LEADER"
    MEMBER = "MEMBER"

    ROLE_CHOICES = [
        (LEADER, "Leader"),
        (MEMBER, "Member"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_membership"
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=MEMBER
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_membership"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


# =====================================================
# TEAM JOIN REQUEST
# =====================================================

class JoinRequest(models.Model):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
    ]

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="join_requests"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="join_requests"
    )

    message = models.TextField(blank=True, max_length=500)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_join_request"
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.team.name} ({self.status})"
