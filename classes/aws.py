from .cloud import Cloud
from .s3 import S3


class AWS(Cloud):

    # Required attributes for Cloud()
    raw_archive = S3("ctp_raw_archive")
    preview_archive = S3("ctp_preview_archive")
    thumb_archive = S3("ctp_thumb_archive")
    sidecar_archive = S3("ctp_sidecar_archive")

    def __init__(self):
        super().__init__(cloud="aws")
