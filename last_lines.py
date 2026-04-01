from __future__ import annotations

import io
import os
from typing import Iterator, Union


def last_lines(
    file_path: Union[os.PathLike[str], str],
    chunk_size: int = io.DEFAULT_BUFFER_SIZE,
) -> Iterator[str]:
    """Yield the lines of a UTF-8 text file in reverse order."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    with open(file_path, "rb") as handle:
        handle.seek(0, io.SEEK_END)
        file_size = handle.tell()
        if file_size == 0:
            return

        handle.seek(file_size - 1)
        endswith_newline = handle.read(1) == b"\n"

        pending = b""
        suffix_is_terminated = endswith_newline
        position = file_size
        first_block = True

        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            handle.seek(position)
            block = handle.read(read_size)
            data = block + pending
            search_end = len(data)

            # Ignore the synthetic empty segment created by the final newline.
            if first_block and endswith_newline:
                search_end -= 1

            while True:
                newline_index = data.rfind(b"\n", 0, search_end)
                if newline_index == -1:
                    break

                line = data[newline_index + 1 : search_end].decode("utf-8")
                if suffix_is_terminated:
                    line += "\n"
                yield line

                suffix_is_terminated = True
                search_end = newline_index

            pending = data[:search_end]
            first_block = False

        line = pending.decode("utf-8")
        if suffix_is_terminated:
            line += "\n"
        yield line
