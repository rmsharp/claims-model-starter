"""Wire-level tests for the httpx-based GitHub adapter (Phase 2; migrated
off PyGithub per docs/planning/httpx-adapter-migration.md Phase 2).

The real adapter is never unit-tested against a network GitHub in this
repo — that's a Phase 5 / CI-with-credentials concern. This module drives
it against ``httpx.MockTransport`` (DP4) so every request/response shape
is asserted at the wire level, with no live network access. Mirrors
``test_gitlab_adapter.py``'s structure (Phase 1).
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from model_project_constructor.agents.website import GitHubAdapter
from model_project_constructor.agents.website.github_adapter import _is_name_conflict
from model_project_constructor.agents.website.protocol import (
    RepoClientError,
    RepoNameConflictError,
)

PROJECT_ID = "acme/foo"
BRANCH = "main"
REPO_PATH = f"/repos/{PROJECT_ID}"
REF_PATH = f"/repos/{PROJECT_ID}/git/ref/heads/{BRANCH}"
PARENT_COMMIT_PATH = f"/repos/{PROJECT_ID}/git/commits/parent-sha"
BLOB_PATH = f"/repos/{PROJECT_ID}/git/blobs"
TREE_PATH = f"/repos/{PROJECT_ID}/git/trees"
COMMITS_PATH = f"/repos/{PROJECT_ID}/git/commits"
REF_EDIT_PATH = f"/repos/{PROJECT_ID}/git/refs/heads/{BRANCH}"

Handler = Callable[[httpx.Request], httpx.Response]
RouteEntry = httpx.Response | Handler
RouteMap = dict[tuple[str, str], RouteEntry]


def _adapter_with_transport(handler: Handler) -> GitHubAdapter:
    """Build an adapter, then swap its client for one backed by a mock transport.

    Mirrors the pre-migration pattern of stubbing the internal SDK handle
    after construction (previously ``adapter._gh = MagicMock()``), just at
    the wire layer instead of the SDK layer.
    """

    adapter = GitHubAdapter(host_url="https://api.github.com", private_token="t")
    adapter._client = httpx.Client(
        base_url=adapter._client.base_url,
        headers=adapter._client.headers,
        transport=httpx.MockTransport(handler),
    )
    return adapter


def _route(mapping: RouteMap) -> Handler:
    """Dispatch a mock request to ``mapping`` by ``(method, path)``.

    Callable entries are invoked with the request (so a test can inspect
    the body or raise a transport error); ``httpx.Response`` entries are
    returned as-is. An unmapped ``(method, path)`` fails the test loudly
    rather than silently 404-ing, so an unexpected extra call is caught
    immediately.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        entry = mapping.get((request.method, request.url.path))
        if entry is None:
            raise AssertionError(f"unexpected request: {request.method} {request.url.path}")
        if callable(entry):
            return entry(request)
        return entry

    return handler


