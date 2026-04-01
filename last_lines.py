import io


def last_lines(file_path, chunk_size=io.DEFAULT_BUFFER_SIZE):
    """Yield the lines of a UTF-8 text file in reverse order."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    with open(file_path, "rb") as file_obj:
        file_obj.seek(0, io.SEEK_END)
        file_size = file_obj.tell()
        if file_size == 0:
            return

        file_obj.seek(file_size - 1)
        suffix_has_newline = file_obj.read(1) == b"\n"

        pending = b""
        position = file_size
        first_block = True

        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            file_obj.seek(position)
            block = file_obj.read(read_size)
            data = block + pending

            if first_block and suffix_has_newline:
                data = data[:-1]

            parts = data.split(b"\n")
            pending = parts[0]
            for part in reversed(parts[1:]):
                line = part.decode("utf-8")
                if suffix_has_newline:
                    line += "\n"
                yield line
                suffix_has_newline = True
            first_block = False

        line = pending.decode("utf-8")
        if suffix_has_newline:
            line += "\n"
        yield line
