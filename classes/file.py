import os


class File:
    def __init__(self, f: str):
        self.__f: str = f

    @property
    def f(self):
        return self.__f

    @property
    def abspath(self) -> str:
        return os.path.abspath(self.__f)

    @property
    def basename(self) -> str:
        return os.path.basename(self.__f)

    @property
    def dirname(self) -> str:
        return os.path.dirname(self.__f)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.__f)

    @property
    def isdir(self) -> bool:
        return os.path.isdir(self.__f)

    @property
    def isfile(self) -> bool:
        return os.path.isfile(self.__f)

    @property
    def realpath(self) -> str:
        return os.path.realpath(self.__f)

    @property
    def relpath(self) -> str:
        return os.path.relpath(self.__f)

    @property
    def size(self) -> int:
        return os.path.getsize(self.__f)

    def __str__(self):
        return str(self.__f)

    def copy(self, dst) -> bool:
        """Copies a file to the specified location"""
        if self.isdir:
            raise IsADirectoryError
        raise NotImplementedError
        # return File(dst)

    def delete(self, confirm: bool = False) -> bool:
        """deletes the file from disk (destructive)"""
        if self.isdir:
            raise IsADirectoryError
        raise NotImplementedError

    def touch(self) -> bool:
        """makes the file if it doesn't exist"""
        if self.exists:
            pass
        elif self.isdir:
            raise IsADirectoryError
        else:
            with open(self.f, "w"):
                pass  # write empty file and close
        return self.exists


class Dir(File):
    def __init__(self, d: str):
        super().__init__(d)

    @property
    def d(self):
        return self.f

    def copy_recursive(self, dst) -> bool:
        """Copies a directory recursively to the specified location"""
        if self.isfile:
            raise NotADirectoryError
        raise NotImplementedError
        # return File(dst)

    def delete(self, confirm: bool = False) -> bool:
        """deletes the file from disk (destructive)"""
        if self.isfile:
            raise NotADirectoryError
        raise NotImplementedError

    def mkdir(self, p: bool = False, **kwargs) -> bool:
        """makes the directory if it doesn't exist"""
        if self.exists and not p:
            raise FileExistsError
        elif self.exists and p:
            pass
        else:
            os.mkdir(self.d, **kwargs)
        return self.exists
