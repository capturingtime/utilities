""" Start over with what you have learned and reorganize. This got away from you """

# from .bucket import Bucket
from .file import File
import boto3
import botocore

# import hashlib
from copy import copy

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-a-configuration-file
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
DEFAULT_CACHING: bool = True

TERRAFORM_BUCKET_CLASS_ID: str = "set_bucket_class"
BUCKET_TYPE_MAP: dict = {
    "archive": "GLACIER_IR",
    "meta_archive": "STANDARD_IA",
    "standard": None,
}

# The name of the File().property & ChecksumAlgorithm (AWS)
HASH_PROPERTY_NAME = "sha256"

GET_ATTR_TO_CONTENTS_MAP: dict = {
    # "{get_object_attributes[KeyName]}": "list_objects_v2["Contents"][KeyName]"
    "LastModified": "LastModified",
    "ETag": "ETag",
    "StorageClass": "StorageClass",
    "ObjectSize": "Size",
}




# class S3(Bucket):
    """A Class to define an S3 Bucket"""

    # def __init__(self, name: str, bucket_type: str):
    #     super().__init__(name=name, bucket_type=bucket_type)
        # self.__s3_obj = boto3.client("s3")
        self.__location: str = str()
        self.__lfc_cfg: list = list()

        # self.__objects: dict = dict()
        """Example Structure:
        dict({
            f"{object_key}": {
                "remote_object": Object(),  # Required
                "local_file": File(),  # Optional
                "uploaded_data": bytes  # Optional
            }
        })
        """

        self._check_bucket_exists()
        self._get_bucket_lfc_cfg()

    def _get_bucket_lfc_cfg(self) -> None:
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_lifecycle_configuration.html
            lfc_cfg = self.__s3_obj.get_bucket_lifecycle_configuration(
                Bucket=super().name
            )
        except botocore.exceptions.ClientError as err:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
            status = err.response["ResponseMetadata"]["HTTPStatusCode"]
            errcode = err.response["Error"]["Code"]
            if status == 404:
                print(f"Missing object, {errcode}: {err}")
            elif status == 403:
                print(f"Access denied, {errcode}: {err}")
            else:
                print(f"Error in request, {errcode}: {err}")
            # raise  # No raise, its ok if this fails.
        else:
            # Grabs list of bucket rules in the lifecycle config
            self.__lfc_cfg = lfc_cfg["Rules"]

        if super().bucket_type != "standard":
            result = False
            for rule in lfc_cfg["Rules"]:
                for t in rule["Transitions"]:
                    if t["StorageClass"] == BUCKET_TYPE_MAP.get(super().bucket_type):
                        result = True

            if not result:
                msg = f"bucket_type must be one of {BUCKET_TYPE_MAP.keys()} Got {super().bucket_type}"  # noqa: E501
                raise ValueError(msg)

    def _check_bucket_exists(self) -> None:
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_location.html
            loc = self.__s3_obj.get_bucket_location(Bucket=super().name)
        except botocore.exceptions.ClientError as err:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
            """# noqa: E501
            >>> err.response
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist', 'BucketName': 'fake-bucket-that-doesntexists'}, 'ResponseMetadata': {'RequestId': 'BSW7PX2A1FZNR1RV', 'HostId': 'NJYxjrdi8sBgzu4UnLrj6CcHHyQMdM95NExK0wZ+1j3GPSI+vtDmvHGlw0n1hDIAUrdSRxOU+WC/yQX7kZ24sA==', 'HTTPStatusCode': 404, 'HTTPHeaders': {'x-amz-request-id': 'BSW7PX2A1FZNR1RV', 'x-amz-id-2': 'NJYxjrdi8sBgzu4UnLrj6CcHHyQMdM95NExK0wZ+1j3GPSI+vtDmvHGlw0n1hDIAUrdSRxOU+WC/yQX7kZ24sA==', 'content-type': 'application/xml', 'transfer-encoding': 'chunked', 'date': 'Fri, 24 Mar 2023 00:38:20 GMT', 'server': 'AmazonS3'}, 'RetryAttempts': 0}}
            >>> err.operation_name
            'GetBucketLifecycleConfiguration'
            """
            status = err.response["ResponseMetadata"]["HTTPStatusCode"]
            errcode = err.response["Error"]["Code"]
            if status == 404:
                print(f"Missing object, {errcode}: {err}")
            elif status == 403:
                print(f"Access denied, {errcode}: {err}")
            else:
                print(f"Error in request, {errcode}: {err}")
            raise
        else:
            self.__location = loc["LocationConstraint"]

    def get_item(self, item: str):
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object.html
        # params: dict = {"Bucket": super().name, "Key": item}

        # response = self.__s3_obj.get_object(**params)
        key = item if isinstance(item, str) else str(item)
        if key not in self.__objects.keys():
            Obj = self.Object(bucket=self, key=key)
            Obj.refresh_data()
            self.__objects.update({key: {"remote_object": Obj}})
        return self.__objects[key]

    def del_item(self, item: str):
        raise NotImplementedError

    def put_item(self, item_key: str, item: [File, bytes, str]) -> bool:
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
        if isinstance(item, str):
            item = File(item)
            if not item.exists:
                raise FileNotFoundError("item as a str is assumed to be a filepath")

        item_key = item_key.strip("/")  # Data cleanup

        # CHECK IF EXISTS FIRST?
        # Do we allow 'put over put?'

        params: dict = {"Bucket": super().name, "Key": item_key}
        extra_args: dict = {
            "ChecksumAlgorithm": HASH_PROPERTY_NAME,
            # "Metadata": {}
        }

        result: bool = False
        if isinstance(item, File):
            result = self.__put_file(item, params, **extra_args)
        elif isinstance(item, bytes):
            result = self.__put_bytes(item, params, **extra_args)
        else:
            raise TypeError(
                f"item type must be one of {[File, bytes, str]} got: {type(item)}"
            )
        return result

    def copy_item(self):
        raise NotImplementedError

    def rename_item(self):
        raise NotImplementedError

    def list_items(self) -> list:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html
        # Should these results cache to an instance variable?
        params: dict = {
            "Bucket": super().name,
            "MaxKeys": 9999,
        }

        response = self.__s3_obj.list_objects_v2(**params)
        truncated: bool = response["IsTruncated"]
        objects: list = response["Contents"] if "Contents" in response else list()
        while truncated:
            # ctoken is a little wonkey logic wise, but reduces code.
            # ctoken is set after we know we need to request the 'next page', from the previous run
            ctoken: str = response["ContinuationToken"]
            response = self.__s3_obj.list_objects_v2(**params, ContinuationToken=ctoken)
            objects.extend(response["Contents"])
            truncated = response["IsTruncated"] if "IsTruncated" in response else False

        if len(objects) > 0:
            for o in objects:
                key = o["Key"]

                # Set cached attrs with the data we just got back
                # (Rather than pulling the data again for every object every time)
                attr_cache: dict = dict()

                # Loop through the attr map, and look for matches
                # If a match is found, update the attr_cache with the value of the found key
                # under the correct attr key expected by Object()
                for k, v in GET_ATTR_TO_CONTENTS_MAP:
                    if v in o.keys():
                        attr_cache.update({k: o[v]})

                # Check if we already have an Object() defined
                if key in self.__objects.keys():
                    # The Object() already exists, so lets ref to it
                    Obj = self.__objects[key]["remote_object"]
                else:
                    # If we don't already have an Object(), create it
                    Obj = self.Object(bucket=self, key=key)
                    self.__objects.update({key: {"remote_object": Obj}})

                Obj._attr_cache = attr_cache

        # Return cached list of keys
        return [v for v in self.__objects.keys()]

    def __put_file(self, file: File, params, **kwargs) -> bool:
        """Low Level Wrapper: boto3.client("s3").upload_file
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/upload_file.html
        """
        if not isinstance(file, File):
            raise TypeError
        upload_params = copy(params)
        upload_params.update(
            {
                "Filename": file.abspath,
                "ExtraArgs": {**kwargs},
            }
        )
        # params.update({"Callback": func})
        self.__s3_obj.upload_file(**upload_params)

        key = params["Key"]

        self.__objects.update(
            {
                key: {
                    "remote_object": self.Object(bucket=self, key=key),
                    "local_file": file,
                }
            }
        )
        return True

    def __put_bytes(self, item: bytes, params, **kwargs) -> bool:
        """Low Level Wrapper: boto3.client("s3").put_object()
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        """
        if not isinstance(item, bytes):
            raise TypeError
        upload_params = copy(params)
        upload_params.update({"Body": item, **kwargs})
        self.__s3_obj.put_object(**upload_params)

        key = params["Key"]

        self.__objects.update(
            {key: {"remote_object": self.Object(bucket=self, key=key), "data": item}}
        )
        return True

