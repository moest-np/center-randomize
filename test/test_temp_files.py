import io
import os
import stat
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.temp_files import saved_uploads


def upload(content: bytes) -> io.BytesIO:
    """Like a Streamlit UploadedFile that has already been read once."""
    file = io.BytesIO(content)
    file.read()
    return file


def test_files_are_saved_with_their_content():
    uploads = {"schools": upload(b"scode\tcount\n1\t10\n"), "prefs": upload(b"")}
    with saved_uploads(uploads) as paths:
        assert set(paths) == {"schools", "prefs"}
        with open(paths["schools"], "rb") as file:
            assert file.read() == b"scode\tcount\n1\t10\n"
        assert os.path.getsize(paths["prefs"]) == 0
        assert paths["schools"].endswith("schools.tsv")


def test_files_and_directory_are_removed_afterwards():
    with saved_uploads({"schools": upload(b"x")}) as paths:
        directory = os.path.dirname(paths["schools"])
        assert os.path.isdir(directory)
    assert not os.path.exists(directory)


def test_files_are_removed_when_the_block_fails():
    with pytest.raises(RuntimeError):
        with saved_uploads({"schools": upload(b"x")}) as paths:
            directory = os.path.dirname(paths["schools"])
            raise RuntimeError("program failed")
    assert not os.path.exists(directory)


def test_every_call_gets_its_own_directory():
    with saved_uploads({"a": upload(b"1")}) as first:
        with saved_uploads({"a": upload(b"2")}) as second:
            assert os.path.dirname(first["a"]) != os.path.dirname(second["a"])


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions only")
def test_directory_is_private_to_the_current_user():
    with saved_uploads({"a": upload(b"1")}) as paths:
        mode = stat.S_IMODE(os.stat(os.path.dirname(paths["a"])).st_mode)
        assert mode == 0o700
