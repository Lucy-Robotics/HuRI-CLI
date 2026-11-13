"""huri-cli: wiring, audio playback, motion viewer."""

import asyncio
import json
import logging
import re
import wave
from pathlib import Path

import numpy as np
import pytest
import websockets
from huri_core.core.dataclasses.config import ClientConfig
from huri_events.audio import Audio
from huri_events.motion import Motion
from omegaconf import OmegaConf

import huri_cli.main as cli_main
from huri_cli.audio import AudioPlayer
from huri_cli.main import RECEIVERS, SENDERS, build_client, run
from huri_cli.viewer import MotionViewer, part_activity

ROOT = Path(__file__).resolve().parents[1]
# The client configs this repository ships (config/), not huri-modules' ones.
CONFIGS = sorted((ROOT / "config").glob("client_*.yaml"))


def config_of(path, **overrides):
    raw = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
    return ClientConfig.from_dict({**raw, "user_id": "test", **overrides}), raw.get(
        "cli", {}
    )


def test_the_example_configs_are_shipped():
    assert [p.name for p in CONFIGS] == [
        "client_aux.yaml",
        "client_full.yaml",
        "client_text.yaml",
    ]


@pytest.mark.parametrize("path", CONFIGS, ids=lambda p: p.name)
def test_shipped_configs_only_use_topics_the_cli_handles(path):
    config, cli = config_of(path)
    assert set(config.send) <= set(SENDERS)
    assert set(config.subscribe) <= set(RECEIVERS)
    client = build_client(config, {})  # no device is opened before audio arrives
    assert client.handshake()["subscribe"] == sorted(config.subscribe)


def test_unsupported_topic_is_reported_with_the_supported_ones():
    config, _ = config_of(CONFIGS[0], subscribe=["acme.servo_angles"])
    with pytest.raises(ValueError, match="acme.servo_angles.*receives"):
        build_client(config, {})


def test_main_reports_a_missing_config(tmp_path, caplog, capsys):
    path = tmp_path / "nope.yaml"
    with pytest.raises(SystemExit) as exc:
        cli_main.main(["--config", str(path)])
    assert exc.value.code == 1
    (message,) = caplog.messages
    assert str(path) in message and "No such file" in message
    assert len(message.splitlines()) == 1
    assert "Traceback" not in caplog.text + capsys.readouterr().err


def test_main_reports_invalid_yaml(tmp_path, caplog, capsys):
    path = tmp_path / "broken.yaml"
    path.write_text("a: [")
    with pytest.raises(SystemExit) as exc:
        cli_main.main(["--config", str(path)])
    assert exc.value.code == 1
    (message,) = caplog.messages
    assert str(path) in message and re.search(r"line \d+", message)
    assert len(message.splitlines()) == 1
    assert "Traceback" not in caplog.text + capsys.readouterr().err


@pytest.mark.parametrize("contents", ["[]", "huri_url: ${missing}"])
def test_main_reports_config_loading_errors(contents, tmp_path, caplog):
    path = tmp_path / "invalid.yaml"
    path.write_text(contents)
    with pytest.raises(SystemExit) as exc:
        cli_main.main(["--config", str(path)])
    assert exc.value.code == 1
    (message,) = caplog.messages
    assert str(path) in message and len(message.splitlines()) == 1
    assert "Traceback" not in caplog.text


def test_main_reports_invalid_server_url(tmp_path, caplog, capsys):
    path = tmp_path / "bad_url.yaml"
    path.write_text(
        f"huri_url: localhost:8000\nuser_id_file_path: {tmp_path / 'user_id'}\n"
    )
    with pytest.raises(SystemExit) as exc:
        cli_main.main(["--config", str(path)])
    assert exc.value.code == 1
    (message,) = caplog.messages
    assert "localhost:8000" in message and "ws://" in message and "wss://" in message
    assert len(message.splitlines()) == 1
    assert "Traceback" not in caplog.text + capsys.readouterr().err


