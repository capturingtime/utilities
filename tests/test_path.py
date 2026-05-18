"""Tests for File and Dir concrete path implementations."""
import os
import pytest

from utilities.classes.path.file import File
from utilities.classes.path.dir import Dir


# ---------------------------------------------------------------------------
# File tests
# ---------------------------------------------------------------------------


class TestFile:
    def test_exists_true_for_real_file(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("hello")
        assert File(str(f)).exists is True

    def test_exists_false_for_missing(self, tmp_path):
        assert File(str(tmp_path / "ghost.txt")).exists is False

    def test_create_makes_empty_file(self, tmp_path):
        path = str(tmp_path / "new.txt")
        fi = File(path)
        assert not fi.exists
        fi.create()
        assert fi.exists
        assert fi.size == 0

    def test_create_idempotent_if_exists(self, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("data")
        fi = File(str(f))
        fi.create()  # should not raise
        assert fi.exists

    def test_delete_removes_file(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_text("bye")
        fi = File(str(f))
        fi.delete()
        assert not fi.exists

    def test_delete_raises_when_missing(self, tmp_path):
        fi = File(str(tmp_path / "nope.txt"))
        with pytest.raises(FileNotFoundError):
            fi.delete()

    def test_copy_produces_identical_content(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_bytes(b"binary content")
        dst_path = str(tmp_path / "dst.txt")

        fi = File(str(src))
        fi.copy(File(dst_path))

        assert open(dst_path, "rb").read() == b"binary content"

    def test_copy_raises_if_dst_exists(self, tmp_path):
        src = tmp_path / "a.txt"
        dst = tmp_path / "b.txt"
        src.write_text("x")
        dst.write_text("y")

        with pytest.raises(FileExistsError):
            File(str(src)).copy(File(str(dst)))

    def test_copy_raises_for_non_file_dst(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("x")
        with pytest.raises(TypeError):
            File(str(src)).copy("not_a_file_obj")  # type: ignore

    def test_sha256_is_deterministic(self, tmp_path):
        f = tmp_path / "hash.txt"
        f.write_text("consistent content")
        fi = File(str(f))
        assert fi.sha256 == fi.sha256

    def test_sha256_changes_with_content(self, tmp_path):
        f = tmp_path / "mutable.txt"
        f.write_text("before")
        fi = File(str(f))
        hash1 = fi.sha256
        f.write_text("after")
        hash2 = fi.sha256
        assert hash1 != hash2

    def test_sha256_raises_when_file_missing(self, tmp_path):
        fi = File(str(tmp_path / "missing.txt"))
        with pytest.raises(FileNotFoundError):
            _ = fi.sha256

    def test_str_returns_abspath(self, tmp_path):
        f = tmp_path / "x.txt"
        f.touch()
        fi = File(str(f))
        assert str(fi) == str(f.resolve())

    def test_basename(self, tmp_path):
        f = tmp_path / "photo.cr2"
        fi = File(str(f))
        assert fi.basename == "photo.cr2"

    def test_dirname(self, tmp_path):
        f = tmp_path / "photo.cr2"
        fi = File(str(f))
        assert fi.dirname == str(tmp_path)

    def test_size(self, tmp_path):
        f = tmp_path / "sized.txt"
        f.write_bytes(b"1234567890")
        fi = File(str(f))
        assert fi.size == 10


# ---------------------------------------------------------------------------
# Dir tests
# ---------------------------------------------------------------------------


class TestDir:
    def test_exists_true_for_real_dir(self, tmp_path):
        assert Dir(str(tmp_path)).exists is True

    def test_exists_false_for_missing(self, tmp_path):
        assert Dir(str(tmp_path / "ghost")).exists is False

    def test_create_makes_directory(self, tmp_path):
        path = str(tmp_path / "newdir")
        d = Dir(path)
        assert not d.exists
        d.create()
        assert d.exists

    def test_create_with_parents(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c")
        d = Dir(nested)
        d.create(p=True)
        assert d.exists

    def test_create_p_false_raises_if_exists(self, tmp_path):
        d = Dir(str(tmp_path))
        with pytest.raises(FileExistsError):
            d.create(p=False)

    def test_delete_removes_empty_dir(self, tmp_path):
        path = tmp_path / "todelete"
        path.mkdir()
        d = Dir(str(path))
        d.delete()
        assert not d.exists

    def test_delete_raises_when_missing(self, tmp_path):
        d = Dir(str(tmp_path / "nope"))
        with pytest.raises(FileNotFoundError):
            d.delete()

    def test_copy_not_implemented(self, tmp_path):
        d = Dir(str(tmp_path))
        with pytest.raises(NotImplementedError):
            d.copy(Dir(str(tmp_path / "dst")))

    def test_mv_not_implemented(self, tmp_path):
        d = Dir(str(tmp_path))
        with pytest.raises(NotImplementedError):
            d.mv()

    def test_str_returns_abspath(self, tmp_path):
        d = Dir(str(tmp_path))
        assert str(d) == str(tmp_path.resolve())
