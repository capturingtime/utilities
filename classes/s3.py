from .bucket import Bucket
import boto3
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-a-configuration-file


class S3(Bucket):
    def __init__(self, name: str):
        super().__init__(name=name)
        self._bucket_obj = boto3.client('s3')

    def get_item(self):
        print("pass: get_obj")

    def del_item(self):
        print("pass: del_obj")

    def put_item(self):
        print("pass: put_obj")
