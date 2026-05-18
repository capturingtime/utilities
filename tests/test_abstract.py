"""Tests for abstract base classes — verifies contract enforcement."""
import pytest
from abc import ABC

from utilities.classes.abstract.bucket import Bucket, VALID_BUCKET_ROLES, DEFAULT_BUCKET_ROLE
from utilities.classes.abstract.bucketitem import BucketItem
from utilities.classes.abstract.cloud import Cloud
from utilities.classes.abstract.path import Path


# ---------------------------------------------------------------------------
# Minimal concrete stubs used only within this test module
# ---------------------------------------------------------------------------


class _ConcreteBucket(Bucket):
    def get_item(self, key): ...
    def del_item(self, key): ...
    def put_item(self, key, body): ...
    def copy_item(self): ...
    def rename_item(self): ...
    def list_items(self): ...


class _ConcreteCloud(Cloud):
    def load_bucket(self, name, bucket_role): ...


class _ConcreteBucketItem(BucketItem):
    @property
    def data(self): ...

    @property
    def metadata(self): ...


class _ConcretePath(Path):
    def copy(self): ...
    def delete(self): ...
    def create(self): ...
    def mv(self): ...


# ---------------------------------------------------------------------------
# Bucket tests
# ---------------------------------------------------------------------------


class TestBucket:
    def test_valid_roles_accepted(self):
        for role in VALID_BUCKET_ROLES:
            b = _ConcreteBucket(name="test-bucket", bucket_role=role)
            assert b.bucket_role == role

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError, match="bucket_role must be one of"):
            _ConcreteBucket(name="test-bucket", bucket_role="invalid-role")

    def test_default_role_is_standard(self):
        b = _ConcreteBucket(name="test-bucket")
        assert b.bucket_role == DEFAULT_BUCKET_ROLE

    def test_name_stored(self):
        b = _ConcreteBucket(name="my-bucket")
        assert b.name == "my-bucket"

    def test_desc_stored(self):
        b = _ConcreteBucket(name="my-bucket", bucket_desc="test desc")
        assert b.bucket_desc == "test desc"

    def test_abstract_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Bucket(name="x")  # type: ignore


# ---------------------------------------------------------------------------
# Cloud tests
# ---------------------------------------------------------------------------


class TestCloud:
    def test_cloud_property(self):
        c = _ConcreteCloud(cloud="aws")
        assert c.cloud == "aws"

    def test_abstract_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Cloud()  # type: ignore


# ---------------------------------------------------------------------------
# BucketItem tests
# ---------------------------------------------------------------------------


class TestBucketItem:
    def test_item_property(self):
        bi = _ConcreteBucketItem(item="prefix/key.jpg")
        assert bi.item == "prefix/key.jpg"

    def test_abstract_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BucketItem(item="x")  # type: ignore


# ---------------------------------------------------------------------------
# Path tests
# ---------------------------------------------------------------------------


class TestPath:
    def test_str_returns_abspath(self, tmp_path):
        p = _ConcretePath(str(tmp_path))
        assert str(p) == str(tmp_path.resolve())

    def test_path_property(self, tmp_path):
        raw = str(tmp_path)
        p = _ConcretePath(raw)
        assert p.path == raw

    def test_abstract_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Path("/some/path")  # type: ignore
