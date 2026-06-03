#!/usr/bin/env python3
import os
import signal
import sys
import time
from collections import deque
from pathlib import Path
from threading import Event, Lock, Thread

from flush_worker import FlushWorker
from serial_reader import PiLedController, SerialReader
from web_server import start_web_server

DEFAULT_SERIAL_PORT = "/dev/ttyACM0"
DATA_FILE = Path(__file__).resolve().parents[1] / "data.bin"


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
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    reader = SerialReader(
        port=serial_port,
        queue=data_queue,
        led_controller=led_controller,
        stop_event=stop_event,
        connected_event=Event(),
    )

    if not _attempt_reader_connection(reader, timeout=10):
        print("No Arduino response after 10s; retrying a second time.")
        reader = SerialReader(
            port=serial_port,
            queue=data_queue,
            led_controller=led_controller,
            stop_event=stop_event,
            connected_event=Event(),
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
