# huri

A convenience package: `pip install --pre huri` installs the HuRI client SDK
(`huri-core[client]`) and the reference command-line client (`huri-cli`), to
talk to a running HuRI server:

```sh
pip install --pre huri
huri-cli --config client.yaml
```

It has no code of its own. Its source is the `huri-meta/` directory of
https://github.com/Lucy-Robotics/huri-cli.

HuRI is a realtime, modular conversational pipeline for robots and avatars.
Start at https://github.com/Lucy-Robotics/HuRI-landing. Running a server is
https://github.com/Lucy-Robotics/huri-modules; the framework and its client
SDK are https://github.com/Lucy-Robotics/huri-core.
