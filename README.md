# huri-cli

The reference client of [HuRI](https://github.com/Lucy-Robotics/HuRI-landing):
talk to a running HuRI server from a terminal. Microphone and a text prompt
in; the assistant's reply as text, speech and a live gesture view out.

huri-cli is a **use case** of HuRI, not a part of it, like the
[demo website](https://github.com/Lucy-Robotics/HuRI_website_demo) or the
[acceptance test site](https://github.com/Lucy-Robotics/HuRI_ATP_testsite).
It uses nothing but the public client SDK of
[huri-core](https://github.com/Lucy-Robotics/huri-core) and the curated events
of [huri-modules](https://github.com/Lucy-Robotics/huri-modules)
(`huri-events`), pinned by version range, and it has its own versions and
releases. Read it as a worked example when you write your own client.

## Install

The easy way is huri-modules' installer: it sets up a server **and** installs
huri-cli next to it (`./install.sh --no-cli` skips it), then prints the
command that starts a session.

On its own, in a virtual environment (Python 3.10 to 3.12), from git at a
ref (a release tag such as `0.1.0`, or `dev`):

```sh
pip install \
  "huri-core[client] @ git+https://github.com/Lucy-Robotics/huri-core.git@<core-ref>" \
  "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<modules-ref>#subdirectory=packages/huri-events" \
  "huri-cli @ git+https://github.com/Lucy-Robotics/huri-cli.git@<cli-ref>"
```

Pick refs that match the table in
[Versions and compatibility](#versions-and-compatibility). A pre-release may
also be on PyPI (`pip install --pre huri-cli`, or `pip install --pre huri`,
see [The `huri` metapackage](#the-huri-metapackage)); git is the reference.

`sounddevice` needs PortAudio (`libportaudio2` on Debian/Ubuntu, `portaudio`
on Arch/Fedora) to open the microphone and the speakers.

### Working on huri-cli

```sh
pip install \
  "huri-core[client] @ git+https://github.com/Lucy-Robotics/huri-core.git@dev" \
  "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@dev#subdirectory=packages/huri-events"
pip install -e ".[dev]"
pytest -q
black --check huri_cli tests scripts && isort --check-only huri_cli tests scripts
flake8 huri_cli tests scripts && mypy huri_cli scripts --check-untyped-defs
```

Local checkouts work as well: `pip install -e "../huri-core[client]"
-e ../huri-modules/packages/huri-events`. The tests never open an audio
device nor reach the network.

## Usage

Start a HuRI server first (huri-modules' installer, or its `deploy/`), then:

```sh
huri-cli --config config/client_full.yaml
huri-cli --config config/client_text.yaml --log-level DEBUG --log-file cli.log
```

Type a question at the `>>` prompt, `\exit` to quit (or Ctrl-C). If the
server refuses the session (a module it does not serve, a topic nobody
emits), huri-cli prints why and the modules the server has.

## Config files

A client config describes the session HuRI builds for you: `huri_url`, the
`modules` of the pipeline with their `args`, the topics the client `send`s
and the ones it `subscribe`s to. huri-modules keeps the commented
[client_template.yaml](https://github.com/Lucy-Robotics/huri-modules/blob/main/config/client_template.yaml),
and its installer writes `config/client_local.generated.yaml` (in the
huri-modules checkout) for the server it set up. This repository ships three
examples:

| File | Sends | Receives | Pipeline |
|---|---|---|---|
| [`config/client_text.yaml`](config/client_text.yaml) | typed questions | the reply as streamed text | rag |
| [`config/client_full.yaml`](config/client_full.yaml) | microphone, typed questions | speech, gestures | vad, stt, tag, emo, eag, qag, rag, tts, mov |
| [`config/client_aux.yaml`](config/client_aux.yaml) | microphone, typed questions | text, speech (saved as WAV), gestures | as `client_full` |

Each module `name` must be one the server serves; the curated ones are listed
in huri-modules'
[registry.toml](https://github.com/Lucy-Robotics/huri-modules/blob/main/registry.toml)
(`huri hub list`). The full pipelines use Piper (`tts`); against a CosyVoice3
server, use `tts_cosyvoice`.

### Topics and the `cli:` section

| Topic | Direction | What it does |
|---|---|---|
| `huri.audio.in` | sends | microphone, 16-bit mono frames |
| `huri.question` | sends | the `>>` prompt, one question per line (`\exit` quits) |
| `huri.token` | receives | prints the reply as it streams |
| `huri.question` | receives | prints the aggregated question |
| `huri.audio.out` | receives | plays the reply in order; optionally saves each utterance as WAV |
| `huri.motion` | receives | logs a bar per body part showing how much it moves; optionally saves each chunk as `.npz` |

A config asking for any other topic is refused before connecting. The `cli:`
section holds the device settings; the server never reads it, and every key
is optional:

```yaml
cli:
  audio_in:  {sample_rate: 16000, frame_duration: 0.030}  # microphone
  audio_out: {sample_rate: 44100, save_audio_dir: ""}     # "" = do not save
  motion:    {save_motion_dir: ""}                        # "" = do not save
```

The saved motion chunks (`poses`, `expressions`, `trans`, `fps`, `pts`) are
SMPL-X parameters and can be rendered offline with the EMAGE tooling.

## Write your own client

huri-cli is a few hundred lines on top of the client SDK, most of them audio
device handling. The SDK (`huri_core.core.client.HuRIClient`, in
`huri-core[client]`) owns the websocket, the handshake and the framing; you
register a handler per subscribed topic and send events. Start from
huri-core's [Client SDK](https://github.com/Lucy-Robotics/huri-core#client-sdk)
section and its
[end-to-end example](https://github.com/Lucy-Robotics/huri-core#a-minimal-end-to-end-example),
then read:

- [`huri_cli/main.py`](huri_cli/main.py): the topic tables (`SENDERS`,
  `RECEIVERS`), building the client from a config, running a session and
  reporting a refused one;
- [`huri_cli/senders.py`](huri_cli/senders.py): microphone frames and typed
  questions as events;
- [`huri_cli/audio.py`](huri_cli/audio.py) and
  [`huri_cli/viewer.py`](huri_cli/viewer.py): playing speech in order,
  showing gestures.

Depend on `huri-core[client]` (never `[server]`: a client does not need Ray)
and on the event packages whose topics you use, by version range, as
[pyproject.toml](pyproject.toml) does.

## Versions and compatibility

huri-cli follows semver on its command line and its `cli:` config section.
Releases are git tags `X.Y.Z` (no `v`) on `main`; `dev` carries the next
version. See [RELEASING.md](RELEASING.md).

| huri-cli | huri-core | huri-events |
|---|---|---|
| 0.1.x | 0.4.x (`>=0.4.0.dev0,<0.5`) | 0.1.x |

CI tests against huri-core and huri-modules at the refs set by the
`HURI_CORE_REF` and `HURI_MODULES_REF` variables of
[ci.yml](.github/workflows/ci.yml) (`dev` by default), and checks the example
configs' module names against huri-modules' `registry.toml` at that ref
([scripts/check_config_modules.py](scripts/check_config_modules.py)).

## The `huri` metapackage

[`huri-meta/`](huri-meta) is the source of `huri`, a convenience distribution
with no code: `pip install --pre huri` installs `huri-core[client]` and
`huri-cli`, everything needed to talk to a running server. It lives here
because the CLI is what it adds to the SDK; CI builds it on every change. It
has its own version (`0.0.1.dev0` today) and is released with huri-cli when
its ranges change (see [RELEASING.md](RELEASING.md)).

## License

GPL-3.0, see [LICENSE](LICENSE).
