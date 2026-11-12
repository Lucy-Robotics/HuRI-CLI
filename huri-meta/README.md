# huri

A convenience package that installs the HuRI client SDK
(`huri-core[client]`) and the reference command-line client (`huri-cli`), to
talk to a running HuRI server.

```sh
pip install huri
huri-cli --config client.yaml
```

To install a ref that is not released (`dev`, a branch) instead, give every
HuRI package as a git URL on the same command line:

```sh
pip install \
  "huri-core[client] @ git+https://github.com/Lucy-Robotics/huri-core.git@<core-ref>" \
  "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<modules-ref>#subdirectory=packages/huri-events" \
  "huri-cli @ git+https://github.com/Lucy-Robotics/HuRI-CLI.git@<cli-ref>" \
  "huri @ git+https://github.com/Lucy-Robotics/HuRI-CLI.git@<cli-ref>#subdirectory=huri-meta"
huri-cli --config client.yaml
```

It has no code of its own. Its source is the `huri-meta/` directory of
https://github.com/Lucy-Robotics/HuRI-CLI.

HuRI is a realtime, modular conversational pipeline for robots and avatars.
Start at https://github.com/Lucy-Robotics/huri-core, the framework and its
client SDK, whose README maps the whole ecosystem. Running a server is
https://github.com/Lucy-Robotics/huri-modules.
