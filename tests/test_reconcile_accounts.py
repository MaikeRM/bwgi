import unittest

from reconcile_accounts import FOUND, MISSING, reconcile_accounts


class ReconcileAccountsTests(unittest.TestCase):
    # ------------------------------------------------------------------
    # Happy-path tests (original coverage)
    # ------------------------------------------------------------------

    def test_statement_example(self) -> None:
        """Validate an end-to-end reconciliation with matches and misses."""
        transactions1 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
            ["2020-12-04", "Jurídico", "60.00", "LinkSquares"],
            ["2020-12-05", "Tecnologia", "50.00", "AWS"],
        ]
        transactions2 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
            ["2020-12-05", "Tecnologia", "49.99", "AWS"],
            ["2020-12-04", "Jurídico", "60.00", "LinkSquares"],
        ]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual(
            out1,
            [
                ["2020-12-04", "Tecnologia", "16.00", "Bitbucket", FOUND],
                ["2020-12-04", "Jurídico", "60.00", "LinkSquares", FOUND],
                ["2020-12-05", "Tecnologia", "50.00", "AWS", MISSING],
            ],
        )
        self.assertEqual(
            out2,
            [
                ["2020-12-04", "Tecnologia", "16.00", "Bitbucket", FOUND],
                ["2020-12-05", "Tecnologia", "49.99", "AWS", MISSING],
                ["2020-12-04", "Jurídico", "60.00", "LinkSquares", FOUND],
            ],
        )

    def test_duplicate_rows_match_one_to_one(self) -> None:
        """Ensure multiple identical rows only match available counterparts one-to-one."""
        transactions1 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
        ]
        transactions2 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
        ]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual([row[-1] for row in out1], [FOUND, MISSING])
        self.assertEqual([row[-1] for row in out2], [FOUND])

    def test_prefers_the_earliest_possible_date(self) -> None:
        """Ensure date matching favors the earliest valid offset (−1 day first)."""
        transactions1 = [
            ["2020-12-25", "Tecnologia", "50.00", "AWS"],
        ]
        transactions2 = [
            ["2020-12-25", "Tecnologia", "50.00", "AWS"],
            ["2020-12-24", "Tecnologia", "50.00", "AWS"],
            ["2020-12-26", "Tecnologia", "50.00", "AWS"],
        ]

        _, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual([row[-1] for row in out2], [MISSING, FOUND, MISSING])

    def test_does_not_mutate_inputs(self) -> None:
        """Verify inputs are structurally preserved and unaltered."""
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]
        transactions2 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        original1 = [row[:] for row in transactions1]
        original2 = [row[:] for row in transactions2]

        reconcile_accounts(transactions1, transactions2)

        self.assertEqual(transactions1, original1)
        self.assertEqual(transactions2, original2)

    # ------------------------------------------------------------------
    # Edge case — empty inputs
    # ------------------------------------------------------------------

    def test_both_lists_empty(self) -> None:
        """Empty inputs must return two empty lists without errors."""
        out1, out2 = reconcile_accounts([], [])
        self.assertEqual(out1, [])
        self.assertEqual(out2, [])

    def test_one_list_empty(self) -> None:
        """A non-empty list reconciled against an empty one yields all MISSING."""
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        out1, out2 = reconcile_accounts(transactions1, [])

        self.assertEqual([row[-1] for row in out1], [MISSING])
        self.assertEqual(out2, [])

    def test_all_missing_no_matches(self) -> None:
        """When no row in t1 has any counterpart in t2, every row is MISSING."""
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]
        transactions2 = [["2020-12-04", "Jurídico", "99.00", "OtherCo"]]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual([row[-1] for row in out1], [MISSING])
        self.assertEqual([row[-1] for row in out2], [MISSING])

    # ------------------------------------------------------------------
    # Edge case — structural validation (ValueError)
    # ------------------------------------------------------------------

    def test_row_too_short_in_transactions1_raises(self) -> None:
        """A row with fewer than 4 columns in transactions1 raises ValueError."""
        bad = [["2020-12-04", "Tecnologia"]]  # only 2 columns
        valid = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        with self.assertRaises(ValueError) as ctx:
            reconcile_accounts(bad, valid)

        self.assertIn("transactions1[0]", str(ctx.exception))
        self.assertIn("4 columns", str(ctx.exception))

    def test_row_too_short_in_transactions2_raises(self) -> None:
        """A row with fewer than 4 columns in transactions2 raises ValueError."""
        valid = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]
        bad = [["2020-12-04"]]  # only 1 column

        with self.assertRaises(ValueError) as ctx:
            reconcile_accounts(valid, bad)

        self.assertIn("transactions2[0]", str(ctx.exception))
        self.assertIn("4 columns", str(ctx.exception))

    def test_empty_row_raises(self) -> None:
        """A completely empty row raises ValueError."""
        with self.assertRaises(ValueError):
            reconcile_accounts([[]], [["2020-12-04", "T", "1.00", "B"]])

    # ------------------------------------------------------------------
    # Edge case — invalid date values (ValueError)
    # ------------------------------------------------------------------

    def test_invalid_date_string_raises(self) -> None:
        """A malformed date string (not ISO-8601) raises ValueError."""
        bad = [["04/12/2020", "Tecnologia", "16.00", "Bitbucket"]]
        valid = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        with self.assertRaises(ValueError) as ctx:
            reconcile_accounts(bad, valid)

        self.assertIn("04/12/2020", str(ctx.exception))

    def test_impossible_date_raises(self) -> None:
        """A syntactically plausible but calendar-invalid date raises ValueError."""
        bad = [["2020-13-40", "Tecnologia", "16.00", "Bitbucket"]]
        valid = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        with self.assertRaises(ValueError):
            reconcile_accounts(bad, valid)

    def test_none_date_raises(self) -> None:
        """None in the date field raises ValueError (str(None) is not a valid date)."""
        bad = [[None, "Tecnologia", "16.00", "Bitbucket"]]
        valid = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        with self.assertRaises(ValueError) as ctx:
            reconcile_accounts(bad, valid)

        self.assertIn("None", str(ctx.exception))

    # ------------------------------------------------------------------
    # Edge case — string-literal comparison behaviours (documented)
    # ------------------------------------------------------------------

    def test_monetary_format_is_compared_as_string_literal(self) -> None:
        """Amount fields are matched as raw strings: '16.00' ≠ '16.0'.

        This is intentional — the spec states all columns are strings. Callers
        must normalise monetary formatting before reconciliation when data comes
        from systems with different conventions.
        """
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]
        transactions2 = [["2020-12-04", "Tecnologia", "16.0", "Bitbucket"]]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        # Same numeric value but different string representation → no match
        self.assertEqual(out1[0][-1], MISSING)
        self.assertEqual(out2[0][-1], MISSING)

    def test_comparison_is_case_sensitive(self) -> None:
        """String fields are compared with case sensitivity: 'AWS' ≠ 'aws'.

        Callers must normalise casing upstream if the data sources use different
        conventions.
        """
        transactions1 = [["2020-12-04", "Tecnologia", "50.00", "AWS"]]
        transactions2 = [["2020-12-04", "tecnologia", "50.00", "aws"]]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual(out1[0][-1], MISSING)
        self.assertEqual(out2[0][-1], MISSING)

    # ------------------------------------------------------------------
    # Edge case — extra columns are silently ignored
    # ------------------------------------------------------------------

    def test_extra_columns_are_preserved_and_match_succeeds(self) -> None:
        """Rows with more than 4 columns are accepted and still match correctly.

        Only the first four columns are used for matching. Any extra columns are
        carried through to the output unchanged.
        """
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket", "extra"]]
        transactions2 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket", "other"]]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        # Match should succeed despite different extra columns
        self.assertEqual(out1[0][-1], FOUND)
        self.assertEqual(out2[0][-1], FOUND)

        # Extra columns are preserved in the output
        self.assertIn("extra", out1[0])
        self.assertIn("other", out2[0])


if __name__ == "__main__":
    unittest.main()
