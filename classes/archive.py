from .file import File, Dir
import py7zr
import logging


from tqdm import tqdm
from progressbar import Bar


class Archive(File):
    """A Class to define an Archive, inherits File"""

    """ Ideas
        - Instantiation should check if its an archive yet, and if its empty with a property
        - Create method to actually make an empty archive file, update property
        - add() checks if create() has been ran, create() if False
        -
    """

    def __init__(
        self, archive: str, logger: logging.Logger = logging.getLogger(__name__)
    ):
        super().__init__(archive)

        self.archive = super().abspath

    @property
    def isarchive(self) -> bool:
        if not super().exists:
            return False
        try:
            a: str = getattr(
                py7zr.SevenZipFile(super().abspath, "r"), "filename", str()
            )
        except (FileNotFoundError, OSError):
            return False
        return True if a else False

    def check_crc(self) -> [str, None]:
        """checks if there are CRC errors in the archive"""
        if self.isarchive:
            return py7zr.SevenZipFile(super().abspath, "r").testzip()
        else:
            raise FileExistsError("File exists and is not an archive")

    def extract(
        self, dst: Dir, file_list: list = list(), progress_bar: bool = False
    ) -> bool:
        """Extracts the contents of this archive (if exists) to the destination directory"""
        if not isinstance(dst, Dir):
            raise TypeError(f"dst must be type {type(Dir)}. Provided: {type(dst)}")
        if not dst.isdir:
            raise NotADirectoryError

        with py7zr.SevenZipFile(super().abspath, "r") as a:
            extract_list = list(file_list if file_list else a.getnames())
            if progress_bar:
                print(
                    "Progressbar is disabled for now, "
                    "archive is extracting silently in the background. "
                    'You\'ll get a "True" when its done.'
                )
                a.extract(path=dst.directory, targets=extract_list)
                # # This logic works, but is painfully slow. orders of magnitude slow
                # total = len(a.getnames())
                # # raise NotImplementedError
                # with tqdm(
                #     ncols=60,
                #     total=total,
                #     bar_format="{l_bar}{bar} | Remaining: {remaining}",
                # ) as pbar:
                #     for f in a.getnames():
                #         a.extract(path=dst.abspath, targets=[f])
                #         pbar.update(1)
                #         a.reset()  # https://py7zr.readthedocs.io/en/latest/api.html#py7zr.SevenZipFile.extract  # noqa: E501
            else:
                a.extract(path=dst.directory, targets=extract_list)

        return dst.exists

    def add(
        self,
        src: list([Dir, File]),
        folder_name: str = str(),
        progress_bar: bool = False,
    ) -> bool:
        """Adds a File or Dir to this archive"""
        type_err_msg = (
            "src must be a list with elements of "
            f"type {Dir} or {File}. Provided: {type(src)}"
        )
        if not isinstance(src, list):
            raise TypeError(type_err_msg)
        if not all(isinstance(i, (File, Dir)) for i in src):
            raise TypeError(type_err_msg)
        created = self._create() if not self.isarchive else True
        if not created:
            raise ChildProcessError(
                "Archive did not exist, an attempt to create it failed"
            )

        if folder_name:
            folder_name = folder_name.rstrip("\\/")
        with py7zr.SevenZipFile(super().abspath, "w") as a:
            if progress_bar:
                raise NotImplementedError
                c = len(src)
                # with tqdm(  # Draws the Bar
                #     ncols=60,
                #     total=c,
                #     bar_format="{l_bar}{bar} | Remaining: {remaining}",
                # ) as pbar:
                bar = Bar(
                    "Archiving Files:",
                    suffix="%(index)d/%(max)d ETA: %(eta)ds (Elapsed: %(elapsed)ds)",
                    max=c,
                )
            for f in src:
                prefix = f"{folder_name}/" if folder_name else ""

                if type(f) == File:
                    a.write(f.abspath, f"{prefix}{f.filename}")
                elif type(f) == Dir:
                    a.writeall(f.abspath, f"{prefix}{f.dirname}")
                else:
                    # This should have been caught in the earlier checks
                    raise TypeError(type_err_msg)
                if progress_bar:
                    bar.next()

    def _create(self) -> bool:
        """Creates the archive if it doesn't already exist"""
        if self.isarchive:
            return True
        if super().exists:
            # If this catches, it means there is a file but it not an archive
            raise FileExistsError("An attempt to create a non-existant archive failed")

        with py7zr.SevenZipFile(super().abspath, "w"):
            pass  # by putting pass here,
            # we effectively create an empty archive, and gracefully close it.

        return self.isarchive
