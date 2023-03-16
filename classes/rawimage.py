import rawpy
import imageio
from .file import File
import logging


class RawImage(File):
    """
    Method Ideas:
        - For files, use a Path object to normalize, and add a helper func to return a path object from path string
    """

    def __init__(
        self, raw_file: str, logger: logging.Logger = logging.getLogger(__name__)
    ):
        super().__init__(raw_file)

        self.log = logger
        self.file_path: str = raw_file
        self.raw: rawpy._rawpy.RawPy = rawpy.imread()
        self.preview = self.raw.extract_thumb()
        self.postprocess = self.raw.postprocess()

    # Do we load dst as File() also to better control operations?
    def save_preview(self, dst):
        """ """
        # try:
        #     dst = File(dst)
        # except FileNotFoundError:

        # if dst.isdir:

        if self.preview.format == rawpy.ThumbFormat.JPEG:
            with open(dst.abspath, "wb") as f:
                f.write(self.preview.data)
            self.log.debug(f"Preview JPEG saved to {dst}")

        elif self.preview.format == rawpy.ThumbFormat.BITMAP:
            # thumb.data is an RGB numpy array, convert with imageio
            imageio.imsave(dst, self.preview.data)
            self.log.debug(f"Preview JPEG saved to {dst}")

        else:
            msg = f"Unable to save preview from RAW Image, Unsupported thumb type: {self.preview}"
            self.log.error(msg)
            raise TypeError(msg)

    def save_tiff(self, dst):
        """Extract and save as .tiff"""
        imageio.imsave(dst, self.postprocess)
