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

Maintainers of `Lucy-Robotics/huri-cli`:

1. On `dev`, check the dependency ranges in `pyproject.toml` against the
   huri-core and huri-events releases this version supports, and update the
   compatibility table in README's "Versions and compatibility". CI must be
   green with `HURI_CORE_REF` / `HURI_MODULES_REF` set to those release tags
   (run the workflow by hand with them).
2. Open a release PR on `dev` that sets `version` (no `.devN`) and summarizes
   the changes; merge it, then merge `dev` into `main` with a PR named
   `Release X.Y.Z`.
3. Tag `main`'s merge commit `X.Y.Z` (no `v` prefix; the first release is
   `0.1.0`), push the tag and publish a GitHub release whose notes are the
   changelog.
4. Tell huri-modules: its `versions.env` pins `HURI_CLI_REF`, which its
   installer installs; its release sets it to this tag.

## The `huri` metapackage

`huri-meta/` has its own `version`. When its ranges (`huri-core[client]`,
`huri-cli`) change, bump it in the same release PR. Publishing to PyPI, when
done, is `python -m build huri-meta` and an upload of `huri-meta/dist/*`,
after huri-cli itself is published.
