"""Helpers to hand uploaded files to other programs through temporary files."""

from contextlib import contextmanager
from os import path
from typing import Dict, Iterator
import tempfile


@contextmanager
def saved_uploads(uploads: Dict[str, object]) -> Iterator[Dict[str, str]]:
    """
    Save uploaded files in a private temporary directory and yield their paths.

    uploads: name -> file like object (e.g. Streamlit UploadedFile), saved as <name>.tsv
    The directory has an unpredictable name and, where the platform supports it, is only
    accessible by the current user, so the files do not share a directory with other
    users' files. It is deleted with its contents when the block exits, also on errors.
    A failure to delete it (e.g. a file still held open by a virus scanner on Windows)
    is ignored, it must not turn a finished calculation into an error.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        paths = {}
        for name, upload in uploads.items():
            file_path = path.join(directory, f"{name}.tsv")
            upload.seek(0)  # Go to the start of the file
            with open(file_path, "wb") as file:
                file.write(upload.read())
            paths[name] = file_path
        yield paths
