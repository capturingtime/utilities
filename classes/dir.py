from __future__ import annotations  # https://stackoverflow.com/a/55344418

import os
from .path import Path


class Dir(Path):
    """A Class to define a Directory, inherits Path"""

    def __init__(self, directory: str):
        super().__init__(directory)

    # @property
    # def directory(self):
    #     return super().abspath

    # @property
    # def dirname(self) -> str:
    #     return super().basename

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

    def create(self, p: bool = True, **kwargs) -> bool:
        """creates the directory if it doesn't exist"""
        if super().exists and not p:
            raise FileExistsError
        elif super().exists and p:
            pass
        else:
            os.mkdir(super().abspath, **kwargs)
        return super().exists

    def mv(self):
        raise NotImplementedError
