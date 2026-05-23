"""Tests for utilities.classes.file.archive_callback.

The two wrapper classes (``py7zrCallBackWrapperExtract`` and
``py7zrCallBackWrapperArchive``) are thin shims around py7zr's progress
callbacks. The interesting bit is the ``display_bar`` toggle: when set to a
positive count, a ``tqdm`` bar is created and ticked; when zero, callbacks
are no-ops.
"""

from unittest.mock import MagicMock, patch

import pytest

from utilities.classes.file import archive_callback as ac


class TestExtractCallbackNoBar:
    """display_bar=0 — every report_* method is a no-op (no tqdm bar created)."""

    def test_init_does_not_create_bar(self):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=0)
        assert cb.count == 0
        assert cb.bar is None

    def test_start_preparation_does_not_create_bar(self, capsys):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=0)
        cb.report_start_preparation()
        assert cb.bar is None
        # Still prints the lifecycle marker
        assert "report_start_preparation" in capsys.readouterr().out

    def test_end_does_not_call_update(self):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=0)
        # No bar exists; calling report_end should not raise.
        cb.report_end("/some/path", 1234)
        assert cb.bar is None

    def test_postprocess_does_not_call_close(self, capsys):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=0)
        cb.report_postprocess()
        assert "report_postprocess" in capsys.readouterr().out


class TestExtractCallbackWithBar:
    """display_bar>0 — tqdm bar created, ticked on report_end, closed on postprocess."""

    @pytest.fixture
    def fake_tqdm(self):
        with patch.object(ac, "tqdm") as mock_tqdm:
            mock_tqdm.return_value = MagicMock()
            yield mock_tqdm

    def test_start_preparation_creates_bar(self, fake_tqdm):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=10)
        cb.report_start_preparation()
        fake_tqdm.assert_called_once()
        assert fake_tqdm.call_args.kwargs["total"] == 10
        assert fake_tqdm.call_args.kwargs["ncols"] == ac.BAR_COL_WIDTH

    def test_report_end_ticks_bar(self, fake_tqdm):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=10)
        cb.report_start_preparation()
        cb.report_end("/some/file", 42)
        cb.bar.update.assert_called_once_with()

    def test_report_postprocess_closes_bar(self, fake_tqdm):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=10)
        cb.report_start_preparation()
        cb.report_postprocess()
        cb.bar.close.assert_called_once_with()


class TestSilentCallbacks:
    """The pass-through callbacks must not raise regardless of bar state."""

    @pytest.mark.parametrize("count", [0, 5])
    def test_report_start_is_noop(self, count):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=count)
        cb.report_start("/file", 123)  # should not raise

    @pytest.mark.parametrize("count", [0, 5])
    def test_report_warning_is_noop(self, count):
        cb = ac.py7zrCallBackWrapperExtract(display_bar=count)
        cb.report_warning("a warning")  # should not raise


class TestArchiveCallbackInheritance:
    def test_archive_wrapper_inherits_behaviour(self):
        cb = ac.py7zrCallBackWrapperArchive(display_bar=0)
        assert isinstance(cb, ac.py7zrCallBackWrapperExtract)
        assert cb.bar is None
