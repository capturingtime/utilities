from py7zr.callbacks import ExtractCallback
from tqdm import tqdm

BAR_COL_WIDTH: int = 60
BAR_FORMAT: str = "{l_bar}{bar} | Remaining: {r_bar}"


class py7zrCallBackWrapperExtract(ExtractCallback):
    """A Class wrapper for the py7zr.callbacks.ExtractCallback(Callback) Class
    https://py7zr.readthedocs.io/en/latest/contribution.html#callback-classes
    https://github.com/miurahr/py7zr/blob/master/py7zr/callbacks.py
    """

    def __init__(self, display_bar: int = 0):
        self.count: int = display_bar
        self.pbar_func: callable = tqdm
        self.bar: object = None

    def report_start_preparation(self):
        """report a start of preparation event such as making list
        of files and looking into its properties."""
        print("report_start_preparation")
        if self.count > 0:
            # Init Bar
            self.bar = self.pbar_func(
                ncols=BAR_COL_WIDTH, bar_format=BAR_FORMAT, total=self.count
            )

    def report_start(self, processing_file_path, processing_bytes):
        """report a start event of specified archive file and its input bytes."""
        pass

    def report_end(self, processing_file_path, wrote_bytes):
        """report an end event of specified archive file and its output bytes."""
        if self.count > 0:
            self.bar.update()

    def report_warning(self, message):
        """report an warning event with its message"""
        pass  # noqa

    def report_postprocess(self):
        """report a start of post processing event such as set
        file properties and permissions or creating symlinks."""
        if self.count > 0:
            self.bar.close()
        print("report_postprocess")


class py7zrCallBackWrapperArchive(py7zrCallBackWrapperExtract):
    """Currently (March 2023) the ArchiveCallback and ExtractCallback classes in py7zr
    inherit a common 'Callback' class and are functionally identical. Following style
    here for potential future implmentation of a split of the logic
    """

    pass
