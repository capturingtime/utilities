from __future__ import annotations  # https://stackoverflow.com/a/55344418
from path import Path
from tqdm import tqdm
import os
import hashlib


# Add methods to convert between file/path and force file if only path called


class File(Path):
    """A Class to define a File, inherits Path"""

    def __init__(self, file: str):
        super().__init__(file)

        self.__sha256: str = str()

    @property
    def sha256(self) -> str:
        return self.__hash_sha256()

    def copy(self, dst: File, progress_bar: bool = False) -> bool:
        """Wrapper to branch a copy with or without a printed progress bar"""
        if not isinstance(dst, File):
            raise TypeError(f"dst must be type <class 'File'>. Provided: {type(dst)}")
        if super().isdir:
            raise IsADirectoryError("The source of the copy is a directory, not a file")
        # raise NotImplementedError
        if dst.exists:
            raise FileExistsError
        if progress_bar:
            self._copy_bar(dst)
        else:
            return self._copy(dst)

    def delete(self, confirm: bool = False) -> bool:
        """deletes the file from disk (destructive)"""
        if super().isdir:
            raise IsADirectoryError
        elif not super().exists:
            raise FileNotFoundError
        os.remove(super().abspath)
        # Returns True is file doesn't exist, and False if it still does
        return not super().exists

    def create(self) -> bool:
        """creates the file if it doesn't exist"""
        if super().exists:
            pass
        elif super().isdir:
            raise IsADirectoryError
        else:
            with open(super().abspath, "w"):
                pass  # write empty file and close
        return super().exists

    def mv(self, dst: File):
        """Move this file to the specified location"""
        if not isinstance(dst, File):
            raise TypeError(f"dst must be type <class 'File'>. Provided: {type(dst)}")
        pass
        # Update/re-init Path (i think?)

    def __hash_sha256(self) -> str:
        if not super().exists:
            raise FileNotFoundError
        with open(super().abspath, "rb") as f:
            self.__sha256 = hashlib.sha256(f.read()).hexdigest()
        return self.__sha256

    def _copy(self, dst: File) -> bool:
        """Copies a file to the specified location"""
        with open(super().abspath, "rb") as src:
            with open(dst.abspath, "ab") as dst:
                dst.write(src.read())

    def _copy_bar(self, dst: File) -> bool:
        """Copies a file to the specified location and outputs a progress bar"""
        fsize = super().size
        with open(super().abspath, "rb") as src:  # open src
            with open(dst.abspath, "ab") as dst:  # open dst
                with tqdm(  # Draws the Bar
                    ncols=60,
                    total=fsize,
                    bar_format="{l_bar}{bar} | Remaining: {remaining}",
                ) as pbar:
                    while True:
                        buf = src.read(8192)  # Read 8192 bytes
                        if len(buf) == 0:  # Check that there is still data to write
                            break
                        dst.write(buf)  # Write the the data that was read
                        pbar.update(len(buf))  # Update progressbar
