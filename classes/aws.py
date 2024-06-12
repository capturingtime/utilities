from cloud import Cloud
from s3 import S3

archive_raw = ("ctp-archive-raw", "archive")
archive_preview = ("ctp-archive-preview", "meta_archive")
archive_thumb = ("ctp-archive-thumb", "meta_archive")
archive_sidecar = ("ctp-archive-sidecar", "meta_archive")


class AWS(Cloud):
    cloud = "aws"

    # This lags when importing because being a class parameter, instantiation happens at import
    # There is likely a better way.
    #

    # original
    # archive_raw = S3("ctp-archive-raw", "archive")
    # archive_preview = S3("ctp-archive-preview", "meta_archive")
    # archive_thumb = S3("ctp-archive-thumb", "meta_archive")
    # archive_sidecar = S3("ctp-archive-sidecar", "meta_archive")

    def __init__(self):
        super().__init__(cloud=self.cloud)

        self.__buckets = dict()

        self.archive_raw = self.load_bucket(*archive_raw)
        self.archive_preview = self.load_bucket(*archive_preview)
        self.archive_thumb = self.load_bucket(*archive_thumb)
        self.archive_sidecar = self.load_bucket(*archive_sidecar)

    def load_bucket(self, name: str, bucket_type: str):
        # "bucket_type" really should be something like "bucket_role" as
        # type refers to a property inherent to the bucket and role refers
        # to how this package uses it.
        bucket = S3(name, bucket_type)
        self.__buckets.update({name: bucket})
        return bucket

    @property
    def get_buckets(self):
        return self.__buckets
