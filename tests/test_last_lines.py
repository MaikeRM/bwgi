import io
import os
import tempfile
import unittest

from last_lines import last_lines


class LastLinesTests(unittest.TestCase):
    def test_returns_lines_in_reverse_order(self) -> None:
        path = self._write_temp_file("This is a file\nThis is line 2\nAnd this is line 3\n")
        self.addCleanup(os.remove, path)

        self.assertEqual(
            list(last_lines(path, chunk_size=8)),
            ["And this is line 3\n", "This is line 2\n", "This is a file\n"],
        )

    def test_returns_a_real_iterator(self) -> None:
        path = self._write_temp_file("a\nb\nc\n")
        self.addCleanup(os.remove, path)

        lines = last_lines(path, chunk_size=2)

        self.assertIs(iter(lines), lines)
        self.assertEqual(next(lines), "c\n")
        self.assertEqual(next(lines), "b\n")
        self.assertEqual(next(lines), "a\n")

    def test_handles_utf8_characters_split_across_chunks(self) -> None:
        path = self._write_temp_file("linha 1\ncafé\n東京\n🙂 emoji\n")
        self.addCleanup(os.remove, path)

        self.assertEqual(
            list(last_lines(path, chunk_size=5)),
            ["🙂 emoji\n", "東京\n", "café\n", "linha 1\n"],
        )

    def test_preserves_missing_trailing_newline(self) -> None:
        path = self._write_temp_file("primeira\nsegunda")
        self.addCleanup(os.remove, path)

        self.assertEqual(list(last_lines(path, chunk_size=4)), ["segunda", "primeira\n"])

    def test_rejects_non_positive_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            list(last_lines("ignored.txt", chunk_size=0))

    def _write_temp_file(self, content: str) -> str:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", delete=False
        ) as handle:
            handle.write(content)
            return handle.name


if __name__ == "__main__":
    unittest.main()

