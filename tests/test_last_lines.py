import io
import os
import tempfile
import unittest
from collections.abc import Iterator

from last_lines import last_lines

class LastLinesTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a temporary test directory and file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = os.path.join(self.temp_dir.name, "my_file.txt")

    def tearDown(self) -> None:
        """Cleanup temporary files"""
        self.temp_dir.cleanup()

    def test_example_behavior(self) -> None:
        """Test the exact behavior specified in the challenge description."""
        content = "This is a file\nThis is line 2\nAnd this is line 3\n"
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

        lines = last_lines(self.filepath)
        
        self.assertIsInstance(lines, Iterator, "Should return an iterator")
        
        self.assertEqual(next(lines), "And this is line 3\n")
        self.assertEqual(next(lines), "This is line 2\n")
        self.assertEqual(next(lines), "This is a file\n")
        
        with self.assertRaises(StopIteration):
            next(lines)

    def test_with_custom_chunk_size(self) -> None:
        """Test functioning correctly with a small default buffer size."""
        content = "Line 1\nLine 2\nLine 3\n"
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # A very small chunk size (e.g., 2) forces multiple reads across a single line
        lines = last_lines(self.filepath, chunk_size=2)
        
        self.assertEqual(next(lines), "Line 3\n")
        self.assertEqual(next(lines), "Line 2\n")
        self.assertEqual(next(lines), "Line 1\n")
        with self.assertRaises(StopIteration):
            next(lines)

    def test_utf8_multi_byte_characters(self) -> None:
        """Ensure UTF-8 multibyte characters are properly decoded even when read in chunks."""
        # ã is 2 bytes (\xc3\xa3), ç is 2 bytes (\xc3\xa7)
        # Using a tiny chunk size ensures reading splits these bytes.
        content = "Primeira linha com português\nSegunda linha com o caractere maçã\n"
        
        with open(self.filepath, "wb") as f:
            f.write(content.encode('utf-8'))

        # Chunk size 1 guarantees characters split at byte boundaries inside the chunking logic
        # although since we split by lines we are protected anyway.
        result_lines = list(last_lines(self.filepath, chunk_size=1))
        
        self.assertEqual(len(result_lines), 2)
        self.assertEqual(result_lines[0], "Segunda linha com o caractere maçã\n")
        self.assertEqual(result_lines[1], "Primeira linha com português\n")

    def test_file_without_trailing_newline(self) -> None:
        """Test file without an EOF trailing newline."""
        content = "First line\nSecond line"
        
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

        lines = last_lines(self.filepath, chunk_size=io.DEFAULT_BUFFER_SIZE)
        
        # The parser appends a \n if we followed the requirements stringently to
        # make it act like python iterations, but actually it returns exactly 
        # what's there on the last chunk. Let's see how our underlying function handles it.
        # last_lines.py handles missing \n by yielding the exact original string decoded.
        self.assertEqual(next(lines), "Second line")
        self.assertEqual(next(lines), "First line\n")

    def test_empty_file(self) -> None:
        """A completely empty file should yield nothing."""
        with open(self.filepath, "wb") as f:
            pass

        lines = last_lines(self.filepath)
        with self.assertRaises(StopIteration):
            next(lines)

    def test_invalid_chunk_size_zero(self) -> None:
        """chunk_size=0 must raise ValueError."""
        with open(self.filepath, "wb") as f:
            f.write(b"hello\n")

        with self.assertRaises(ValueError):
            list(last_lines(self.filepath, chunk_size=0))

    def test_invalid_chunk_size_negative(self) -> None:
        """Negative chunk_size must raise ValueError."""
        with open(self.filepath, "wb") as f:
            f.write(b"hello\n")

        with self.assertRaises(ValueError):
            list(last_lines(self.filepath, chunk_size=-1))

    def test_invalid_chunk_size_non_integer_types(self) -> None:
        """Non-integer chunk_size values must raise ValueError."""
        with open(self.filepath, "wb") as f:
            f.write(b"hello\n")

        for invalid_chunk_size in (1.5, "4", None, True, False):
            with self.subTest(chunk_size=invalid_chunk_size):
                with self.assertRaises(ValueError):
                    list(last_lines(self.filepath, chunk_size=invalid_chunk_size))

    def test_single_line_with_newline(self) -> None:
        """A file with exactly one line (with trailing newline) yields that line."""
        with open(self.filepath, "wb") as f:
            f.write(b"only line\n")

        result = list(last_lines(self.filepath))
        self.assertEqual(result, ["only line\n"])

    def test_single_line_without_newline(self) -> None:
        """A file with exactly one line (no trailing newline) yields that line without newline."""
        with open(self.filepath, "wb") as f:
            f.write(b"only line")

        result = list(last_lines(self.filepath))
        self.assertEqual(result, ["only line"])

    def test_line_longer_than_chunk_size(self) -> None:
        """A line longer than chunk_size must still be returned intact."""
        long_line = "a" * 200 + "\n"
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(long_line)

        result = list(last_lines(self.filepath, chunk_size=8))
        self.assertEqual(result, [long_line])

    def test_only_newlines(self) -> None:
        """A file containing only newline characters yields each as an empty line."""
        with open(self.filepath, "wb") as f:
            f.write(b"\n\n\n")

        result = list(last_lines(self.filepath))
        self.assertEqual(result, ["\n", "\n", "\n"])

    def test_empty_lines_between_content(self) -> None:
        """Empty lines between content lines are yielded as bare newlines."""
        with open(self.filepath, "wb") as f:
            f.write(b"line1\n\nline3\n")

        result = list(last_lines(self.filepath))
        self.assertEqual(result, ["line3\n", "\n", "line1\n"])

    def test_many_lines_small_chunk(self) -> None:
        """100 lines with a small chunk_size must come out in correct reverse order."""
        lines = [f"linha {i}\n" for i in range(1, 101)]
        content = "".join(lines).encode("utf-8")
        with open(self.filepath, "wb") as f:
            f.write(content)

        result = list(last_lines(self.filepath, chunk_size=16))
        self.assertEqual(result, list(reversed(lines)))

    def test_chunk_size_larger_than_file(self) -> None:
        """chunk_size larger than the file must work as if reading all at once."""
        content = "abc\ndef\n"
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

        result = list(last_lines(self.filepath, chunk_size=10_000))
        self.assertEqual(result, ["def\n", "abc\n"])

    def test_file_not_found(self) -> None:
        """A non-existent path must propagate FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            list(last_lines("/tmp/__nonexistent_file_xyz__.txt"))


if __name__ == "__main__":
    unittest.main()