# class Object:
#     """A Class to define an S3 Object"""

#     def __init__(self, bucket: Bucket, key: str, caching: bool = DEFAULT_CACHING):
#         if not isinstance(bucket, Bucket):
#             raise TypeError(
#                 f"bucket type must contain {[Bucket]} got: {type(bucket)}"
#             )
#         self.__bucket = bucket
#         self.__caching: bool = bool(caching)
#         self.__data: dict = dict()
#         self.__key: str = str(key)
#         self.__attr_cache: dict = dict()

#     @property
#     def bucket(self):
#         return self.__bucket

#     @property
#     def caching(self) -> dict:
#         """Determines whther attribute data is cached or fetched each time"""
#         return self.__caching

#     @property
#     def Checksum(self) -> dict:
#         return dict(self.__resolve_attr("Checksum"))

#     @property
#     def data(self) -> dict:
#         if not self.__data or not self.__caching:
#             self.refresh_data()
#         return dict(self.__data)

#     @property
#     def DeleteMarker(self) -> bool:
#         return bool(self.__resolve_attr("DeleteMarker"))

#     @property
#     def ETag(self) -> str:
#         return str(self.__resolve_attr("ETag"))

#     @property
#     def key(self):
#         return self.__key

#     @property
#     def LastModified(self) -> datetime:
#         return self.__resolve_attr("LastModified")