def test_main_refuses_unknown_log_level(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        cli_main.main(
            ["--config", str(tmp_path / "unused.yaml"), "--log-level", "verbose"]
        )
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "usage:" in error and "--log-level" in error
    assert all(
        level in error for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    )
    assert "Traceback" not in error


def test_main_accepts_lowercase_debug(tmp_path, monkeypatch, caplog):
    path = tmp_path / "valid.yaml"
    path.write_text(f"user_id_file_path: {tmp_path / 'user_id'}\n")
    configured = []

    def configure(**kwargs):
        configured.append(kwargs["level"])
        monkeypatch.setattr(logging.getLogger(), "level", logging.DEBUG)

    class Client:
        user_id = "test"

        async def connect(self):
            logging.getLogger("huri_cli").debug("connected test client")

        async def wait_closed(self):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(logging, "basicConfig", configure)
    monkeypatch.setattr(cli_main, "build_client", lambda config, cli: Client())
    with pytest.raises(SystemExit) as exc:
        cli_main.main(["--config", str(path), "--log-level", "debug"])
    assert exc.value.code == 0
    assert configured == ["DEBUG"]
    assert "connected test client" in caplog.messages
    assert "session started, user_id=test" in caplog.messages


# --- audio ---------------------------------------------------------------------


class FakeOutput:
    def __init__(self, rate, log):
        self.rate, self.log = rate, log

    def write(self, pcm):
        self.log.append((self.rate, pcm.size))

    def stop(self):
        pass

    def close(self):
        pass


def chunk(n, rate=24000, end=False, pts=0.0):
    return Audio(
        data=np.full(n, 0.5, dtype=np.float32), sample_rate=rate, end=end, pts=pts
    )


def test_audio_is_played_in_order_at_the_tts_rate():
    log = []
    player = AudioPlayer(open_output=lambda rate: FakeOutput(rate, log))

    async def play():
        for n in (100, 200, 300):
            await player(chunk(n))

    asyncio.run(play())
    assert log == [(24000, 100), (24000, 200), (24000, 300)]


def test_audio_falls_back_to_resampling_when_the_device_refuses_the_rate():
    log = []

    def open_output(rate):
        if rate != 44100:
            raise RuntimeError("Invalid sample rate")
        return FakeOutput(rate, log)

    player = AudioPlayer(sample_rate=44100, open_output=open_output)
    asyncio.run(player(chunk(240)))
    assert log == [(44100, 441)]


def test_each_utterance_is_saved_at_its_own_rate(tmp_path):
    player = AudioPlayer(
        save_audio_dir=str(tmp_path), open_output=lambda r: FakeOutput(r, [])
    )

    async def play():
        await player(chunk(100))
        await player(chunk(50, end=True))

    asyncio.run(play())
    (path,) = tmp_path.glob("utt-000-*.wav")
    with wave.open(str(path)) as wav:
        assert wav.getframerate() == 24000 and wav.getnframes() == 150


def test_playback_errors_do_not_stop_the_session():
    class Broken(FakeOutput):
        def write(self, pcm):
            raise OSError("device unplugged")

    player = AudioPlayer(open_output=lambda rate: Broken(rate, []))
    asyncio.run(player(chunk(10)))  # logged, not raised


# --- motion ----------------------------------------------------------------------


def motion(frames=4, moving_joint=None, pts=1.0):
    poses = np.zeros((frames, 165), dtype=np.float32)
    if moving_joint is not None:
        poses[:, moving_joint * 3] = np.linspace(0, 0.3, frames)
    return Motion(
        poses=poses,
        expressions=np.zeros((frames, 100), dtype=np.float32),
        trans=np.zeros((frames, 3), dtype=np.float32),
        pts=pts,
    )


def test_activity_is_attributed_to_the_moving_body_part():
    still = part_activity(motion().poses)
    assert all(v == 0.0 for v in still.values())
    activity = part_activity(motion(moving_joint=19).poses)  # right elbow
    assert activity["r_arm"] > 0 and activity["l_arm"] == 0 and activity["head"] == 0


def test_viewer_renders_a_line_and_saves_chunks(tmp_path):
    viewer = MotionViewer(save_motion_dir=str(tmp_path))
    line = viewer.render(motion(moving_joint=19))
    assert "4f @30fps" in line and "r_arm" in line
    asyncio.run(viewer(motion(moving_joint=19)))
    saved = np.load(tmp_path / "motion-0000.npz")
    assert saved["poses"].shape == (4, 165) and float(saved["pts"]) == 1.0


# --- session lifecycle -----------------------------------------------------------


def test_run_ends_cleanly_when_the_server_closes_the_session():
    async def server(ws):
        await ws.recv()
        await ws.send(json.dumps({"type": "session_init", "user_id": "u"}))
        await ws.close()

    async def scenario():
        async with websockets.serve(server, "127.0.0.1", 0) as srv:
            port = srv.sockets[0].getsockname()[1]
            config, _ = config_of(
                ROOT / "config/client_text.yaml",
                huri_url=f"ws://127.0.0.1:{port}",
                send=[],
            )
            return await asyncio.wait_for(run(config), timeout=10)

    assert asyncio.run(scenario()) == 0


def test_run_reports_a_rejected_session():
    async def server(ws):
        await ws.recv()
        await ws.send(json.dumps({"type": "session_error", "error": "nope"}))

    async def scenario():
        async with websockets.serve(server, "127.0.0.1", 0) as srv:
            port = srv.sockets[0].getsockname()[1]
            config, _ = config_of(
                ROOT / "config/client_text.yaml", huri_url=f"ws://127.0.0.1:{port}"
            )
            return await asyncio.wait_for(run(config), timeout=10)

    assert asyncio.run(scenario()) == 1
