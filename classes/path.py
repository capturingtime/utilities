from abc import ABC, abstractmethod
import os

class Path(ABC):
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

    @abstractmethod
    def copy(self):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def mv(self):
        pass