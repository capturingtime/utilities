"""Tests for Archive file class."""
import pytest
import py7zr

from utilities.classes.file.archive import Archive
from utilities.classes.path.file import File
from utilities.classes.path.dir import Dir


def _make_archive(path: str) -> Archive:
    """Helper: create a valid empty archive at path."""
    with py7zr.SevenZipFile(path, "w"):
        pass
    return Archive(path)


class TestArchive:
    def test_isarchive_false_when_missing(self, tmp_path):
        a = Archive(str(tmp_path / "nonexistent.7z"))
        assert a.isarchive is False

    def test_isarchive_false_for_non_archive_file(self, tmp_path):
        f = tmp_path / "fake.7z"
        f.write_text("not an archive")
        assert Archive(str(f)).isarchive is False

    def test_isarchive_true_for_valid_archive(self, tmp_path):
        path = str(tmp_path / "real.7z")
        a = _make_archive(path)
        assert a.isarchive is True

    def test_create_makes_valid_archive(self, tmp_path):
        path = str(tmp_path / "created.7z")
        a = Archive(path)
        assert not a.isarchive
        result = a._create()
        assert result is True
        assert a.isarchive

    def test_create_idempotent_when_already_archive(self, tmp_path):
        path = str(tmp_path / "existing.7z")
        a = _make_archive(path)
        assert a._create() is True  # should return True without error

    def test_create_raises_if_non_archive_file_exists(self, tmp_path):
        f = tmp_path / "conflict.7z"
        f.write_text("garbage")
        a = Archive(str(f))
        with pytest.raises(FileExistsError):
            a._create()

    def test_check_crc_on_valid_archive(self, tmp_path):
        path = str(tmp_path / "crc.7z")
        # Add a real file so testzip has something to check
        src_file = tmp_path / "content.txt"
        src_file.write_text("hello crc")
        with py7zr.SevenZipFile(path, "w") as zf:
            zf.write(str(src_file), "content.txt")
        a = Archive(path)
        result = a.check_crc()
        assert result is None  # None means no errors

    def test_check_crc_raises_on_non_archive(self, tmp_path):
        f = tmp_path / "bad.7z"
        f.write_text("not an archive")
        with pytest.raises(FileExistsError):
            Archive(str(f)).check_crc()

    def test_add_single_file(self, tmp_path):
        archive_path = str(tmp_path / "out.7z")
        src = tmp_path / "file.txt"
        src.write_text("archived content")

        a = Archive(archive_path)
        a.add(File(str(src)))

        assert a.isarchive
        with py7zr.SevenZipFile(archive_path, "r") as zf:
            names = zf.getnames()
        assert "file.txt" in names

    def test_add_does_not_truncate_existing_content(self, tmp_path):
        """Second call to add() must not wipe content added in the first call."""
        archive_path = str(tmp_path / "multi.7z")
        f1 = tmp_path / "first.txt"
        f2 = tmp_path / "second.txt"
        f1.write_text("first")
        f2.write_text("second")

        a = Archive(archive_path)
        a.add(File(str(f1)))
        a.add(File(str(f2)))

        with py7zr.SevenZipFile(archive_path, "r") as zf:
            names = zf.getnames()
        assert "first.txt" in names
        assert "second.txt" in names

    def test_add_raises_for_wrong_type(self, tmp_path):
        a = Archive(str(tmp_path / "x.7z"))
        with pytest.raises(TypeError):
            a.add("not_a_file_or_dir")  # type: ignore

    def test_extract_raises_for_wrong_dst_type(self, tmp_path):
        path = str(tmp_path / "ex.7z")
        a = _make_archive(path)
        with pytest.raises(TypeError):
            a.extract("not_a_dir_obj")  # type: ignore
