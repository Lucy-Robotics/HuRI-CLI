"""Plan a release: what the Release workflow tags, publishes and uploads.

    python scripts/release_plan.py

Run by .github/workflows/release.yml, from a full clone (tags included):

- on a pull request into main (the release PR): checks the release is
  consistent, and fails it otherwise;
- on a push to main: a release when huri-cli's version is not tagged yet,
  nothing otherwise (a merge into main that is not a release);
- on a manual run on main, once the version is tagged at this commit: resumes
  the upload.

Prints the plan (and adds it to the job summary), writes `release`,
`create`, `version` and `previous` to $GITHUB_OUTPUT, exits 1 on a problem.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional

from packaging.version import InvalidVersion, Version

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
OnPyPI = Callable[[str, str], bool]


def on_pypi(name: str, version: str) -> bool:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30):
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def release_tags(tags: List[str]) -> List[Version]:
    """The release tags (`X.Y.Z`, no pre-release), oldest first."""

    versions = []
    for tag in tags:
        try:
            version = Version(tag)
        except InvalidVersion:
            continue
        if not version.is_prerelease and str(version) == tag:
            versions.append(version)
    return sorted(versions)


def problems(cli: str, tags: List[str], pypi: OnPyPI) -> List[str]:
    """Why releasing huri-cli `cli` now would be wrong."""

    found = []
    if Version(cli).is_prerelease:
        found.append(
            f"huri-cli's version {cli} is a pre-release: drop its pre-release "
            "suffix (.devN, rcN, ...) in pyproject.toml"
        )
    if cli in tags:
        found.append(f"tag {cli} already exists: bump huri-cli's version")
    elif pypi("huri-cli", cli):
        found.append(f"huri-cli {cli} is already on PyPI: bump huri-cli's version")
    return found


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def _output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.writelines(f"{k}={v}\n" for k, v in values.items())


def _summary(text: str) -> None:
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(text + "\n")


def main(pypi: OnPyPI = on_pypi) -> int:
    event = os.environ.get("GITHUB_EVENT_NAME", "pull_request")
    ref = os.environ.get("GITHUB_REF")
    if event != "pull_request" and ref != "refs/heads/main":
        # A tag is forever: only main's commits are ever released.
        print(f"::error::releases run on main only, not {ref}")
        _output(release="false")
        return 1
    with open(ROOT / "pyproject.toml", "rb") as f:
        cli = tomllib.load(f)["project"]["version"]

    tags = _git("tag", "--list").stdout.split()
    # The release before this one (a patch on an older line compares to its own).
    released = [str(v) for v in release_tags(tags) if v < Version(cli)]
    previous: Optional[str] = released[-1] if released else None

    if cli in tags:
        tagged = _git("rev-list", "-n", "1", cli).stdout.strip()
        head = _git("rev-parse", "HEAD").stdout.strip()
        if event == "push":
            _summary(f"huri-cli {cli} is already tagged: not a release.")
            _output(release="false")
            return 0
        if event == "workflow_dispatch" and tagged == head:
            # Resume: the tag and the GitHub release exist, upload if missing.
            _output(
                release="true", create="false", version=cli, previous=previous or ""
            )
            _summary(f"Resuming the upload of release {cli}.")
            return 0

    found = problems(cli, tags, pypi)
    if found:
        for problem in found:
            print(f"::error::{problem}")
        _summary("Release blocked:\n" + "\n".join(f"- {p}" for p in found))
        _output(release="false")
        return 1

    _summary(
        "\n".join(
            [
                f"Merging this into main releases huri-cli **{cli}**"
                + (f" (previous: {previous})" if previous else "")
                + ":",
                "",
                "| what | action |",
                "|---|---|",
                f"| tag `{cli}` on main's merge commit | create |",
                f"| GitHub release `{cli}` | publish, marked latest |",
                f"| PyPI `huri-cli {cli}` | upload |",
            ]
        )
    )
    _output(
        release=json.dumps(event != "pull_request"),
        create="true",
        version=cli,
        previous=previous or "",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
