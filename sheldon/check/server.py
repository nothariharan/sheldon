"""Run the webhook: ``python -m sheldon.check.server``.

Environment:

- ``SHELDON_WEBHOOK_SECRET``: the secret set on the GitHub webhook. Required.
- ``GITHUB_TOKEN``: token that can read PR files and write checks or statuses. Required.
- ``SHELDON_CHECK_MODE``: ``check_run`` (default, needs an App token) or ``status``.
- ``SHELDON_PORT``: listen port, default 8080.
"""

import os
from wsgiref.simple_server import make_server

from sheldon.check.github import GitHubClient
from sheldon.check.webhook import make_app


def main() -> None:
    secret = os.environ["SHELDON_WEBHOOK_SECRET"].encode()
    github = GitHubClient(os.environ["GITHUB_TOKEN"])
    mode = os.environ.get("SHELDON_CHECK_MODE", "check_run")
    port = int(os.environ.get("SHELDON_PORT", "8080"))
    with make_server("", port, make_app(secret, github, mode=mode)) as server:
        print(f"sheldon check webhook on :{port}/webhook ({mode})")
        server.serve_forever()


if __name__ == "__main__":
    main()
