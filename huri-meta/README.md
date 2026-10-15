# huri

A convenience package that installs the HuRI client SDK
(`huri-core[client]`) and the reference command-line client (`huri-cli`), to
talk to a running HuRI server.

It is **not published on PyPI yet**: huri-core, huri-events and huri-cli are
not on PyPI either, so publishing `huri` needs them there first. Until then,
install it from git, giving every HuRI package as a git URL on the same
command line (a `huri-core` or `huri-events` found on a package index is not
HuRI's):

```sh
pip install \
  "huri-core[client] @ git+https://github.com/Lucy-Robotics/huri-core.git@<core-ref>" \
  "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<modules-ref>#subdirectory=packages/huri-events" \
  "huri-cli @ git+https://github.com/Lucy-Robotics/huri-cli.git@<cli-ref>" \
  "huri @ git+https://github.com/Lucy-Robotics/huri-cli.git@<cli-ref>#subdirectory=huri-meta"
huri-cli --config client.yaml
```

It has no code of its own. Its source is the `huri-meta/` directory of
https://github.com/Lucy-Robotics/huri-cli.

HuRI is a realtime, modular conversational pipeline for robots and avatars.
Start at https://github.com/Lucy-Robotics/HuRI-landing. Running a server is
https://github.com/Lucy-Robotics/huri-modules; the framework and its client
SDK are https://github.com/Lucy-Robotics/huri-core.
