from abc import ABC, abstractmethod


class BucketItem(ABC):
    def __init__(self, item: str):
        # item is the object key — the full path within the bucket (e.g. "shoots/2024/img.jpg")
        self.__item = item

    @property
    def item(self):
        return self.__item

    @property
    def exists(self) -> bool:
        """Return a bool indicating if the object exists"""
        raise NotImplementedError

    @property
    @abstractmethod
    def data(self):
        """Return the object's data"""
        raise NotImplementedError

    @property
    @abstractmethod
    def metadata(self):
        """Return the object's metadata"""
        raise NotImplementedError
