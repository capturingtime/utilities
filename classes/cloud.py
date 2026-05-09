from abc import ABC, abstractmethod
from .bucket import Bucket


DEFAULT_CLOUD = "aws"

REQUIRED_ATTRIBUTE_TYPES: dict = {
    "archive_raw": Bucket,
    "archive_preview": Bucket,
    "archive_thumb": Bucket,
    "archive_sidecar": Bucket,
}


class Cloud(ABC):
    def __init__(self, cloud: str = DEFAULT_CLOUD):
        self.__cloud = cloud

    def __init_subclass__(cls):
        """https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__"""

        # original
        # # Loop through the dict and check the subclass's attributes types
        # for attr_name, attr_type in REQUIRED_ATTRIBUTE_TYPES.items():
        #     cls_attr = getattr(cls, attr_name, None)
        #     if not isinstance(cls_attr, attr_type):
        #         raise TypeError(
        #             f"Class {cls.__name__}.{attr_name} must be type {Bucket}. "
        #             f"Got: {type(cls_attr)}"
        #         )
        pass

    @property
    def cloud(self):
        return self.__cloud

    @abstractmethod
    def load_bucket(self, name: str, bucket_type: str):
        raise NotImplementedError

    # @property
    # @abstractmethod
    # def archive_raw(self):
    #     raise NotImplementedError

    # @property
    # @abstractmethod
    # def archive_preview(self):
    #     raise NotImplementedError

    # @property
    # @abstractmethod
    # def archive_thumb(self):
    #     raise NotImplementedError

    # @property
    # @abstractmethod
    # def archive_sidecar(self):
    #     raise NotImplementedError
