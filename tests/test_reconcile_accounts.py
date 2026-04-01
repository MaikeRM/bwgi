import unittest

from reconcile_accounts import reconcile_accounts


class ReconcileAccountsTests(unittest.TestCase):
    def test_statement_example(self) -> None:
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
                ["2020-12-04", "Tecnologia", "16.00", "Bitbucket", "FOUND"],
                ["2020-12-04", "Jurídico", "60.00", "LinkSquares", "FOUND"],
                ["2020-12-05", "Tecnologia", "50.00", "AWS", "MISSING"],
            ],
        )
        self.assertEqual(
            out2,
            [
                ["2020-12-04", "Tecnologia", "16.00", "Bitbucket", "FOUND"],
                ["2020-12-05", "Tecnologia", "49.99", "AWS", "MISSING"],
                ["2020-12-04", "Jurídico", "60.00", "LinkSquares", "FOUND"],
            ],
        )

    def test_duplicate_rows_match_one_to_one(self) -> None:
        transactions1 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
        ]
        transactions2 = [
            ["2020-12-04", "Tecnologia", "16.00", "Bitbucket"],
        ]

        out1, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual([row[-1] for row in out1], ["FOUND", "MISSING"])
        self.assertEqual([row[-1] for row in out2], ["FOUND"])

    def test_prefers_the_earliest_possible_date(self) -> None:
        transactions1 = [
            ["2020-12-25", "Tecnologia", "50.00", "AWS"],
        ]
        transactions2 = [
            ["2020-12-25", "Tecnologia", "50.00", "AWS"],
            ["2020-12-24", "Tecnologia", "50.00", "AWS"],
            ["2020-12-26", "Tecnologia", "50.00", "AWS"],
        ]

        _, out2 = reconcile_accounts(transactions1, transactions2)

        self.assertEqual([row[-1] for row in out2], ["MISSING", "FOUND", "MISSING"])

    def test_does_not_mutate_inputs(self) -> None:
        transactions1 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]
        transactions2 = [["2020-12-04", "Tecnologia", "16.00", "Bitbucket"]]

        original1 = [row[:] for row in transactions1]
        original2 = [row[:] for row in transactions2]

        reconcile_accounts(transactions1, transactions2)

        self.assertEqual(transactions1, original1)
        self.assertEqual(transactions2, original2)


if __name__ == "__main__":
    unittest.main()

