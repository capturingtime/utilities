from __future__ import annotations  # https://stackoverflow.com/a/55344418
import os
from tqdm import tqdm


class Path:
    """A Class to define a Path, inherited by File, Dir"""

    def __init__(self, path: str):
        self.__path: str = path

    @property
    def path(self):
        return self.__path

    @property
    def abspath(self) -> str:
        return os.path.abspath(self.__path)

    @property
    def basename(self) -> str:
        return os.path.basename(self.__path)

    @property
    def dirname(self) -> str:
        return os.path.dirname(self.__path)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.__path)

    @property
    def isdir(self) -> bool:
        return os.path.isdir(self.__path)

    @property
    def isfile(self) -> bool:
        return os.path.isfile(self.__path)

    @property
    def realpath(self) -> str:
        return os.path.realpath(self.__path)

    @property
    def relpath(self) -> str:
        return os.path.relpath(self.__path)

    @property
    def size(self) -> int:
        return os.path.getsize(self.__path)


class File(Path):
    """A Class to define a File, inherits Path"""

    def __init__(self, file: str):
        super().__init__(file)

    @property
    def file(self):
        return super().abspath

    @property
    def filename(self) -> str:
        return super().basename

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

    def touch(self) -> bool:
        """makes the file if it doesn't exist"""
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


class Dir(Path):
    """A Class to define a Directory, inherits Path"""

    def __init__(self, directory: str):
        super().__init__(directory)

    @property
    def directory(self):
        return super().abspath

    @property
    def dirname(self) -> str:
        return super().basename

    # make this similar to File.copy()
    def copy(self, dst: Dir) -> bool:
        """Copies a directory recursively to the specified location"""
        if not isinstance(dst, Dir):
            raise TypeError(f"dst must be type <class 'Dir'>. Provided: {type(dst)}")
        if not super().isdir:
            raise NotADirectoryError("The source of the copy is not a directory")
        raise NotImplementedError
        # return File(dst)

    def delete(self, confirm: bool = False) -> bool:
        """deletes the file from disk (destructive)"""
        if not super().isdir:
            raise NotADirectoryError
        elif not super().exists:
            raise FileNotFoundError
        os.rmdir(super().abspath)
        # Returns True is file doesn't exist, and False if it still does
        return not super().exists

    def mkdir(self, p: bool = False, **kwargs) -> bool:
        """makes the directory if it doesn't exist"""
        if super().exists and not p:
            raise FileExistsError
        elif super().exists and p:
            pass
        else:
            os.mkdir(super().abspath, **kwargs)
        return super().exists
