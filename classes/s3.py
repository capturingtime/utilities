from bucket import Bucket
from file import File
from object import Object
from botocore.exceptions import (
    ClientError,
)
import boto3
from copy import copy

BUCKET_TYPE_MAP: dict = {
    "archive": "GLACIER_IR",
    "meta_archive": "STANDARD_IA",
    "standard": None,
}

# The name of the File().property & ChecksumAlgorithm (AWS)
HASH_PROPERTY_NAME = "sha256"


class S3(Bucket):
    """A Class to define an S3 Bucket"""

    def __init__(self, name: str, bucket_type: str):
        super().__init__(name=name, bucket_type=bucket_type)
        self.__lfc_cfg: list = list()
        self.__location: str = str()
        self.__objects: dict = dict()
        self.__s3_client = boto3.client("s3")

        self._check_bucket_exists()
        self._get_bucket_lfc_cfg()

    def __define_object(self, key: str, fetch_data: bool = False) -> Object:
        """Defines an object data entry into the cache"""
        key = str(key)
        entry: dict = {
            key: {
                "object": Object(bucket=super().name, key=key),
                "file": None,
                "raw_bytes": bytes,
            }
        }
        self.__objects.update(entry)

        if fetch_data:
            entry[key]["object"].refresh_data()
        return entry[key]["object"]

    def _get_bucket_lfc_cfg(self) -> None:
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_lifecycle_configuration.html
            lfc_cfg = self.__s3_client.get_bucket_lifecycle_configuration(
                Bucket=super().name
            )
        except ClientError as err:
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
            loc = self.__s3_client.get_bucket_location(Bucket=super().name)
        except ClientError as err:
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

    def get_item(self, key: str) -> Object:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object.html
        key = key if isinstance(key, str) else str(key)
        if key not in self.__objects.keys():
            self.__define_object(key, fetch_data=True)
        return self.__objects[key]["object"]

    def del_item(self, key: str):
        raise NotImplementedError

    def copy_item(self):
        raise NotImplementedError

    def rename_item(self):
        raise NotImplementedError

    def put_item(self, key: str, body: [File, bytes, str], force: bool = False) -> bool:
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
        if isinstance(body, str):
            body = File(body)
            if not body.exists:
                raise FileNotFoundError("body as a str is assumed to be a filepath")

        key = key.strip("/")  # Data cleanup

        """Validation and parity checking"""
        exists = False
        if key in self.__objects.keys():
            try:
                self.__objects[key]["object"].exists
            except Exception:
                exists = False
        else:
            try:
                self.get_item(key)
            except Exception:
                exists = False

        if exists and not force:
            # force = True signifies to take the dangerous action of forcefully overwritting
            raise Exception(
                f"The specified S3 Object exists and force is False ({key})"
            )

        # implicit else:
        params: dict = {"Bucket": super().name, "Key": key}
        extra_args: dict = {
            "ChecksumAlgorithm": HASH_PROPERTY_NAME,
            # "Metadata": {}
        }

        result: bool = False
        if isinstance(body, File):
            result = self.__put_file(body, params, **extra_args)
        elif isinstance(body, bytes):
            result = self.__put_bytes(body, params, **extra_args)
        else:
            raise TypeError(
                f"body type must be one of {[File, bytes, str]} got: {type(body)}"
            )
        return result

    def list_items(self) -> list:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html
        params: dict = {
            "Bucket": super().name,
            "MaxKeys": 9999,
        }

        response = None
        try:
            response = self.__s3_client.list_objects_v2(**params)
            truncated: bool = response["IsTruncated"]
            contents: list = response["Contents"] if "Contents" in response else list()
        except Exception as err:
            raise err

        while truncated:
            # ctoken is a little wonkey logic wise, but reduces code.
            # ctoken is set after we know we need to request the 'next page', from the previous run
            ctoken: str = response["ContinuationToken"]
            response = self.__s3_client.list_objects_v2(
                **params, ContinuationToken=ctoken
            )
            contents.extend(response["Contents"])
            truncated = response["IsTruncated"] if "IsTruncated" in response else False

        # resolve locally known vs remotely known objects
        remote_keys: list = list()
        if len(contents) > 0:
            # Make sure we know about any remote objects
            for c in contents:
                key = c["Key"]
                remote_keys.append(key)

                # Check if we already have an Object() defined
                if key not in self.__objects.keys():
                    self.__define_object(key)

            # Check if we have erroneous local objects (deleted remotely somehow) and delete them
            for k in self.__objects.keys():
                if k not in remote_keys:
                    del self.__objects[k]
                    print(
                        f"A local object with key: {k} was not found in the remote list, deleting"
                    )
        else:
            # There are no remote objects, so we should have zero locally
            self.__objects = dict()

        # Return local list of keys
        return [k for k in self.__objects.keys()]
