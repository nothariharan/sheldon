"""Minimal GitHub REST client for the check. Standard library only.

``create_check_run`` needs a GitHub App installation token (the Actions
``GITHUB_TOKEN`` is one). A personal access token cannot create check runs,
so run the server with ``SHELDON_CHECK_MODE=status`` to post a commit status.
"""

import json
import urllib.request

API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, api: str = API) -> None:
        self.token = token
        self.api = api.rstrip("/")

    def _request(self, method: str, path: str, body: dict | None = None):
        request = urllib.request.Request(
            f"{self.api}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read() or b"null")

    def changed_paths(self, repo: str, number: int) -> list[str]:
        paths: list[str] = []
        page = 1
        while True:
            files = self._request(
                "GET", f"/repos/{repo}/pulls/{number}/files?per_page=100&page={page}"
            )
            paths.extend(item["filename"] for item in files)
            if len(files) < 100:
                return paths
            page += 1

    def create_check_run(self, repo: str, payload: dict) -> None:
        self._request("POST", f"/repos/{repo}/check-runs", payload)

    def create_status(self, repo: str, sha: str, payload: dict) -> None:
        self._request("POST", f"/repos/{repo}/statuses/{sha}", payload)