def _blob_response(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    return httpx.Response(201, json={"sha": f"blob-{payload['content']}"})


def _raise_connect_error(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


def _happy_commit_dance_mapping() -> RouteMap:
    """The full 7-call git-dance, all succeeding.

    Tests that want a single failure point copy this dict and override one
    key, so every failure test still exercises the calls preceding it
    exactly as the happy path does.
    """

    return {
        ("GET", REPO_PATH): httpx.Response(200, json={"id": 1}),
        ("GET", REF_PATH): httpx.Response(200, json={"object": {"sha": "parent-sha"}}),
        ("GET", PARENT_COMMIT_PATH): httpx.Response(
            200, json={"tree": {"sha": "base-tree-sha"}}
        ),
        ("POST", BLOB_PATH): _blob_response,
        ("POST", TREE_PATH): httpx.Response(201, json={"sha": "new-tree-sha"}),
        ("POST", COMMITS_PATH): httpx.Response(201, json={"sha": "commit-sha"}),
        ("PATCH", REF_EDIT_PATH): httpx.Response(200, json={"ref": f"refs/heads/{BRANCH}"}),
    }


class TestImport:
    def test_adapter_has_protocol_methods(self) -> None:
        # ``RepoClient`` is not runtime_checkable (structural only), so a
        # duck-type check mirrors the gitlab-adapter pattern. mypy strict
        # on the production module enforces the real contract.
        adapter = GitHubAdapter(
            host_url="https://api.github.com", private_token="dummy"
        )
        assert callable(adapter.create_project)
        assert callable(adapter.commit_files)

    def test_constructor_does_not_make_network_call(self) -> None:
        """Creating an adapter with a dummy token must not reach the network.

        ``httpx.Client`` defers all I/O to the first request, so
        instantiating with junk credentials should succeed silently.
        """

        GitHubAdapter(
            host_url="https://invalid.example.invalid",
            private_token="not-a-real-token",
        )

    def test_constructor_scopes_client_to_default_host(self) -> None:
        adapter = GitHubAdapter(host_url="https://api.github.com", private_token="t")
        assert str(adapter._client.base_url) == "https://api.github.com"
        assert adapter._client.headers["authorization"] == "Bearer t"
        assert adapter._client.headers["accept"] == "application/vnd.github+json"

    def test_constructor_normalizes_trailing_slash_for_enterprise_host(self) -> None:
        # A single trailing slash passed by the caller must not become a
        # double slash once httpx's own base_url normalization (which
        # always ends a non-empty path in "/") is applied.
        adapter = GitHubAdapter(
            host_url="https://github.example.com/api/v3/", private_token="t"
        )
        assert str(adapter._client.base_url) == "https://github.example.com/api/v3/"


class TestNameConflictSniffing:
    @staticmethod
    def _response(
        status_code: int, *, json_body: object = None, text: str | None = None
    ) -> httpx.Response:
        if text is not None:
            return httpx.Response(status_code, text=text)
        return httpx.Response(status_code, json=json_body)

    def test_422_with_already_exists_message_is_conflict(self) -> None:
        response = self._response(
            422, json_body={"errors": [{"message": "name already exists on this account"}]}
        )
        assert _is_name_conflict(response) is True

    def test_422_with_generic_already_exists_fallback_is_conflict(self) -> None:
        # Wording drift: message is elsewhere in the payload, but the
        # stringified body still mentions "already exists".
        response = self._response(422, json_body={"message": "Repository already exists"})
        assert _is_name_conflict(response) is True

    def test_500_is_not_conflict(self) -> None:
        response = self._response(500, json_body={"message": "server error"})
        assert _is_name_conflict(response) is False

    def test_422_with_unrelated_message_is_not_conflict(self) -> None:
        response = self._response(
            422, json_body={"errors": [{"message": "visibility is invalid"}]}
        )
        assert _is_name_conflict(response) is False

    def test_422_with_multiple_errors_matches_second_entry(self) -> None:
        # Exercises the loop continuing past a non-matching first entry
        # rather than only ever inspecting a single-element list.
        response = self._response(
            422,
            json_body={
                "errors": [
                    {"message": "visibility is invalid"},
                    "not-a-dict-entry",
                    {"message": "name already exists on this account"},
                ]
            },
        )
        assert _is_name_conflict(response) is True

    def test_non_json_body_falls_back_to_raw_text(self) -> None:
        response = self._response(422, text="name already exists (plain text)")
        assert _is_name_conflict(response) is True


class TestNestedNamespaceGuard:
    def test_nested_namespace_raises_client_error(self) -> None:
        # No transport needed — the guard fires before any request is sent.
        adapter = GitHubAdapter(host_url="https://api.github.com", private_token="t")
        with pytest.raises(RepoClientError, match="nested namespace"):
            adapter.create_project(namespace="acme/sub", name="foo", visibility="private")


class TestCreateProject:
    def test_org_lookup_network_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(_route({("GET", "/orgs/acme"): _raise_connect_error}))
        with pytest.raises(RepoClientError, match="owner lookup failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_org_lookup_non_404_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route({("GET", "/orgs/acme"): httpx.Response(500, json={"message": "boom"})})
        )
        with pytest.raises(RepoClientError, match="owner lookup failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_user_lookup_network_error_after_org_missing_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/alice"): httpx.Response(404, json={"message": "Not Found"}),
                    ("GET", "/users/alice"): _raise_connect_error,
                }
            )
        )
        with pytest.raises(RepoClientError, match="owner lookup failed"):
            adapter.create_project(namespace="alice", name="foo", visibility="private")

    def test_user_lookup_failure_after_org_missing_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/alice"): httpx.Response(404, json={"message": "Not Found"}),
                    ("GET", "/users/alice"): httpx.Response(500, json={"message": "boom"}),
                }
            )
        )
        with pytest.raises(RepoClientError, match="owner lookup failed"):
            adapter.create_project(namespace="alice", name="foo", visibility="private")

    def test_org_missing_falls_back_to_authenticated_user_repos(self) -> None:
        def create_repo(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload == {"name": "foo", "private": False}
            return httpx.Response(
                201,
                json={
                    "full_name": "alice/foo",
                    "html_url": "https://github.com/alice/foo",
                    "default_branch": "main",
                },
            )

        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/alice"): httpx.Response(404, json={"message": "Not Found"}),
                    ("GET", "/users/alice"): httpx.Response(200, json={"login": "alice"}),
                    ("POST", "/user/repos"): create_repo,
                }
            )
        )

        info = adapter.create_project(namespace="alice", name="foo", visibility="public")

        assert info.id == "alice/foo"
        assert info.url == "https://github.com/alice/foo"
        assert info.default_branch == "main"

    def test_create_project_network_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): _raise_connect_error,
                }
            )
        )
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_create_project_name_conflict_raises_repo_name_conflict(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): httpx.Response(
                        422,
                        json={"errors": [{"message": "name already exists on this account"}]},
                    ),
                }
            )
        )
        with pytest.raises(RepoNameConflictError) as excinfo:
            adapter.create_project(namespace="acme", name="foo", visibility="private")
        assert excinfo.value.name == "foo"

    def test_create_project_redirect_response_raises_client_error(self) -> None:
        """A 3xx must not silently pass through: ``httpx.Client`` does not
        follow redirects by default (unlike the ``requests``-based
        transport the old ``PyGithub`` adapter used), so treating "not >=
        400" as success would try to parse a redirect body as JSON and
        crash with a raw exception."""

        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): httpx.Response(
                        301, headers={"Location": "https://elsewhere"}
                    ),
                }
            )
        )
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_create_project_malformed_json_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): httpx.Response(201, text="not json"),
                }
            )
        )
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_create_project_generic_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): httpx.Response(
                        500, json={"message": "Internal error"}
                    ),
                }
            )
        )
        with pytest.raises(RepoClientError, match="create_project failed"):
            adapter.create_project(namespace="acme", name="foo", visibility="private")

    def test_create_project_happy_path_under_org_returns_project_info(self) -> None:
        def create_repo(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/orgs/acme/repos"
            payload = json.loads(request.content)
            assert payload == {"name": "foo", "private": True}
            return httpx.Response(
                201,
                json={
                    "full_name": "acme/foo",
                    "html_url": "https://github.com/acme/foo",
                    "default_branch": "develop",
                },
            )

        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): create_repo,
                }
            )
        )

        info = adapter.create_project(namespace="acme", name="foo", visibility="internal")
        assert info.id == "acme/foo"
        assert info.url == "https://github.com/acme/foo"
        assert info.default_branch == "develop"

    def test_create_project_defaults_default_branch_to_main(self) -> None:
        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): httpx.Response(
                        201,
                        json={
                            "full_name": "acme/foo",
                            "html_url": "https://github.com/acme/foo",
                        },
                    ),
                }
            )
        )
        info = adapter.create_project(namespace="acme", name="foo", visibility="private")
        assert info.default_branch == "main"

    def test_create_project_visibility_public_passes_private_false(self) -> None:
        def create_repo(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload["private"] is False
            return httpx.Response(
                201,
                json={"full_name": "acme/foo", "html_url": "https://github.com/acme/foo"},
            )

        adapter = _adapter_with_transport(
            _route(
                {
                    ("GET", "/orgs/acme"): httpx.Response(200, json={"login": "acme"}),
                    ("POST", "/orgs/acme/repos"): create_repo,
                }
            )
        )
        adapter.create_project(namespace="acme", name="foo", visibility="public")


class TestCommitFiles:
    def test_project_lookup_network_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(_route({("GET", REPO_PATH): _raise_connect_error}))
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_project_lookup_http_error_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route({("GET", REPO_PATH): httpx.Response(404, json={"message": "Not Found"})})
        )
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_project_lookup_redirect_response_raises_client_error(self) -> None:
        adapter = _adapter_with_transport(
            _route({("GET", REPO_PATH): httpx.Response(302, headers={"Location": "https://x"})})
        )
        with pytest.raises(RepoClientError, match="project lookup failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_ref_lookup_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("GET", REF_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_ref_lookup_http_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("GET", REF_PATH)] = httpx.Response(404, json={"message": "No commit found"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_ref_lookup_redirect_response_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("GET", REF_PATH)] = httpx.Response(303, headers={"Location": "https://x"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_parent_commit_lookup_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("GET", PARENT_COMMIT_PATH)] = httpx.Response(
            500, json={"message": "boom"}
        )
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_parent_commit_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("GET", PARENT_COMMIT_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="test"
            )

    def test_blob_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", BLOB_PATH)] = httpx.Response(500, json={"message": "blob boom"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_blob_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", BLOB_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_tree_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", TREE_PATH)] = httpx.Response(500, json={"message": "tree boom"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_tree_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", TREE_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_create_commit_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", COMMITS_PATH)] = httpx.Response(500, json={"message": "commit boom"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_create_commit_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", COMMITS_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_ref_edit_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("PATCH", REF_EDIT_PATH)] = httpx.Response(500, json={"message": "ref boom"})
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_ref_edit_network_error_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("PATCH", REF_EDIT_PATH)] = _raise_connect_error
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_commit_files_malformed_json_raises_client_error(self) -> None:
        mapping = _happy_commit_dance_mapping()
        mapping[("POST", TREE_PATH)] = httpx.Response(201, text="not json")
        adapter = _adapter_with_transport(_route(mapping))
        with pytest.raises(RepoClientError, match="commit_files failed"):
            adapter.commit_files(
                project_id=PROJECT_ID, branch=BRANCH, files={"a.txt": "x"}, message="init"
            )

    def test_commit_files_happy_path_returns_commit_info(self) -> None:
        def create_tree(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload["base_tree"] == "base-tree-sha"
            assert payload["tree"] == [
                {"path": "a.txt", "mode": "100644", "type": "blob", "sha": "blob-x"},
                {"path": "b.txt", "mode": "100644", "type": "blob", "sha": "blob-y"},
            ]
            return httpx.Response(201, json={"sha": "new-tree-sha"})

        def create_commit(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload == {
                "message": "init",
                "tree": "new-tree-sha",
                "parents": ["parent-sha"],
            }
            return httpx.Response(201, json={"sha": "commit-sha"})

        def edit_ref(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload == {"sha": "commit-sha"}
            return httpx.Response(200, json={"ref": f"refs/heads/{BRANCH}"})

        mapping = _happy_commit_dance_mapping()
        mapping[("POST", TREE_PATH)] = create_tree
        mapping[("POST", COMMITS_PATH)] = create_commit
        mapping[("PATCH", REF_EDIT_PATH)] = edit_ref
        adapter = _adapter_with_transport(_route(mapping))

        info = adapter.commit_files(
            project_id=PROJECT_ID,
            branch=BRANCH,
            files={"b.txt": "y", "a.txt": "x"},
            message="init",
        )
        assert info.sha == "commit-sha"
        assert info.files_committed == ["a.txt", "b.txt"]
