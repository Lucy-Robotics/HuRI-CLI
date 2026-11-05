# Contributing to HuRI-CLI

HuRI's contribution guide is
[huri-core's CONTRIBUTING.md](https://github.com/Lucy-Robotics/huri-core/blob/main/CONTRIBUTING.md):
which repository takes which change, how to submit a pull request, the commit
format, the conventions and the response times. This page adds what is
specific to HuRI-CLI.

- **Branch from `dev`** and open the pull request to `dev`.
- **Before pushing**, run the lint and the tests of
  [Working on huri-cli](README.md#working-on-huri-cli). The tests never open an
  audio device nor reach the network; keep it that way.
- **The `cli:` section and the command line** follow semver: a change that
  breaks an existing config or flag is a minor bump while `0.x`
  ([Versions and compatibility](README.md#versions-and-compatibility)).
- **A module name in `config/`** must exist in huri-modules' `registry.toml`;
  CI checks it.
- **Releases** follow [RELEASING.md](RELEASING.md).
