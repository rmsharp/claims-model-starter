"""Parse-level validation of generated SQL with ``sqlparse``.

``sqlparse`` is intentionally forgiving — it tokenises almost any string
without raising. We therefore reject only the clear-cut cases that indicate
the LLM returned nothing usable: empty/whitespace strings, statements whose
type ``sqlparse`` cannot classify, or input that ``sqlparse.parse`` refuses.
Stricter semantic validation (column existence, type compatibility) requires
a live database and is the job of the EXECUTE_QC stage.
"""

from __future__ import annotations

import sqlparse


def validate_sql(sql: str) -> tuple[bool, str]:
    """Return ``(is_valid, error_message)`` for a candidate SQL string."""
    if not sql or not sql.strip():
        return False, "empty SQL"
    try:
        parsed = sqlparse.parse(sql)
    except Exception as e:  # pragma: no cover - sqlparse rarely raises
        return False, f"sqlparse raised: {e}"
    if not parsed:
        return False, "sqlparse returned no statements"
    stmt_type = parsed[0].get_type()
    if stmt_type == "UNKNOWN":
        return False, f"unknown SQL statement type for input: {sql[:80]!r}"
    return True, ""
