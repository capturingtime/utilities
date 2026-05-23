"""Smoke tests for utilities.classes.file.rawimage.

``RawImage`` is a thin wrapper over ``rawpy.imread()`` plus a couple of
``imageio.imsave`` calls. Meaningful tests would need a small camera RAW
fixture file (e.g. a Canon ``.CR3``), which isn't shipped in the repo. The
tests below cover what can be verified without a fixture:

* the module imports cleanly when ``rawpy`` is available
* ``RawImage`` inherits from ``File`` (so ``RawImage(path)`` works wherever a
  ``File(path)`` does)
* invoking the constructor on a non-RAW file raises a recognizable error
  (rather than e.g. crashing the interpreter)

If a maintainer adds a small ``.CR3`` or ``.RAF`` fixture under
``utilities/tests/fixtures/raw/``, replace the smoke tests with real
preview/TIFF round-trip tests.
"""

import pytest

pytest.importorskip("rawpy", reason="rawpy not installed (no [raw] extra)")
pytest.importorskip("imageio")

from utilities.classes.file.rawimage import RawImage  # noqa: E402
from utilities.classes.path.file import File  # noqa: E402


def test_rawimage_is_a_file_subclass():
    assert issubclass(RawImage, File)


def test_constructor_on_non_raw_file_raises(tmp_path):
    """A plain text file is not a RAW image; rawpy should reject it.

    The specific exception class is rawpy's internal LibRawError or similar;
    we only care that the constructor does not silently succeed.
    """
    fake = tmp_path / "not_a_raw.txt"
    fake.write_text("definitely not a CR3")
    with pytest.raises(Exception):
        RawImage(str(fake))


def test_constructor_on_missing_file_raises(tmp_path):
    missing = tmp_path / "does_not_exist.CR3"
    with pytest.raises(Exception):
        RawImage(str(missing))
