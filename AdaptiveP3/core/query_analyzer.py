"""
AP3 — Query Analyzer
=====================
Parses raw SQL with *sqlparse*, extracts metadata (tables, aggregates,
WHERE clauses), computes a heuristic sensitivity score, and detects
basic SQL injection patterns.
"""

import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Function, Comparison, Parenthesis
from sqlparse.tokens import Keyword, DML


# Aggregate functions that require differential-privacy noise
AGGREGATE_FUNCTIONS = {"count", "sum", "avg", "min", "max"}


# ── Data class for analysis results ─────────────────────────────────

class QueryAnalysis:
    """Container for the results of analysing a single SQL statement."""

    def __init__(
        self,
        raw_sql: str,
        is_select: bool,
        is_aggregate: bool,
        tables: list[str],
        columns: list[str],
        aggregates: list[str],
        has_where: bool,
        sensitivity: float,
        is_dangerous: bool,
        danger_reason: str | None = None,
        predicates: list[str] | None = None,
    ):
        self.raw_sql = raw_sql
        self.is_select = is_select
        self.is_aggregate = is_aggregate
        self.tables = tables
        self.columns = columns
        self.aggregates = aggregates
        self.has_where = has_where
        self.sensitivity = sensitivity
        self.is_dangerous = is_dangerous
        self.danger_reason = danger_reason
        self.predicates = predicates or []



# ── Internal helpers ─────────────────────────────────────────────────

def _extract_tables(parsed) -> list[str]:
    """Walk tokens to pull out table names after FROM / JOIN."""
    tables: list[str] = []
    from_seen = False
    for token in parsed.tokens:
        if token.ttype is Keyword and token.value.upper() in ("FROM", "JOIN"):
            from_seen = True
            continue
        if from_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(identifier.get_name())
                from_seen = False
            elif isinstance(token, Identifier):
                tables.append(token.get_name())
                from_seen = False
    return tables


def _extract_aggregates(parsed) -> list[str]:
    """Return aggregate function names (COUNT, SUM, …) found in the query."""
    aggregates: list[str] = []

    def _walk(token_list):
        for token in token_list.tokens:
            if isinstance(token, Function):
                func_name = token.get_name().lower()
                if func_name in AGGREGATE_FUNCTIONS:
                    aggregates.append(func_name)
            if hasattr(token, "tokens"):
                _walk(token)

    _walk(parsed)
    return aggregates


def _detect_sql_injection(raw_sql: str) -> str | None:
    """
    Basic heuristic injection detection.
    Returns a reason string if the query looks dangerous, else None.
    """
    lower = raw_sql.lower()

    # Piggy-back attack: multiple statements
    statements = sqlparse.split(raw_sql)
    if len(statements) > 1:
        return "Multiple SQL statements detected (possible piggyback injection)."

    # Common injection fingerprints
    injection_patterns = [
        "' or '1'='1",
        "'; drop table",
        "'; --",
        "union select",
        "exec xp_",
        "exec sp_",
        "1=1",
        "' or ''='",
    ]
    for pattern in injection_patterns:
        if pattern in lower:
            return f"SQL injection pattern detected: '{pattern}'"

    return None


def _compute_sensitivity(aggregates: list[str], has_where: bool) -> float:
    """
    Heuristic sensitivity score (Δf).

    * Aggregates that expose ranges (SUM, AVG) are weighted higher.
    * A WHERE clause that narrows the population increases inference risk.
    """
    base = 1.0
    agg_weights = {
        "count": 1.0,
        "sum": 2.0,
        "avg": 2.5,
        "min": 1.5,
        "max": 1.5,
    }
    for agg in aggregates:
        base += agg_weights.get(agg, 1.0)

    if has_where:
        base *= 1.5   # narrowing a population raises risk

    return round(base, 4)


def _extract_predicates(parsed) -> list[str]:
    """Extract normalized predicates from WHERE clauses (e.g. department='engineering')."""
    predicates: list[str] = []
    for token in parsed.tokens:
        if isinstance(token, Where):
            for subtoken in token.tokens:
                if isinstance(subtoken, Comparison):
                    clean = "".join(subtoken.value.split()).lower()
                    predicates.append(clean)
            if not predicates:
                val = re.sub(r"^\s*WHERE\s+", "", token.value, flags=re.IGNORECASE)
                parts = re.split(r"\s+(?:AND|OR)\s+", val, flags=re.IGNORECASE)
                for p in parts:
                    clean = "".join(p.split()).lower()
                    if clean:
                        predicates.append(clean)
    return predicates


def _extract_columns(parsed, tables: list[str]) -> list[str]:
    """Extract column names referenced in SELECT, aggregates, and WHERE."""
    cols: set[str] = set()
    table_set = {t.lower() for t in tables}

    for token in parsed.tokens:
        if isinstance(token, Where):
            for st in token.tokens:
                if isinstance(st, Comparison) and st.left:
                    cols.add(str(st.left).strip().lower())
        elif isinstance(token, Function):
            for p in token.tokens:
                if isinstance(p, Parenthesis):
                    val = p.value.strip("() ")
                    for item in val.split(","):
                        item = item.strip().lower()
                        if item and item != "*":
                            cols.add(item)
        elif isinstance(token, IdentifierList):
            for ident in token.get_identifiers():
                if isinstance(ident, Function):
                    for p in ident.tokens:
                        if isinstance(p, Parenthesis):
                            val = p.value.strip("() ")
                            for item in val.split(","):
                                item = item.strip().lower()
                                if item and item != "*":
                                    cols.add(item)
                else:
                    name = ident.get_real_name() or str(ident)
                    cols.add(name.strip().lower())
        elif isinstance(token, Identifier):
            name = token.get_real_name() or str(token)
            cols.add(name.strip().lower())

    cleaned = [c for c in cols if c not in table_set and c not in AGGREGATE_FUNCTIONS]
    return sorted(cleaned)


# ── Public API ───────────────────────────────────────────────────────

def analyze_query(raw_sql: str) -> QueryAnalysis:
    """
    Parse a raw SQL string and return a :class:`QueryAnalysis` containing
    tables, aggregates, sensitivity score, predicates, and injection flags.
    """
    parsed = sqlparse.parse(raw_sql.strip())[0]

    # Statement type
    stmt_type = parsed.get_type()
    is_select = stmt_type == "SELECT" if stmt_type else False

    # Injection check
    danger_reason = _detect_sql_injection(raw_sql)
    is_dangerous = danger_reason is not None

    # Tables
    tables = _extract_tables(parsed)

    # Columns (fine-grained extraction)
    columns = _extract_columns(parsed, tables)

    # Aggregates
    aggregates = _extract_aggregates(parsed)
    is_aggregate = len(aggregates) > 0

    # WHERE present and predicates
    has_where = any(isinstance(token, Where) for token in parsed.tokens)
    predicates = _extract_predicates(parsed)

    # Sensitivity
    sensitivity = _compute_sensitivity(aggregates, has_where)

    return QueryAnalysis(
        raw_sql=raw_sql,
        is_select=is_select,
        is_aggregate=is_aggregate,
        tables=tables,
        columns=columns,
        aggregates=aggregates,
        has_where=has_where,
        sensitivity=sensitivity,
        is_dangerous=is_dangerous,
        danger_reason=danger_reason,
        predicates=predicates,
    )

