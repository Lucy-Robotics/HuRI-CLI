# Releasing huri-cli

huri-cli has its own versions, independent of huri-core and huri-modules.

## Version and semver

The version is `version` in `pyproject.toml`. Between releases `dev` carries
the next version with a `.devN` suffix (`0.1.0.dev0` until the first
release, `0.1.0`). The public surface is the command line
(`huri-cli --config ... --log-level ... --log-file ...`) and the keys of the
`cli:` config section; while the major version is `0`, a minor bump may break
it and a patch bump must not. The Python modules under `huri_cli/` are an
example to read, not an API.

## Steps

Maintainers of `Lucy-Robotics/HuRI-CLI`:

1. On `dev`, check the dependency ranges in `pyproject.toml` against the
   huri-core and huri-events releases this version supports, and update the
   compatibility table in README's "Versions and compatibility". CI must be
   green with `HURI_CORE_REF` / `HURI_MODULES_REF` set to those release tags
   (run the workflow by hand with them). When the huri-core range moves to a
   new minor, move the default `HURI_CORE_REF` of `ci.yml` with it.
2. Open a release PR on `dev` that sets `version` (no `.devN`) and summarizes
   the changes; merge it, then open the PR from `dev` into `main` named
   `Release X.Y.Z`. Its **Release** check (`.github/workflows/release.yml`)
   fails when the release would be wrong: a pre-release version, or a version
   already tagged or on PyPI. Its job summary says what merging will publish.
3. Merge it. The Release workflow then tags `main`'s merge commit `X.Y.Z` (no
   `v` prefix), publishes the GitHub release (notes generated from the merged
   pull requests since the previous tag; edit them afterwards if needed), and
   waits for a maintainer to approve the `pypi` environment before uploading
   huri-cli to PyPI. It ends by installing it from PyPI. PyPI never accepts a
   version twice. A failed upload: "Re-run failed jobs" on that run; or, while
   `main` is still at the release commit, run the Release workflow by hand on
   `main`.
4. The workflow also opens a PR into `dev` that sets `version` to the next
   `X.(Y+1).0.dev0` (`chore: start X.(Y+1).0.dev0 after the X.Y.Z release`).
   CI does not start on a PR opened by `GITHUB_TOKEN`: close and reopen it (or
   push to it), then merge it.
5. Tell huri-modules: its `versions.env` pins `HURI_CLI_REF`, which its
   installer installs; its release sets it to this tag.

## Publishing setup (once)

The Release workflow uploads with PyPI's trusted publishing: no token is
stored. `huri-cli` has, on pypi.org (Manage → Publishing), a GitHub publisher
with owner `Lucy-Robotics`, repository `HuRI-CLI`, workflow `release.yml` and
environment `pypi`. The repository's `pypi` environment requires a
maintainer's approval and only accepts `main`. If the repository moves to
another GitHub owner, add the new publisher and remove the old one.

By hand, if the workflow cannot run: from the tag,
`python -m build -o dist . && twine check dist/* && twine upload dist/*`.
