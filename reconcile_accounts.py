from collections import defaultdict, deque
from datetime import date
from typing import Any, Sequence

DATE_IDX = 0
DEPARTMENT_IDX = 1
AMOUNT_IDX = 2
BENEFICIARY_IDX = 3

FOUND = "FOUND"
MISSING = "MISSING"
DATE_OFFSETS = (-1, 0, 1)


def reconcile_accounts(
    transactions1: Sequence[Sequence[Any]],
    transactions2: Sequence[Sequence[Any]],
) -> tuple[list[list[Any]], list[list[Any]]]:
    """Compare two transaction lists and append FOUND/MISSING to each row.

    A match requires equal department, amount, and beneficiary with dates within ±1 day.
    Each transaction is matched at most once (one-to-one). Inputs are not mutated.

    When multiple candidates satisfy the date constraint, the one with the earliest
    date (offset -1 before 0 before +1) is preferred.

    Args:
        transactions1: Reference rows (columns: date, department, amount, beneficiary).
        transactions2: Candidate rows with the same column layout.

    Returns:
        Tuple (out1, out2) — copies of each list with a status string appended.

    Raises:
        ValueError: If any row has fewer than 4 columns, or if a date field cannot
            be parsed as a valid ISO-8601 date (YYYY-MM-DD).

    Notes:
        - **String-literal comparison**: department, amount, and beneficiary are compared
          as raw strings. ``"16.00"`` and ``"16.0"`` represent the same numeric value but
          will *not* match. Callers must normalise formatting before reconciliation if
          data originates from systems with different conventions.
        - **Case-sensitive comparison**: ``"Tecnologia"`` and ``"tecnologia"`` are distinct
          values and will *not* match. Normalise case upstream if needed.
        - **Extra columns**: rows with more than 4 columns are accepted; only the first
          four are used for matching. The extra columns are preserved in the output as-is.
    """
    for i, row in enumerate(transactions1):
        _validate_row(row, source=1, idx=i)
    for i, row in enumerate(transactions2):
        _validate_row(row, source=2, idx=i)

    pool: defaultdict[tuple[Any, int], deque[int]] = defaultdict(deque)

    for i, row in enumerate(transactions2):
        pool[(_key(row), _day(row))].append(i)

    statuses1 = [MISSING] * len(transactions1)
    statuses2 = [MISSING] * len(transactions2)

    for i, row in enumerate(transactions1):
        key = _key(row)
        tx_day = _day(row)

        for offset in DATE_OFFSETS:
            bucket = pool.get((key, tx_day + offset))
            if bucket:
                statuses1[i] = FOUND
                statuses2[bucket.popleft()] = FOUND
                break

    out1 = [list(row) + [status] for row, status in zip(transactions1, statuses1)]
    out2 = [list(row) + [status] for row, status in zip(transactions2, statuses2)]

    return out1, out2


def _validate_row(row: Sequence[Any], source: int, idx: int) -> None:
    """Raise ValueError if *row* does not satisfy the minimum column schema.

    Args:
        row: The row to validate.
        source: Which input list the row belongs to (1 or 2), used in the error message.
        idx: Zero-based position of the row within its list, used in the error message.

    Raises:
        ValueError: If ``len(row) < 4``.
    """
    if len(row) < 4:
        raise ValueError(
            f"transactions{source}[{idx}] must have at least 4 columns, "
            f"got {len(row)}: {row!r}"
        )


def _key(row: Sequence[Any]) -> tuple[Any, Any, Any]:
    """Return a (department, amount, beneficiary) key for bucketed lookups.

    Comparison is string-literal: values must match exactly, including formatting
    (e.g. ``"16.00"`` ≠ ``"16.0"``) and case (e.g. ``"AWS"`` ≠ ``"aws"``).
    """
    return (
        row[DEPARTMENT_IDX],
        row[AMOUNT_IDX],
        row[BENEFICIARY_IDX],
    )


def _day(row: Sequence[Any]) -> int:
    """Return the ordinal integer for the row's ISO-8601 date field.

    Raises:
        ValueError: If the date field cannot be parsed as a valid YYYY-MM-DD string.
    """
    raw = row[DATE_IDX]
    try:
        return date.fromisoformat(str(raw)).toordinal()
    except ValueError as exc:
        raise ValueError(
            f"Invalid ISO-8601 date {raw!r} in row {row!r}: {exc}"
        ) from exc