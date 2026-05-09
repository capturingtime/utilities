from .bucketitem import BucketItem
import boto3
from botocore.response import StreamingBody
from datetime import datetime


DEFAULT_CACHING: bool = True

VALID_OBJECT_REQUEST_ATTRIBUTES: list = [
    "Checksum",
    "ETag",
    "ObjectParts",
    "ObjectSize",
    "StorageClass",
]

VALID_OBJECT_RESPONSE_ATTRIBUTES: list = list(
    set(
        ["DeleteMarker", "LastModified", "VersionId", "RequestCharged"]
        + VALID_OBJECT_REQUEST_ATTRIBUTES
    )
)


class Object(BucketItem):
    """A Class to define an S3 Object"""

    def __init__(self, bucket: str, key: str, caching: bool = DEFAULT_CACHING):
        super().__init__(item=key)
        self.__obj_attrs: dict = dict()
        self.__bucket: str = bucket
        self.__caching: bool = bool(caching)
        self.__data: StreamingBody = StreamingBody
        self.__exists: bool = False
        self.__key: str = str(key)
        self.__last_response_meta: dict = dict()
        self.__last_update: datetime = datetime.now()
        self.__s3_client = boto3.client("s3")

    @property
    def data(self) -> dict:
        if not self.__data or not self.__caching:
            self.refresh_data()
        return dict({"data": self.__data})

    @property
    def metadata(self) -> dict:
        if not self.__data or not self.__caching:
            self.refresh_data()
        return dict(self.__obj_attrs)

    @property
    def caching(self) -> dict:
        """Determines whther attribute data is cached or fetched each time"""
        return self.__caching

    @property
    def exists(self) -> bool:
        return self.__get_object_attributes()

    @property
    def Checksum(self) -> dict:
        return dict(self.__resolve_attr("Checksum"))

    @property
    def DeleteMarker(self) -> bool:
        return bool(self.__resolve_attr("DeleteMarker"))

    @property
    def ETag(self) -> str:
        return str(self.__resolve_attr("ETag"))

    @property
    def key(self):
        return self.__key

    @property
    def LastModified(self) -> datetime:
        return self.__resolve_attr("LastModified")

    @property
    def cache_updated_at(self) -> datetime:
        return self.__last_update

    @property
    def ObjectParts(self) -> dict:
        return dict(self.__resolve_attr("ObjectParts"))

    @property
    def ObjectSize(self) -> int:
        return int(self.__resolve_attr("ObjectSize"))

    @property
    def RequestCharged(self) -> str:
        return str(self.__resolve_attr("RequestCharged"))

    @property
    def StorageClass(self) -> str:
        return str(self.__resolve_attr("StorageClass"))

    @property
    def VersionId(self) -> str:
        return str(self.__resolve_attr("VersionId"))

    def refresh_data(self) -> bool:
        """Manual refresh of data. Useful when self.__caching is True"""
        params: dict = {"Bucket": self.__bucket, "Key": self.__key}

        try:
            self.__get_object_attributes()
            response = self.__s3_client.get_object(**params)
            self.__update_cache_ds()
        except Exception as err:
            raise err
        else:
            self.__last_response_meta = response.pop("ResponseMetadata")
            self.__data = response.pop("Body")
            for k, v in response.items():
                self.__obj_attrs[k] = v
            return True

    def __update_cache_ds(self) -> bool:
        """Datestamp updater fun"""
        self.__last_update = datetime.now()

    def __get_object_attributes(self) -> bool:
        """Low Level Wrapper: boto3.client("s3").get_object_attributes
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object_attributes.html
        """
        get_kwargs: dict = {
            "Bucket": self.__bucket,
            "Key": self.__key,
            "ObjectAttributes": VALID_OBJECT_REQUEST_ATTRIBUTES,
        }
        try:
            response = self.__s3_client.get_object_attributes(**get_kwargs)
        except Exception as err:
            raise err
        else:
            self.__last_response_meta = response.pop("ResponseMetadata")
            for k, v in response.items():
                self.__obj_attrs[k] = v
            return True

    def __resolve_attr(self, attr):
        """A DRY func to return an attr from the self.__obj_attrs dict"""

        # Check for conditions resulting in the need to pull attributes
        if (not self.__obj_attrs or not self.__caching) or (
            attr not in self.__obj_attrs and attr in VALID_OBJECT_RESPONSE_ATTRIBUTES
        ):
            self.__get_object_attributes()

        if attr in self.__obj_attrs:
            return self.__obj_attrs[attr]
        elif attr in VALID_OBJECT_RESPONSE_ATTRIBUTES:
            raise ValueError(
                f"The requested object attribute ({attr}) is valid, "
                "but not found in the object's attributes"
            )
        else:
            raise ValueError(
                f"The requested object attribute ({attr}) must be one of "
                f"{VALID_OBJECT_RESPONSE_ATTRIBUTES}"
            )

    def toggle_caching(self) -> None:
        """Returns None because any bool response could be confused between:
        Successful Change / Current State
        Confirming cache mode can be done via the cache param
        """
        self.__caching = not self.__caching  # bool negation
        return None
