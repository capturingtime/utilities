from ..path.file import File
from ..path.dir import Dir
import py7zr
import logging
from yaspin import yaspin, Spinner


spin = Spinner(["\\", "|", "/", "-"], 250)


class Archive(File):
    """A Class to define an Archive, inherits File"""

    def __init__(
        self, archive: str, logger: logging.Logger = logging.getLogger(__name__)
    ):
        super().__init__(archive)

        self.archive = super().abspath
        self.py7zr = py7zr

    @property
    def isarchive(self) -> bool:
        """Returns True only if the file exists and py7zr can open it as a valid 7z archive."""
        if not super().exists:
            return False
        try:
            a: str = getattr(
                py7zr.SevenZipFile(super().abspath, "r"), "filename", str()
            )
        except (FileNotFoundError, OSError, py7zr.Bad7zFile):
            # Bad7zFile is raised by newer py7zr versions for corrupted/non-archive files;
            # it does not inherit from OSError so must be caught separately
            return False
        return True if a else False

    def check_crc(self) -> [str, None]:
        """checks if there are CRC errors in the archive"""
        if self.isarchive:
            return py7zr.SevenZipFile(super().abspath, "r").testzip()
        else:
            raise FileExistsError("File exists and is not an archive")

    def extract(
        self,
        dst: Dir,
        file_list: list = list(),
    ) -> bool:
        """Extracts the contents of this archive (if exists) to the destination directory"""
        if not isinstance(dst, Dir):
            raise TypeError(f"dst must be type {type(Dir)}. Provided: {type(dst)}")
        if not dst.isdir:
            raise NotADirectoryError

        with yaspin(
            spin, text="Extracting Archive...", color="cyan", timer=True
        ) as spinner:
            with py7zr.SevenZipFile(super().abspath, "r") as a:
                extract_list = list(file_list if file_list else a.getnames())
                a._extract(
                    path=dst.directory,
                    targets=extract_list,
                )
            spinner.ok()

        return dst.exists

    def add(
        self,
        src: list([Dir, File]),
        folder_name: str = str(),
    ) -> bool:
        """Adds a File or Dir to this archive"""
        type_err_msg = (
            "src must be a list with elements of "
            f"type {Dir} or {File}. Provided: {type(src)}"
        )
        if not isinstance(src, list):
            if isinstance(src, (Dir, File)):
                src = list([src])
            else:
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
        with yaspin(
            spin, text="Adding files to Archive...", color="cyan", timer=True
        ) as spinner:
            # "a" = append; "w" would truncate the archive on every call
            with py7zr.SevenZipFile(super().abspath, "a") as a:
                for f in src:
                    prefix = f"{folder_name}/" if folder_name else ""

                    if type(f) == File:
                        a.write(f.abspath, f"{prefix}{f.basename}")
                    elif type(f) == Dir:
                        a.writeall(f.abspath, f"{prefix}{f.basename}")
                    else:
                        raise TypeError(type_err_msg)
            spinner.ok()

        return True

    def _create(self) -> bool:
        """Creates the archive if it doesn't already exist"""
        if self.isarchive:
            return True
        if super().exists:
            # A file exists at this path but is not a valid archive — refuse to overwrite
            raise FileExistsError("An attempt to create a non-existant archive failed")

        with py7zr.SevenZipFile(super().abspath, "w"):
            pass  # open in write mode and immediately close to produce an empty archive

        return self.isarchive
