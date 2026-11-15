
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import SQLPlaygroundForm
from .engine import (
    get_tables,
    get_table_structure,
    get_table_records,
    execute_readonly_query,
)


@login_required
def dbms_lab_home(request):
    tables = []
    selected_table = None
    table_structure = []
    table_columns = []
    table_records = []

    query_form = SQLPlaygroundForm()
    query_result = None
    query_error = None

    try:
        tables = get_tables()
    except Exception as error:
        query_error = f"Could not connect to the read-only database: {error}"

    if request.method == "POST":
        query_form = SQLPlaygroundForm(request.POST)

        if query_form.is_valid():
            try:
                query_result = execute_readonly_query(
                    query_form.cleaned_data["query"]
                )
            except Exception as error:
                query_error = str(error)

    selected_table_name = request.GET.get("table", "").strip()

    if selected_table_name:
        try:
            selected_table = selected_table_name
            table_structure = get_table_structure(selected_table_name)

            table_columns, table_records = get_table_records(
                selected_table_name
            )

        except Exception as error:
            selected_table = None
            query_error = str(error)
    print("DBMS TABLES SENT TO TEMPLATE:", tables)
    context = {
        "tables": tables,
        "selected_table": selected_table,
        "table_structure": table_structure,
        "table_columns": table_columns,
        "table_records": table_records,
        "query_form": query_form,
        "query_result": query_result,
        "query_error": query_error,
    }

    return render(request, "dbms_lab/index.html", context)
