from ...classes.abstract.cloud import Cloud
from .s3 import S3


class AWS(Cloud):
    cloud = "aws"

    def __init__(self):
        super().__init__(cloud=self.cloud)

        # Keyed by bucket name — allows callers to retrieve any registered bucket by name
        self.__buckets = dict()

    def load_bucket(self, name: str, **kwargs):
        """Instantiate an S3 bucket wrapper and register it by name.

        kwargs are forwarded to S3.__init__ / Bucket.__init__ (bucket_role, bucket_desc).
        Connecting to S3 and validating lifecycle config happens inside S3.__init__.
        """
        bucket = S3(name, **kwargs)
        self.__buckets.update({name: bucket})
        return bucket

    @property
    def list_buckets(self):
        return self.__buckets

    def get_bucket(self, bucket_name: str):
        return self.__buckets[bucket_name]
