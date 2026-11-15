
from django import forms


class SQLPlaygroundForm(forms.Form):
    query = forms.CharField(
        label="SQL Query",
        widget=forms.Textarea(attrs={
            "class": "form-control dbms-query-input",
            "rows": 7,
            "placeholder": "SELECT * FROM core_team LIMIT 20;",
            "spellcheck": "false",
        }),
        max_length=5000,
    )
