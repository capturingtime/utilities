from abc import ABC, abstractmethod
from typing import List

VALID_BUCKET_TYPES: List[str] = [
    "archive",  # This bucket is an actual archive with files for Long Term Storage
    "meta_archive",  # This bucket is for files that are related to archives, but not for LTS
    "standard",  # This bucket is just a standard bucket with no special considerations
]
DEFAULT_BUCKET_TYPE = "standard"


class Bucket(ABC):
    def __init__(self, name: str, bucket_type: str = DEFAULT_BUCKET_TYPE):
        self.__name = name
        self.__bucket_type = bucket_type

        if bucket_type not in VALID_BUCKET_TYPES:
            raise ValueError(
                f"bucket_type must be one of {VALID_BUCKET_TYPES}. Got: {bucket_type}"
            )

    @property
    def name(self):
        return self.__name

    @property
    def bucket_type(self):
        return self.__bucket_type

    @abstractmethod
    def get_item(self, key: str):
        raise NotImplementedError

    @abstractmethod
    def del_item(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def put_item(self, key: str, body: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def copy_item(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def rename_item(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_items(self) -> list:
        raise NotImplementedError
