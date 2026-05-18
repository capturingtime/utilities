from abc import ABC, abstractmethod
from typing import List

# Roles map to S3 storage class tiers defined in BUCKET_ROLE_MAP in clients/aws/s3.py.
# Validated on Bucket construction so misconfiguration fails fast at init, not on first upload.
VALID_BUCKET_ROLES: List[str] = [
    "archive",  # RAW image files — long-term cold storage (GLACIER_IR)
    "meta_archive",  # Previews, thumbnails, sidecars — infrequently accessed (STANDARD_IA)
    "standard",  # General-purpose; no storage-class lifecycle enforced
]
DEFAULT_BUCKET_ROLE = "standard"


class Bucket(ABC):
    def __init__(
        self,
        name: str,
        bucket_role: str = DEFAULT_BUCKET_ROLE,
        bucket_desc: str = "A Bucket to store files",
    ):
        self.__name = name
        self.__bucket_role = bucket_role
        self.__bucket_desc = bucket_desc

        if bucket_role not in VALID_BUCKET_ROLES:
            raise ValueError(
                f"bucket_role must be one of {VALID_BUCKET_ROLES}. Got: {bucket_role}"
            )

    @property
    def name(self):
        return self.__name

    @property
    def bucket_role(self):
        return self.__bucket_role

    @property
    def bucket_desc(self):
        return self.__bucket_desc

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
