
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User, StudentProfile, Team, JoinRequest


# ==========================================
# STUDENT REGISTRATION
# ==========================================

class RegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email"
        })
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "First name"
        })
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Last name"
        })
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["password1"].widget.attrs["placeholder"] = "Create a password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm your password"


# ==========================================
# STUDENT LOGIN
# ==========================================

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your username"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password"
        })
    )


# ==========================================
# STUDENT PROFILE
# ==========================================

class StudentProfileForm(forms.ModelForm):

    class Meta:
        model = StudentProfile

        fields = [
            "full_name",
            "introduction",
            "skills",
            "github_url",
            "linkedin_url"
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your full name"
            }),

            "introduction": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Tell others about yourself"
            }),

            "skills": forms.CheckboxSelectMultiple(),

            "github_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://github.com/username"
            }),

            "linkedin_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://www.linkedin.com/in/username"
            })
        }


# ==========================================
# CREATE TEAM
# ==========================================

class TeamCreateForm(forms.ModelForm):

    class Meta:
        model = Team

        fields = [
            "name",
            "project_title",
            "description",
            "required_skills",
            "max_members"
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your team name"
            }),

            "project_title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your project title"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe your project and team goals"
            }),

            "required_skills": forms.CheckboxSelectMultiple(),

            "max_members": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 2,
                "max": 10
            })
        }

        labels = {
            "name": "Team Name",
            "project_title": "Project Title",
            "description": "Project Description",
            "required_skills": "Required Skills",
            "max_members": "Maximum Team Members"
        }


# ==========================================
# JOIN TEAM REQUEST
# ==========================================

class JoinRequestForm(forms.ModelForm):

    class Meta:
        model = JoinRequest

        fields = ["message"]

        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Explain why you want to join this team"
            })
        }

        labels = {
            "message": "Message to Team Leader"
        }
