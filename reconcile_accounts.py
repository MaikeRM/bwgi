from collections import defaultdict, deque
from datetime import date


def reconcile_accounts(transactions1, transactions2):
    """Reconcile two lists of financial transactions.

    Two transactions match when department, amount and beneficiary are equal and
    the dates differ by at most one day. Duplicates are allowed, but each row can
    only be matched once.
    """

    available = defaultdict(lambda: defaultdict(deque))
    for index, row in enumerate(transactions2):
        available[_signature(row)][_as_ordinal(row[0])].append(index)

    statuses1 = ["MISSING"] * len(transactions1)
    statuses2 = ["MISSING"] * len(transactions2)

    ordered_left = []
    for index, row in enumerate(transactions1):
        ordered_left.append((_signature(row), _as_ordinal(row[0]), index))
    ordered_left.sort()

    for signature, tx_date, left_index in ordered_left:
        candidates_by_date = available.get(signature)
        if candidates_by_date is None:
            continue

        right_index = _take_match(candidates_by_date, tx_date)
        if right_index is None:
            continue

        statuses1[left_index] = "FOUND"
        statuses2[right_index] = "FOUND"

    output1 = [list(row) + [status] for row, status in zip(transactions1, statuses1)]
    output2 = [list(row) + [status] for row, status in zip(transactions2, statuses2)]
    return output1, output2


def _signature(row):
    return row[1], row[2], row[3]


def _as_ordinal(value):
    return date.fromisoformat(value).toordinal()


def _take_match(candidates_by_date, tx_date):
    for candidate_date in (tx_date - 1, tx_date, tx_date + 1):
        candidates = candidates_by_date.get(candidate_date)
        if not candidates:
            continue

        matched_index = candidates.popleft()
        if not candidates:
            del candidates_by_date[candidate_date]
        return matched_index

    return None
