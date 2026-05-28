"""Tests for utilities.clients.tave.client.

Coverage focus on the parts that are testable without hitting the real Tave
API. ``APISpecV2.__init__`` makes a real HTTP call to ``tave.io`` to fetch
the OpenAPI spec — that's mocked out at the ``Session.send`` layer so tests
run offline.
"""

from unittest.mock import MagicMock, patch

import pytest

from utilities.clients.tave import client as tave_client


# A minimal OpenAPI-shaped spec — only the keys the Tave class actually reads
# (paths + per-path methods) are populated.
FAKE_SPEC = {
    "paths": {
        "/jobs": {
            "get": {"parameters": []},
            "post": {},
        },
        "/jobs/{id}": {
            "get": {"parameters": [{"name": "expand"}]},
        },
        "/contacts/{jobId}": {
            "get": {"parameters": []},
        },
    },
}


def _fake_send_returning_spec():
    """Replacement for Session.send that returns a response carrying FAKE_SPEC."""
    fake_response = MagicMock()
    fake_response.json.return_value = FAKE_SPEC
    return MagicMock(return_value=fake_response)


class TestIdInPath:
    def test_matches_path_with_26_char_id(self):
        assert tave_client.id_in_path("/jobs/abc123def456ghi789jkl012mn")

    def test_rejects_path_without_id(self):
        assert not tave_client.id_in_path("/jobs")

    def test_rejects_path_with_short_id(self):
        # 25 characters, not 26
        assert not tave_client.id_in_path("/jobs/abc123def456ghi789jkl01")


class TestClient:
    def test_request_returns_prepared(self):
        c = tave_client.Client()
        req = c.request("GET", url="https://example.com/x")
        # PreparedRequest exposes .method and .url
        assert req.method == "GET"
        assert req.url == "https://example.com/x"

    def test_send_with_none_raises(self):
        c = tave_client.Client()
        with pytest.raises(ValueError, match="no request"):
            c.send(request=None)


class TestApiSpecV2:
    def test_fetches_spec_on_init(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            api = tave_client.APISpecV2()
        assert api.get_spec == FAKE_SPEC
        assert set(api.get_paths) == set(FAKE_SPEC["paths"].keys())

    def test_list_path_params_empty_when_none_declared(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            api = tave_client.APISpecV2()
        assert api._list_path_params("/jobs") == []

    def test_list_path_params_extracts_parameter_names(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            api = tave_client.APISpecV2()
        params = api._list_path_params("/jobs/{id}")
        assert "expand" in params


class TestTave:
    def test_unsupported_api_version_raises(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            with pytest.raises(ValueError, match="API version"):
                tave_client.Tave("fake-key", api_ver=3)

    def test_default_api_version_is_v2(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            t = tave_client.Tave("fake-key")
        assert isinstance(t._api, tave_client.APISpecV2)

    def test_format_req_includes_api_key_header(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            t = tave_client.Tave("secret-key-value")
        req = t._format_req("GET", "/jobs")
        assert req.headers["X-API-KEY"] == "secret-key-value"
        assert req.headers["Accept"] == "application/json"

    def test_format_req_rejects_unknown_path(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            t = tave_client.Tave("fake-key")
        with pytest.raises(ValueError, match="path must be one of"):
            t._format_req("GET", "/no-such-endpoint")

    def test_format_req_rejects_method_not_in_spec(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            t = tave_client.Tave("fake-key")
        # /jobs supports GET and POST in FAKE_SPEC — DELETE is not declared
        with pytest.raises(ValueError, match="HTTP method"):
            t._format_req("DELETE", "/jobs")

    def test_format_req_encodes_get_params_in_url(self):
        with patch.object(
            tave_client.Session, "send", _fake_send_returning_spec()
        ):
            t = tave_client.Tave("fake-key")
        req = t._format_req("GET", "/jobs", path_params={"limit": 10, "offset": 0})
        assert "limit=10" in req.url
        assert "offset=0" in req.url
