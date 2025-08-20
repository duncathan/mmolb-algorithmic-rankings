import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile


@contextmanager
def safe_write(path: Path, *, encoding: str | None = None, newline: str | None = None):
    try:
        f = None
        with NamedTemporaryFile("w", encoding=encoding, newline=newline, dir=path.parent, delete=False) as f:  # noqa: F811
            yield f
        os.replace(f.name, path)
        f = None
    finally:
        if f is not None:
            os.remove(f.name)
