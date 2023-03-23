
from abc import ABC, abstractmethod
from .bucket import Bucket


DEFAULT_CLOUD = "aws"

REQUIRED_ATTRIBUTE_TYPES: dict = {
    "raw_archive": Bucket,
    "preview_archive": Bucket,
    "thumb_archive": Bucket,
    "sidecar_archive": Bucket,
}


class Cloud(ABC):

    def __init__(self, cloud: str = DEFAULT_CLOUD):
        self.__cloud = cloud

    def __init_subclass__(cls):
        """ https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__ """

        # Loop through the dict and check the subclass's attributes types
        for attr_name, attr_type in REQUIRED_ATTRIBUTE_TYPES.items():
            cls_attr = getattr(cls, attr_name, None)
            if not isinstance(cls_attr, attr_type):
                raise TypeError(
                    f"Class {cls.__name__}.{attr_name} must be type {Bucket}. "
                    f"Got: {type(cls_attr)}"
                )

    @property
    def cloud(self):
        return self.__cloud

    @property
    @abstractmethod
    def raw_archive(self):
        pass

    @property
    @abstractmethod
    def preview_archive(self):
        pass

    @property
    @abstractmethod
    def thumb_archive(self):
        pass

    @property
    @abstractmethod
    def sidecar_archive(self):
        pass
