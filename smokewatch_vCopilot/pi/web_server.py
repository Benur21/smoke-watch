import json
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from bitstream import read_records
from flask import Flask, jsonify, render_template


def create_app(data_path: str | Path, file_lock: Lock, template_folder: str | Path) -> Flask:
    app = Flask(__name__, template_folder=str(template_folder))
    data_path = Path(data_path)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/data")
    def data():
        with file_lock:
            records = read_records(data_path)

        timestamps = []
        ao_values = []
        do_values = []
        valid_records = 0
        now_ms = int(time.time() * 1000)
        for timestamp_ms, ao_value, do_value in records:
            if not (0 <= ao_value <= 1023 and do_value in (0, 1)):
                continue
            if not (1_000_000_000_000 <= timestamp_ms <= now_ms + 60_000):
                continue
            try:
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
            except (OverflowError, OSError, ValueError):
                continue
            timestamps.append(dt.isoformat())
            ao_values.append(ao_value)
            do_values.append(do_value)
            valid_records += 1

        response = {
            "timestamps": timestamps,
            "ao_values": ao_values,
            "do_values": do_values,
            "record_count": valid_records,
            "file_size": data_path.stat().st_size if data_path.exists() else 0,
            "updated_at": datetime.now().astimezone().isoformat(),
        }
        return jsonify(response)

    return app


def start_web_server(data_path: str | Path, file_lock: Lock, host: str = "0.0.0.0", port: int = 5000) -> None:
    template_folder = Path(__file__).resolve().parent / "templates"
    app = create_app(data_path, file_lock, template_folder)
    app.run(host=host, port=port, threaded=True, use_reloader=False)
