"""Tests for AWS client layer — boto3 calls are fully mocked."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from botocore.exceptions import ClientError

from utilities.classes.abstract.bucket import VALID_BUCKET_ROLES
from utilities.clients.aws.object import Object, VALID_OBJECT_REQUEST_ATTRIBUTES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client_error(code: str, status: int) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": "msg"}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "TestOperation",
    )


def _make_object(bucket="test-bucket", key="test/key.jpg", caching=True) -> Object:
    with patch("utilities.clients.aws.object.boto3.client"):
        return Object(bucket=bucket, key=key, caching=caching)


# ---------------------------------------------------------------------------
# Object tests
# ---------------------------------------------------------------------------


class TestObject:
    def test_key_property(self):
        obj = _make_object(key="folder/image.cr2")
        assert obj.key == "folder/image.cr2"

    def test_item_property_matches_key(self):
        obj = _make_object(key="some/key")
        assert obj.item == "some/key"

    def test_caching_default_true(self):
        obj = _make_object()
        assert obj.caching is True

    def test_toggle_caching_flips_state(self):
        obj = _make_object()
        obj.toggle_caching()
        assert obj.caching is False
        obj.toggle_caching()
        assert obj.caching is True

    def test_toggle_caching_returns_none(self):
        obj = _make_object()
        assert obj.toggle_caching() is None

    def test_exists_calls_get_object_attributes(self):
        with patch("utilities.clients.aws.object.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_object_attributes.return_value = {
                "ResponseMetadata": {},
                "ObjectSize": 1024,
            }
            obj = Object(bucket="b", key="k")
            result = obj.exists
            assert result is True
            mock_s3.get_object_attributes.assert_called_once()

    def test_refresh_data_fetches_object(self):
        with patch("utilities.clients.aws.object.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_object_attributes.return_value = {
                "ResponseMetadata": {},
                "ObjectSize": 512,
            }
            mock_s3.get_object.return_value = {
                "ResponseMetadata": {},
                "Body": b"data",
                "ContentType": "image/jpeg",
            }
            obj = Object(bucket="b", key="k")
            result = obj.refresh_data()
            assert result is True
            mock_s3.get_object.assert_called_once_with(Bucket="b", Key="k")


# ---------------------------------------------------------------------------
# S3 bucket tests (mocked boto3)
# ---------------------------------------------------------------------------


class TestS3BucketInit:
    def test_raises_on_missing_bucket(self):
        from utilities.clients.aws.s3 import S3

        with patch("utilities.clients.aws.s3.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_bucket_location.side_effect = _client_error("NoSuchBucket", 404)

            with pytest.raises(ClientError):
                S3(name="nonexistent-bucket")

    def test_successful_init_stores_location(self):
        from utilities.clients.aws.s3 import S3

        with patch("utilities.clients.aws.s3.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
            mock_s3.get_bucket_lifecycle_configuration.side_effect = _client_error(
                "NoSuchLifecycleConfiguration", 404
            )

            bucket = S3(name="my-bucket", bucket_role="standard")
            assert bucket.name == "my-bucket"

    def test_invalid_bucket_role_raises(self):
        from utilities.clients.aws.s3 import S3

        with patch("utilities.clients.aws.s3.boto3.client"):
            with pytest.raises(ValueError):
                S3(name="x", bucket_role="not-valid")

    def test_list_items_returns_keys(self):
        from utilities.clients.aws.s3 import S3

        with patch("utilities.clients.aws.s3.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
            mock_s3.get_bucket_lifecycle_configuration.side_effect = _client_error(
                "NoSuchLifecycleConfiguration", 404
            )
            mock_s3.list_objects_v2.return_value = {
                "IsTruncated": False,
                "Contents": [{"Key": "a.jpg"}, {"Key": "b.jpg"}],
            }

            with patch("utilities.clients.aws.s3.Object"):
                bucket = S3(name="my-bucket", bucket_role="standard")
                keys = bucket.list_items()

            assert set(keys) == {"a.jpg", "b.jpg"}

    def test_list_items_handles_pagination(self):
        from utilities.clients.aws.s3 import S3

        with patch("utilities.clients.aws.s3.boto3.client") as mock_client_cls:
            mock_s3 = MagicMock()
            mock_client_cls.return_value = mock_s3
            mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
            mock_s3.get_bucket_lifecycle_configuration.side_effect = _client_error(
                "NoSuchLifecycleConfiguration", 404
            )
            # First page truncated, second page is last
            mock_s3.list_objects_v2.side_effect = [
                {
                    "IsTruncated": True,
                    "NextContinuationToken": "token123",
                    "Contents": [{"Key": "page1.jpg"}],
                },
                {
                    "IsTruncated": False,
                    "Contents": [{"Key": "page2.jpg"}],
                },
            ]

            with patch("utilities.clients.aws.s3.Object"):
                bucket = S3(name="my-bucket", bucket_role="standard")
                keys = bucket.list_items()

            assert set(keys) == {"page1.jpg", "page2.jpg"}


# ---------------------------------------------------------------------------
# AWS client wrapper tests
# ---------------------------------------------------------------------------


class TestAWSClient:
    def test_load_bucket_registers_bucket(self):
        from utilities.clients.aws.client import AWS

        with patch("utilities.clients.aws.client.S3") as MockS3:
            mock_bucket = MagicMock()
            MockS3.return_value = mock_bucket

            aws = AWS()
            result = aws.load_bucket("my-bucket", bucket_role="standard")

            assert result is mock_bucket
            assert aws.get_bucket("my-bucket") is mock_bucket

    def test_list_buckets_returns_dict(self):
        from utilities.clients.aws.client import AWS

        with patch("utilities.clients.aws.client.S3") as MockS3:
            MockS3.return_value = MagicMock()
            aws = AWS()
            aws.load_bucket("bucket-a")
            aws.load_bucket("bucket-b")

            buckets = aws.list_buckets
            assert "bucket-a" in buckets
            assert "bucket-b" in buckets

    def test_cloud_identifier(self):
        from utilities.clients.aws.client import AWS

        aws = AWS()
        assert aws.cloud == "aws"
