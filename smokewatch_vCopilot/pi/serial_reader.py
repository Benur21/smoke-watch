import threading
import time
from collections import deque
from pathlib import Path

import serial
from serial import SerialException


class PiLedController:
    def __init__(self) -> None:
        self.base_path = Path("/sys/class/leds")
        self.led_path = self._detect_led_path()
        self._set_trigger("none")

    def _detect_led_path(self) -> Path:
        for candidate in ("ACT", "led0"):
            path = self.base_path / candidate
            if path.exists():
                return path
        raise FileNotFoundError("Pi ACT LED sysfs path not found")

    def _set_trigger(self, trigger_value: str) -> None:
        trigger_file = self.led_path / "trigger"
        trigger_file.write_text(trigger_value, encoding="utf-8")

    def _set_brightness(self, value: int) -> None:
        brightness_file = self.led_path / "brightness"
        brightness_file.write_text(str(value), encoding="utf-8")

    def on(self) -> None:
        self._set_brightness(1)

    def off(self) -> None:
        self._set_brightness(0)


class SerialReader(threading.Thread):
    def __init__(
        self,
        port: str,
        queue: deque,
        led_controller: PiLedController,
        stop_event: threading.Event,
        connected_event: threading.Event,
        baudrate: int = 9600,
    ) -> None:
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.queue = queue
        self.led_controller = led_controller
        self.stop_event = stop_event
        self.connected_event = connected_event
        self.serial = None
        self._lock = threading.Lock()

    def request_stop(self) -> None:
        self.stop_event.set()
        with self._lock:
            if self.serial and self.serial.is_open:
                self.serial.close()

    def parse_line(self, line: str) -> tuple[int, int] | None:
        payload = line.strip()
        if not payload:
            return None
        parts = payload.split(",")
        if len(parts) != 2:
            return None
        try:
            ao_value = int(parts[0].strip())
            do_value = int(parts[1].strip())
        except ValueError:
            return None

        if not (0 <= ao_value <= 1023) or do_value not in (0, 1):
            return None
        return ao_value, do_value

    def run(self) -> None:
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                self.serial = ser
                self.led_controller.on()
                start_time = time.monotonic()
                while not self.stop_event.is_set():
                    line = ser.readline().decode("utf-8", errors="ignore")
                    parsed = self.parse_line(line)
                    if parsed is None:
                        if time.monotonic() - start_time >= 10:
                            return
                        continue

                    ao_value, do_value = parsed
                    self.queue.append((int(time.time() * 1_000), ao_value, do_value))
                    self.connected_event.set()
                    start_time = time.monotonic()

                    while not self.stop_event.is_set():
                        line = ser.readline().decode("utf-8", errors="ignore")
                        if not line:
                            if time.monotonic() - start_time > 10:
                                self.led_controller.off()
                                return
                            continue
                        parsed = self.parse_line(line)
                        if parsed is None:
                            continue
                        ao_value, do_value = parsed
                        self.queue.append((int(time.time() * 1_000), ao_value, do_value))
                        start_time = time.monotonic()
        except SerialException:
            return
        except FileNotFoundError:
            return
        finally:
            self.led_controller.off()
