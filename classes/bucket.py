from abc import ABC, abstractmethod


class Bucket(ABC):

    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self):
        return self.__name

    @abstractmethod
    def get_item(self):
        pass

    @abstractmethod
    def del_item(self):
        pass

    @abstractmethod
    def put_item(self):
        pass
