import rawpy
import imageio
from ..path.file import File
import logging


class RawImage(File):
    """Wraps a camera RAW file for preview and TIFF export.

    rawpy.imread() is expensive — it decodes the full RAW at init. Cache this instance
    rather than re-instantiating it when exporting multiple formats from the same file.
    """

    def __init__(
        self, raw_file: str, logger: logging.Logger = logging.getLogger(__name__)
    ):
        super().__init__(raw_file)

        self.log = logger
        self.file_path: str = raw_file
        self.raw: rawpy._rawpy.RawPy = rawpy.imread(raw_file)
        self.preview = self.raw.extract_thumb()
        self.postprocess = self.raw.postprocess()

    def save_preview(self, dst: File):
        """Extract and save the embedded preview image to dst.

        Prefers the embedded JPEG thumbnail (lossless copy of camera-generated preview).
        Falls back to converting the BITMAP preview via imageio when JPEG is unavailable.
        """
        if dst.exists and dst.size > 0:
            msg = f"The provided destination file: {dst.abspath} already exists and is not empty"
            raise FileExistsError(msg)
        elif dst.exists and dst.size == 0:
            dst.delete(confirm=True)

        if dst.exists:
            msg = f"The provided destination file: {dst.abspath} exists and couldn't be deleted"
            raise FileExistsError(msg)

        if self.preview.format == rawpy.ThumbFormat.JPEG:
            with open(dst.abspath, "wb") as j:
                j.write(self.preview.data)
            self.log.debug(f"Preview JPEG saved to {dst}")

        elif self.preview.format == rawpy.ThumbFormat.BITMAP:
            # thumb.data is an RGB numpy array, convert with imageio
            imageio.imsave(dst, self.preview.data)
            self.log.debug(f"Preview JPEG saved to {dst}")

        else:
            msg = (
                "Unable to save preview from RAW Image, "
                f"Unsupported thumb type: {self.preview.format}"
            )
            self.log.error(msg)
            raise TypeError(msg)

    def save_tiff(self, dst: File):
        """Save the full-resolution postprocessed RAW as a TIFF."""
        imageio.imsave(dst.abspath, self.postprocess)
