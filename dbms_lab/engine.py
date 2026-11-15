
import re

from django.db import connections


DB_ALIAS = "dbms_readonly"
MAX_ROWS = 200
MAX_QUERY_LENGTH = 5000


def get_db_connection():
    return connections[DB_ALIAS]


def get_tables():
    """Return tables visible to the read-only MySQL account."""
    db = get_db_connection()

    with db.cursor() as cursor:
        tables = db.introspection.table_names(cursor)

    return sorted(tables)


def get_table_structure(table_name):
    """Return column information and primary/foreign key details."""
    db = get_db_connection()
    tables = get_tables()

    if table_name not in tables:
        raise ValueError("This table is not available.")

    with db.cursor() as cursor:
        description = db.introspection.get_table_description(
            cursor, table_name
        )

        constraints = db.introspection.get_constraints(
            cursor, table_name
        )

    primary_keys = set()
    foreign_keys = {}

    for constraint in constraints.values():
        columns = constraint.get("columns") or []

        if constraint.get("primary_key"):
            primary_keys.update(columns)

        if constraint.get("foreign_key") and columns:
            foreign_keys[columns[0]] = constraint["foreign_key"]

    result = []

    for field in description:
        try:
            data_type = db.introspection.get_field_type(
                field.type_code, field
            )
        except Exception:
            data_type = str(field.type_code)

        result.append({
            "name": field.name,
            "type": data_type,
            "nullable": field.null_ok,
            "primary_key": field.name in primary_keys,
            "foreign_key": foreign_keys.get(field.name),
        })

    return result


def get_table_records(table_name):
    """Fetch a limited number of actual records from a permitted table."""
    db = get_db_connection()

    if table_name not in get_tables():
        raise ValueError("This table is not available.")

    quoted_table = db.ops.quote_name(table_name)

    with db.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM {quoted_table} LIMIT %s",
            [MAX_ROWS]
        )

        columns = [column[0] for column in cursor.description]
        records = cursor.fetchall()

    return columns, records


def validate_readonly_query(query):
    """Allow one read-only SELECT statement."""
    query = query.strip()

    if not query:
        raise ValueError("Please enter an SQL query.")

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Query is too long. Maximum length is 5000 characters.")

    # Reject comments to prevent attempts to hide prohibited SQL.
    if any(marker in query for marker in ("--", "/*", "*/", "#")):
        raise ValueError("SQL comments are not permitted in the lab.")

    # Permit one optional trailing semicolon, but no multiple statements.
    query = query.rstrip()

    if query.endswith(";"):
        query = query[:-1].rstrip()

    if ";" in query:
        raise ValueError("Only one SQL statement can be executed at a time.")

    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        raise ValueError("Only SELECT queries and SELECT-based CTEs are permitted.")

    blocked_keywords = (
        r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|TRUNCATE|"
        r"CREATE|RENAME|GRANT|REVOKE|CALL|DO|HANDLER|LOAD|"
        r"OUTFILE|DUMPFILE|INTO)\b"
    )

    if re.search(blocked_keywords, query, re.IGNORECASE):
        raise ValueError("This query contains a prohibited SQL operation.")

    blocked_patterns = (
        r"\bFOR\s+UPDATE\b",
        r"\bLOCK\s+IN\s+SHARE\s+MODE\b",
        r"\bSLEEP\s*\(",
        r"\bBENCHMARK\s*\(",
        r"\bLOAD_FILE\s*\(",
        r"\bGET_LOCK\s*\(",
        r"\bRELEASE_LOCK\s*\(",
    )

    for pattern in blocked_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError("This SQL operation is not permitted.")

    return query


def execute_readonly_query(query):
    """Execute a permitted query and return at most 200 records."""
    query = validate_readonly_query(query)
    db = get_db_connection()

    with db.cursor() as cursor:
        cursor.execute(query)

        if cursor.description is None:
            raise ValueError("The query did not return a result set.")

        columns = [column[0] for column in cursor.description]

        records = cursor.fetchmany(MAX_ROWS + 1)

    truncated = len(records) > MAX_ROWS
    records = records[:MAX_ROWS]

    return {
        "columns": columns,
        "rows": records,
        "truncated": truncated,
        "row_count": len(records),
    }
