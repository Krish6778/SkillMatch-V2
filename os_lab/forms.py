
import json
from django import forms


class CPUForm(forms.Form):
    ALGORITHMS = [
        ("FCFS", "First Come First Serve (FCFS)"),
        ("SJF", "Shortest Job First (Non-preemptive)"),
        ("PRIORITY", "Priority Scheduling (Non-preemptive)"),
        ("RR", "Round Robin"),
    ]

    algorithm = forms.ChoiceField(
        choices=ALGORITHMS,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    processes = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "P1,0,5,2\nP2,1,3,1\nP3,2,8,3"
        }),
        help_text="One process per line: PID, arrival time, burst time, priority."
    )

    quantum = forms.IntegerField(
        required=False,
        min_value=1,
        initial=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )



class BankerForm(forms.Form):
    configuration = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 9,
            "placeholder": '{"available":[3,3,2],"allocation":[[0,1,0]],"maximum":[[7,5,3]]}'
        }),
        help_text="Enter JSON containing available, allocation and maximum arrays."
    )

    def clean_configuration(self):
        raw = self.cleaned_data["configuration"]

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise forms.ValidationError("Enter valid JSON.")

        if not isinstance(parsed, dict):
            raise forms.ValidationError("The JSON value must be an object.")

        required = {"available", "allocation", "maximum"}

        if not required.issubset(parsed):
            raise forms.ValidationError(
                "JSON must contain available, allocation and maximum."
            )

        return parsed


class ProducerConsumerForm(forms.Form):
    capacity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=3,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    operations = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "P:10, P:20, C, P:30, C"
        }),
        help_text="Use P:item to produce and C to consume. Separate operations with commas."
    )

    def clean_operations(self):
        raw = self.cleaned_data["operations"]
        operations = [item.strip() for item in raw.split(",") if item.strip()]

        if not operations:
            raise forms.ValidationError("Enter at least one operation.")

        if len(operations) > 30:
            raise forms.ValidationError("A maximum of 30 operations is allowed.")

        return operations
