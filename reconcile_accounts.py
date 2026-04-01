from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from typing import DefaultDict, Deque, Optional, Sequence


Transaction = Sequence[str]
TransactionKey = tuple[str, str, str]


def reconcile_accounts(
    transactions1: Sequence[Transaction],
    transactions2: Sequence[Transaction],
) -> tuple[list[list[str]], list[list[str]]]:
    """Reconcile two lists of financial transactions.

    Two transactions match when department, amount and beneficiary are equal and
    the dates differ by at most one day. Duplicates are allowed, but each row can
    only be matched once.
    """

    transactions2_by_key: DefaultDict[
        TransactionKey, DefaultDict[int, Deque[int]]
    ] = defaultdict(lambda: defaultdict(deque))
    statuses1 = ["MISSING"] * len(transactions1)
    statuses2 = ["MISSING"] * len(transactions2)

    for index, row in enumerate(transactions2):
        transactions2_by_key[_transaction_key(row)][_transaction_date(row)].append(index)

    transactions1_by_key: DefaultDict[TransactionKey, list[tuple[int, int]]] = defaultdict(
        list
    )
    for index, row in enumerate(transactions1):
        transactions1_by_key[_transaction_key(row)].append((_transaction_date(row), index))

    for key, rows in transactions1_by_key.items():
        rows.sort()
        matching_rows = transactions2_by_key.get(key)
        if not matching_rows:
            continue

        for tx_date, left_index in rows:
            right_index = _consume_match(matching_rows, tx_date)
            if right_index is None:
                continue
            statuses1[left_index] = "FOUND"
            statuses2[right_index] = "FOUND"

    output1 = [list(row) + [status] for row, status in zip(transactions1, statuses1)]
    output2 = [list(row) + [status] for row, status in zip(transactions2, statuses2)]
    return output1, output2


def _transaction_key(row: Transaction) -> TransactionKey:
    return row[1], row[2], row[3]


def _transaction_date(row: Transaction) -> int:
    return date.fromisoformat(row[0]).toordinal()


def _consume_match(
    matching_rows: DefaultDict[int, Deque[int]], tx_date: int
) -> Optional[int]:
    for candidate_date in (tx_date - 1, tx_date, tx_date + 1):
        candidates = matching_rows.get(candidate_date)
        if not candidates:
            continue

        matched_index = candidates.popleft()
        if not candidates:
            del matching_rows[candidate_date]
        return matched_index

    return None
