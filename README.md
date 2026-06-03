# SmokeWatch

SmokeWatch is a local air-quality monitoring stack built around an Arduino UNO, an MQ-135 sensor, and a Raspberry Pi. The Arduino samples the sensor once per second and sends `AO,DO` readings over serial. The Pi timestamps those readings, buffers them in RAM, writes them to `data.bin` as compact 75-bit records, and serves a browser dashboard on the local network.

## Repository Layout

This repository contains two standalone implementations of the same project:

- `smokewatch_vCopilot/` - refactored layout with a `pi/` subdirectory and a bundled `requirements.txt`.
- `smokewatch_vClaude/` - earlier flat layout with the same core pipeline.

Each variant has its own README with variant-specific notes.

## Hardware Wiring

MQ-135 to Arduino UNO:

- `VCC` -> `5V`
- `GND` -> `GND`
- `AO` -> `A0`
- `DO` -> `D2`

The Arduino sketch also mirrors `DO` on the onboard LED at pin `13`.

## Runtime Flow

1. The Arduino reads the analog and digital outputs from the sensor and streams them at `9600` baud.
2. The Pi reads each serial line, validates the values, and adds a millisecond timestamp.
3. A flush worker keeps readings in RAM and appends them to `data.bin` in batches of 300 records.
4. A Flask app exposes a dashboard at `/` and JSON data at `/data` for the browser UI.
5. The Pi ACT LED is turned on while the serial link is healthy.

## Data Format

Each record in `data.bin` uses 75 bits:

- 64 bits - Unix timestamp in milliseconds
- 10 bits - analog value (`AO`)
- 1 bit - digital value (`DO`)

This compact format keeps storage overhead low while still preserving the full history stream.

## Requirements

- Python 3.10 or newer
- `Flask`
- `pyserial`
- Arduino IDE for flashing the sketch

## Quick Start

### `smokewatch_vCopilot`

```bash
cd smokewatch_vCopilot
python3 -m pip install -r requirements.txt
python3 pi/main.py
```

Set a custom serial port if needed:

```bash
export SMOKEWATCH_SERIAL_PORT=/dev/ttyACM0
```

### `smokewatch_vClaude`

```bash
cd smokewatch_vClaude
python3 -m pip install flask pyserial
python3 main.py
```

If the Arduino is not on `/dev/ttyACM0`, update `config.py` before starting the app.

## Browser Dashboard

Open the Pi in a browser on the same network:

```text
http://<pi-ip>:5000
```

Useful endpoint:

- `GET /data` - returns timestamps, AO values, DO values, record count, file size, and the last update time.

To find the Pi IP:

```bash
hostname -I
```

## systemd

Each variant includes a `smokewatch.service` unit. Before enabling it, update the hard-coded `WorkingDirectory` and `ExecStart` paths so they match your checkout location.

Example for the `smokewatch_vCopilot` layout:

```bash
sudo cp smokewatch_vCopilot/pi/smokewatch.service /etc/systemd/system/smokewatch.service
sudo systemctl daemon-reload
sudo systemctl enable smokewatch.service
sudo systemctl start smokewatch.service
```

## Variant Docs

- [smokewatch_vCopilot/README.md](smokewatch_vCopilot/README.md)
- [smokewatch_vClaude/README.md](smokewatch_vClaude/README.md)