#     @property
#     def ObjectParts(self) -> dict:
#         return dict(self.__resolve_attr("ObjectParts"))

#     @property
#     def ObjectSize(self) -> int:
#         return int(self.__resolve_attr("ObjectSize"))

#     @property
#     def RequestCharged(self) -> str:
#         return str(self.__resolve_attr("RequestCharged"))

#     @property
#     def StorageClass(self) -> str:
#         return str(self.__resolve_attr("StorageClass"))

#     @property
#     def VersionId(self) -> str:
#         return str(self.__resolve_attr("VersionId"))

    # @property
    # def _attr_cache(self) -> dict:
    #     """Returns cached attr data"""
    #     return self.__attr_cache

    # @_attr_cache.setter
    # def _attr_cache(self, **kwargs) -> bool:
    #     """A setter method intended to give the ability to manually set attr data.
    #     Not inteded for operators to call, assumes confidence in data provided
    #     """
    #     self.__attr_cache.update(kwargs)
    #     return True

    # def refresh_attrs(self) -> bool:
    #     """Manual refresh of attributes. Useful when self.__caching is True"""
    #     return self.__get_object_attributes()

    # def refresh_data(self) -> bool:
    #     """Manual refresh of data. Useful when self.__caching is True"""
    #     params: dict = {"Bucket": self.__bucket, "Key": self.__key}
    #     self.__bucket.get_object(**params)
    #     return True

    # def toggle_caching(self) -> None:
    #     """Returns None because any bool response could be confused between:
    #     Successful Change / Current State
    #     Confirming cache mode can be done via the cache param
    #     """
    #     self.__caching = not self.__caching  # bool negation
    #     return None

    # def __get_object_attributes(self) -> bool:
    #     """Low Level Wrapper: boto3.client("s3").get_object_attributes
    #     https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object_attributes.html
    #     """
    #     # get_kwargs: dict = {
    #     #     "Bucket": self.__bucket,
    #     #     "Key": self.__key,
    #     #     "ObjectAttributes": VALID_OBJECT_REQUEST_ATTRIBUTES,
    #     # }
    #     try:
    #         self.__attr_cache = self.__bucket.get_item_details(**get_kwargs)
    #     except Exception as err:
    #         raise err
    #     else:
    #         return True

    # def __resolve_attr(self, attr):
    #     """A DRY func to return an attr from the self.__attr_cache dict"""

    #     # Check for conditions resulting in the need to pull attributes
    #     if (not self.__attr_cache or not self.__caching) or (
    #         attr not in self.__attr_cache
    #         and attr in VALID_OBJECT_RESPONSE_ATTRIBUTES
    #     ):
    #         self.__get_object_attributes()

    #     if attr in self.__attr_cache:
    #         return self.__attr_cache[attr]
    #     elif attr in VALID_OBJECT_RESPONSE_ATTRIBUTES:
    #         raise ValueError(
    #             f"The requested object attribute ({attr}) is valid, "
    #             "but not found in the object's attributes"
    #         )
    #     else:
    #         raise ValueError(
    #             f"The requested object attribute ({attr}) must be one of "
    #             f"{VALID_OBJECT_RESPONSE_ATTRIBUTES}"
    #         )
