import io
import os
from typing import Iterator


def last_lines(
    filename: str,
    chunk_size: int = io.DEFAULT_BUFFER_SIZE
) -> Iterator[str]:
    """Yield lines from a text file in reverse order.

    Reads the file backwards in chunks without loading it entirely into memory.
    Correctly handles UTF-8 multibyte characters.

    Args:
        filename: Path to the UTF-8 text file.
        chunk_size: Maximum bytes to read per I/O operation.

    Yields:
        File lines in reverse order. Lines terminated by ``'\\n'`` include it;
        the first line of the file is yielded without ``'\\n'`` when the file
        does not end with a newline. Empty files yield nothing.

    Raises:
        ValueError: If ``chunk_size`` is not a positive integer.
    """
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    with open(filename, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()

        if pos == 0:
            return

        remainder = b""

        while pos > 0:
            n = min(chunk_size, pos)
            pos -= n
            f.seek(pos)
            chunk = f.read(n)

            data = chunk + remainder
            parts = data.split(b"\n")

            complete_lines = [part + b"\n" for part in parts[:-1]]
            trailing = parts[-1]
            if trailing:
                complete_lines.append(trailing)

            remainder = complete_lines[0] if complete_lines else data

            for line_bytes in reversed(complete_lines[1:]):
                yield line_bytes.decode("utf-8")

        if remainder:
            yield remainder.decode("utf-8")
