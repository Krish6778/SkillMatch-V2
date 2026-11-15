
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CPUForm, BankerForm, ProducerConsumerForm
from .algorithms import (
    parse_processes,
    cpu_scheduling,
    banker_algorithm,
    producer_consumer_simulation,
)


@login_required
def os_lab_home(request):
    context = {
        "cpu_form": CPUForm(),
        "banker_form": BankerForm(),
        "pc_form": ProducerConsumerForm(),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "cpu":
            form = CPUForm(request.POST)
            context["cpu_form"] = form

            if form.is_valid():
                try:
                    processes = parse_processes(form.cleaned_data["processes"])
                    context["cpu_result"] = cpu_scheduling(
                        processes,
                        form.cleaned_data["algorithm"],
                        form.cleaned_data["quantum"] or 2,
                    )
                except ValueError as error:
                    form.add_error(None, str(error))

        elif action == "banker":
            form = BankerForm(request.POST)
            context["banker_form"] = form

            if form.is_valid():
                try:
                    context["banker_result"] = banker_algorithm(
                        form.cleaned_data["configuration"]
                    )
                except (ValueError, KeyError, TypeError) as error:
                    form.add_error(None, str(error))

        elif action == "producer_consumer":
            form = ProducerConsumerForm(request.POST)
            context["pc_form"] = form

            if form.is_valid():
                try:
                    context["pc_result"] = producer_consumer_simulation(
                        form.cleaned_data["capacity"],
                        form.cleaned_data["operations"],
                    )
                except ValueError as error:
                    form.add_error(None, str(error))

    return render(request, "os_lab/index.html", context)
