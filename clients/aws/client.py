from ...classes.abstract.cloud import Cloud
from .s3 import S3

# archive_raw = ("ctp-archive-raw", "archive")
# archive_preview = ("ctp-archive-preview", "meta_archive")
# archive_thumb = ("ctp-archive-thumb", "meta_archive")
# archive_sidecar = ("ctp-archive-sidecar", "meta_archive")


class AWS(Cloud):
    cloud = "aws"

    def __init__(self):
        super().__init__(cloud=self.cloud)

        self.__buckets = dict()

        # self.archive_raw = self.load_bucket(*archive_raw)
        # self.archive_preview = self.load_bucket(*archive_preview)
        # self.archive_thumb = self.load_bucket(*archive_thumb)
        # self.archive_sidecar = self.load_bucket(*archive_sidecar)

    def load_bucket(self, name: str, **kwargs):
        bucket = S3(name, **kwargs)
        self.__buckets.update({name: bucket})
        return bucket

    @property
    def list_buckets(self):
        return self.__buckets

    def get_bucket(self, bucket_name: str):
        return self.__buckets[bucket_name]
