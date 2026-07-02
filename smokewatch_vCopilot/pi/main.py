#!/usr/bin/env python3
import os
import signal
import sys
import time
from collections import deque
from pathlib import Path
from threading import Event, Lock, Thread

from flush_worker import FlushWorker
from ntfy_client import NtfyNotifier
from serial_reader import PiLedController, SerialReader
from web_server import start_web_server

DEFAULT_SERIAL_PORT = "/dev/ttyACM0"
DATA_FILE = Path(__file__).resolve().parents[1] / "data.bin"
DEFAULT_ALERT_THRESHOLD = 120
DEFAULT_NTFY_SERVER = "https://ntfy.sh"


def _get_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        print(f"Invalid {name} value {raw_value!r}; using {default}.")
        return default


def _attempt_reader_connection(reader: SerialReader, timeout: float) -> bool:
    reader.start()
    connected = reader.connected_event.wait(timeout=timeout)
    if not connected:
        reader.request_stop()
        reader.join(timeout=2)
    return connected


def main() -> int:
    stop_event = Event()
    file_lock = Lock()
    data_queue = deque()
    led_controller = PiLedController()
    serial_port = os.environ.get("SMOKEWATCH_SERIAL_PORT", DEFAULT_SERIAL_PORT)
    alert_threshold = _get_env_int("SMOKEWATCH_ALERT_THRESHOLD", DEFAULT_ALERT_THRESHOLD)
    ntfy_topic = os.environ.get("SMOKEWATCH_NTFY_TOPIC", "").strip()
    ntfy_server = os.environ.get("SMOKEWATCH_NTFY_SERVER", DEFAULT_NTFY_SERVER).strip() or DEFAULT_NTFY_SERVER
    ntfy_title = os.environ.get("SMOKEWATCH_NTFY_TITLE", "SmokeWatch alerta").strip() or "SmokeWatch alerta"
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    notifier = NtfyNotifier(topic=ntfy_topic, server=ntfy_server, title=ntfy_title)

    reader = SerialReader(
        port=serial_port,
        queue=data_queue,
        led_controller=led_controller,
        stop_event=stop_event,
        connected_event=Event(),
        alert_threshold=alert_threshold,
        notifier=notifier,
    )

    if not _attempt_reader_connection(reader, timeout=10):
        print("No Arduino response after 10s; retrying a second time.")
        reader = SerialReader(
            port=serial_port,
            queue=data_queue,
            led_controller=led_controller,
            stop_event=stop_event,
            connected_event=Event(),
            alert_threshold=alert_threshold,
            notifier=notifier,
        )
        if not _attempt_reader_connection(reader, timeout=10):
            print("Arduino absent after second attempt. LED ACT apagado. Terminando.")
            led_controller.off()
            return 1

    flush_worker = FlushWorker(
        queue=data_queue,
        data_path=DATA_FILE,
        file_lock=file_lock,
        stop_event=stop_event,
        batch_size=300,
    )
    flush_worker.start()

    web_thread = Thread(
        target=start_web_server,
        args=(DATA_FILE, file_lock),
        kwargs={"host": "0.0.0.0", "port": 5000},
        daemon=True,
    )
    web_thread.start()

    def _shutdown(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event.is_set():
            if not reader.is_alive():
                print("Serial reader thread stopped unexpectedly.")
                stop_event.set()
                break
            time.sleep(1)
    finally:
        stop_event.set()
        reader.request_stop()
        reader.join(timeout=5)
        flush_worker.join(timeout=5)
        led_controller.off()
        print("SmokeWatch encerrado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
