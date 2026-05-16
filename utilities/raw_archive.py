from ..clients.aws.client import AWS

# from ..clients.archive.client import ??

archive_raw = (
    "ctp-archive-raw",
    "archive",
    "An archive utility, containing RAW binary image files",
)
archive_preview = ("ctp-archive-preview", "meta_archive", "")
archive_thumb = ("ctp-archive-thumb", "meta_archive", "")
archive_sidecar = ("ctp-archive-sidecar", "meta_archive", "")

aws = AWS()
aws.load_bucket(*archive_raw)
