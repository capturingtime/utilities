from __future__ import annotations  # https://stackoverflow.com/a/55344418

import os
from ..abstract.path import Path


class Dir(Path):
    """A Class to define a Directory, inherits Path"""

    def __init__(self, directory: str):
        super().__init__(directory)

    def copy(self, dst: Dir) -> bool:
        """Copies a directory recursively to the specified location"""
        if not isinstance(dst, Dir):
            raise TypeError(f"dst must be type <class 'Dir'>. Provided: {type(dst)}")
        if not super().isdir:
            raise NotADirectoryError("The source of the copy is not a directory")
        raise NotImplementedError

    def delete(self, confirm: bool = False) -> bool:
        """deletes the directory from disk (destructive, directory must be empty)"""
        if not super().exists:
            raise FileNotFoundError
        elif not super().isdir:
            raise NotADirectoryError
        os.rmdir(super().abspath)
        return not super().exists

    def create(self, p: bool = True, **kwargs) -> bool:
        """creates the directory if it doesn't exist.

        p=True (default) behaves like mkdir -p: creates all missing parent directories.
        p=False raises FileExistsError if the directory already exists.
        """
        if p:
            # makedirs is equivalent to mkdir -p: creates all missing parents
            os.makedirs(super().abspath, exist_ok=True, **kwargs)
        elif super().exists:
            raise FileExistsError
        else:
            os.mkdir(super().abspath, **kwargs)
        return super().exists

    def mv(self):
        raise NotImplementedError
