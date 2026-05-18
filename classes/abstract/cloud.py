from abc import ABC, abstractmethod


DEFAULT_CLOUD = "Unknown Cloud Provider"


class Cloud(ABC):
    def __init__(self, cloud: str = DEFAULT_CLOUD):
        self.__cloud = cloud

    def __init_subclass__(cls):
        """Hook called when a subclass is defined.
        https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__
        Reserved for future enforcement of required bucket attributes on subclasses.
        """
        pass

    @property
    def cloud(self):
        return self.__cloud

    @abstractmethod
    def load_bucket(self, name: str, bucket_role: str):
        raise NotImplementedError
