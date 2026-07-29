"""Wire-level tests for the httpx-based GitLab adapter (Phase 4B; migrated
off python-gitlab per docs/planning/httpx-adapter-migration.md Phase 1).

The real adapter is never unit-tested against a network GitLab in this
repo — that's a Phase 5 / CI-with-credentials concern. This module drives
it against ``httpx.MockTransport`` (DP4) so every request/response shape
is asserted at the wire level, with no live network access.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from model_project_constructor.agents.website import GitLabAdapter
from model_project_constructor.agents.website.gitlab_adapter import _is_name_conflict
from model_project_constructor.agents.website.protocol import (
    RepoClientError,
    RepoNameConflictError,
)


def _adapter_with_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> GitLabAdapter:
    """Build an adapter, then swap its client for one backed by a mock transport.

    Mirrors the pre-migration pattern of stubbing the internal SDK handle
    after construction (previously ``adapter._gl = MagicMock()``), just at
    the wire layer instead of the SDK layer.
    """

    adapter = GitLabAdapter(
        host_url="https://gitlab.example.com", private_token="t"
    )
    adapter._client = httpx.Client(
        base_url=adapter._client.base_url,
        headers=adapter._client.headers,
        transport=httpx.MockTransport(handler),
    )
    return adapter


class TestImport:
    def test_adapter_has_protocol_methods(self) -> None:
        # ``RepoClient`` is not runtime_checkable (structural only), so
        # ``isinstance`` would raise. A duck-type check is sufficient
        # since mypy strict on the module enforces the real contract.
        adapter = GitLabAdapter(
            host_url="https://gitlab.example.com", private_token="dummy"
        )
        assert callable(adapter.create_project)
        assert callable(adapter.commit_files)

    def test_constructor_does_not_make_network_call(self) -> None:
        """Creating an adapter with a dummy token must not reach the network.

        ``httpx.Client`` defers all I/O to the first request, so
        instantiating with junk credentials should succeed silently.
        """

        GitLabAdapter(
            host_url="https://invalid.example.invalid",
            private_token="not-a-real-token",
        )

    def test_constructor_scopes_client_to_api_v4(self) -> None:
        adapter = GitLabAdapter(
            host_url="https://gitlab.example.com/", private_token="t"
        )
        assert str(adapter._client.base_url) == "https://gitlab.example.com/api/v4/"
        assert adapter._client.headers["private-token"] == "t"


class TestNameConflictSniffing:
    @staticmethod
    def _response(
        status_code: int, *, json_body: object = None, text: str | None = None
    ) -> httpx.Response:
        if text is not None:
            return httpx.Response(status_code, text=text)
        return httpx.Response(status_code, json=json_body)

    def test_400_with_taken_message_is_conflict(self) -> None:
        response = self._response(400, json_body={"name": ["has already been taken"]})
        assert _is_name_conflict(response) is True

    def test_409_with_exists_message_is_conflict(self) -> None:
        response = self._response(409, json_body={"message": "Project already exists"})
        assert _is_name_conflict(response) is True

    def test_500_is_not_conflict(self) -> None:
        response = self._response(500, json_body={"message": "Internal Server Error"})
        assert _is_name_conflict(response) is False

    def test_400_without_taken_message_is_not_conflict(self) -> None:
        response = self._response(400, json_body={"visibility": ["is invalid"]})
        assert _is_name_conflict(response) is False

    def test_non_json_body_falls_back_to_raw_text(self) -> None:
        response = self._response(400, text="name already exists (plain text)")
        assert _is_name_conflict(response) is True


class TestCreateProject:
    def test_group_lookup_network_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="group lookup failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_group_lookup_http_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "404 Group Not Found"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="group lookup failed"):
            adapter.create_project(
                namespace="missing", name="foo", visibility="private"
            )

    def test_group_lookup_redirect_response_raises_client_error(self) -> None:
        """A 3xx must not silently pass through: ``httpx.Client`` does not
        follow redirects by default (unlike the old ``requests``-based
        transport), so treating "not >= 400" as success would try to parse
        a redirect body as JSON and crash with a raw exception."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"Location": "https://elsewhere"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="group lookup failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_group_lookup_malformed_json_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>not json</html>")

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="group lookup failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_create_project_network_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 42})
            raise httpx.ConnectError("connection refused", request=request)

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_create_project_name_conflict_raises_repo_name_conflict(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 42})
            return httpx.Response(400, json={"name": ["has already been taken"]})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoNameConflictError) as excinfo:
            adapter.create_project(namespace="g", name="foo", visibility="private")
        assert excinfo.value.name == "foo"

    def test_create_project_redirect_response_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 42})
            return httpx.Response(301, headers={"Location": "https://elsewhere"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_create_project_malformed_json_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 42})
            return httpx.Response(201, text="not json")

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_create_project_generic_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 42})
            return httpx.Response(500, json={"message": "Internal error"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="g", name="foo", visibility="private")

    def test_create_project_happy_path_returns_project_info(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                # Assert on the raw (still-encoded) path — GitLab requires
                # the literal ``%2F`` to address a nested group as one
                # path segment; ``.path`` would decode it back to ``/``.
                assert (
                    request.url.raw_path.decode()
                    == "/api/v4/groups/data-science%2Fmodels"
                )
                assert request.headers["private-token"] == "t"
                return httpx.Response(200, json={"id": 42})
            assert request.url.path == "/api/v4/projects"
            payload = json.loads(request.content)
            assert payload == {
                "name": "foo",
                "path": "foo",
                "namespace_id": 42,
                "visibility": "private",
            }
            return httpx.Response(
                201,
                json={
                    "id": 7,
                    "web_url": "https://gitlab.example.com/data-science/models/foo",
                    "default_branch": "develop",
                },
            )

        adapter = _adapter_with_transport(handler)
        info = adapter.create_project(
            namespace="data-science/models", name="foo", visibility="private"
        )
        assert info.id == "7"
        assert info.url == "https://gitlab.example.com/data-science/models/foo"
        assert info.default_branch == "develop"

    def test_create_project_defaults_default_branch_to_main(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 1})
            return httpx.Response(201, json={"id": 2, "web_url": "https://x/y"})

        adapter = _adapter_with_transport(handler)
        info = adapter.create_project(namespace="g", name="foo", visibility="private")
        assert info.default_branch == "main"


class TestCommitFiles:
    def test_project_lookup_network_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_project_lookup_http_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "404 Project Not Found"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_project_lookup_redirect_response_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"Location": "https://elsewhere"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_commit_files_network_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 1})
            raise httpx.ConnectError("connection refused", request=request)

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_commit_files_http_error_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 1})
            return httpx.Response(429, json={"message": "rate limited"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_commit_files_redirect_response_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 1})
            return httpx.Response(303, headers={"Location": "https://elsewhere"})

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_commit_files_malformed_json_raises_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json={"id": 1})
            return httpx.Response(201, text="not json")

        adapter = _adapter_with_transport(handler)
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id="1", branch="main", files={"a.txt": "x"}, message="test"
            )

    def test_commit_files_happy_path_returns_commit_info(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                assert request.url.path == "/api/v4/projects/1"
                return httpx.Response(200, json={"id": 1})
            assert request.url.path == "/api/v4/projects/1/repository/commits"
            payload = json.loads(request.content)
            assert payload == {
                "branch": "main",
                "commit_message": "init",
                "actions": [
                    {"action": "create", "file_path": "a.txt", "content": "x"},
                    {"action": "create", "file_path": "b.txt", "content": "y"},
                ],
            }
            return httpx.Response(201, json={"id": "deadbeef"})

        adapter = _adapter_with_transport(handler)
        info = adapter.commit_files(
            project_id="1",
            branch="main",
            files={"b.txt": "y", "a.txt": "x"},
            message="init",
        )
        assert info.sha == "deadbeef"
        assert info.files_committed == ["a.txt", "b.txt"]
