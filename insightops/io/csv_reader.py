import contextlib
from pathlib import Path
from typing import Generator, Tuple, TextIO


class CsvDecodeError(Exception):
    pass


def detect_csv_encoding(path: Path) -> str:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1"]
    for enc in encodings:
        try:
            with path.open(mode="r", encoding=enc) as f:
                chunk_size = 65536
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    if "\x00" in chunk:
                        raise UnicodeDecodeError(
                            enc, b"", 0, 1, "Null byte detected (binary file)"
                        )
            return enc
        except UnicodeDecodeError:
            continue
    raise CsvDecodeError(
        "CSV file could not be decoded. Supported encodings are UTF-8, UTF-8 BOM, Windows-1252, and ISO-8859-1."
    )


@contextlib.contextmanager
def open_csv_text(path: Path) -> Generator[Tuple[TextIO, str], None, None]:
    encoding = detect_csv_encoding(path)
    f = path.open(mode="r", newline="", encoding=encoding)
    try:
        yield f, encoding
    finally:
        f.close()
