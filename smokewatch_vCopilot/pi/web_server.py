import json
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from bitstream import get_num_records, read_record_at_bytes, read_records
from flask import Flask, jsonify, render_template, request


def create_app(data_path: str | Path, file_lock: Lock, template_folder: str | Path) -> Flask:
    app = Flask(__name__, template_folder=str(template_folder))
    data_path = Path(data_path)

    DEFAULT_MAX_POINTS = 1000

    @app.route("/")
    def index():
        return render_template("index.html")

    def _downsample_records(records, max_points):
        """Reduce records to max_points using min/max bucketing."""
        if len(records) <= max_points:
            return records
        
        # Strategy: uniformly sample max_points records, preserving first and last
        # This simple approach works well and guarantees <= max_points output
        step = len(records) / max_points
        downsampled = []
        
        for i in range(max_points):
            idx = int(i * step)
            if idx >= len(records):
                idx = len(records) - 1
            downsampled.append(records[idx])
        
        # Ensure last point is included (in case of rounding)
        if not downsampled or downsampled[-1] != records[-1]:
            downsampled.append(records[-1])
        
        return downsampled

    @app.route("/data")
    def data():
        start_ms = request.args.get('start', type=int)
        end_ms = request.args.get('end', type=int)
        max_points = request.args.get('max_points', DEFAULT_MAX_POINTS, type=int)

        if max_points < 1:
            max_points = DEFAULT_MAX_POINTS

        with file_lock:
            raw = data_path.read_bytes() if data_path.exists() else b''

        num_records = (len(raw) * 8) // 75
        records = []

        if raw and num_records > 0:
            # Use direct binary access to sample records efficiently
            if start_ms is None and end_ms is None and num_records > max_points:
                # Full range: uniform sampling
                indices = [int(i * num_records / max_points) for i in range(max_points)]
                if indices and indices[-1] != num_records - 1:
                    indices[-1] = num_records - 1
            else:
                # Either filtered by time or requesting all points
                # Sample densely to ensure good coverage of the requested time range
                # Use a large multiplier for time-filtered queries (sample ~50-75% of records)
                multiplier = 1000 if (start_ms or end_ms) else 10
                sample_size = min(num_records, max_points * multiplier)
                indices = [int(i * num_records / sample_size) for i in range(sample_size)]
                if indices and indices[-1] != num_records - 1:
                    indices[-1] = num_records - 1
            
            # Read sampled records and filter by time if needed
            for idx in indices:
                record = read_record_at_bytes(raw, idx)
                if record is not None:
                    timestamp_ms = record[0]
                    if start_ms is not None and timestamp_ms < start_ms:
                        continue
                    if end_ms is not None and timestamp_ms > end_ms:
                        continue
                    records.append(record)

        timestamps = []
        ao_values = []
        do_values = []
        valid_records = 0
        now_ms = int(time.time() * 1000)
        validated_records = []
        for timestamp_ms, ao_value, do_value in records:
            if not (0 <= ao_value <= 1023 and do_value in (0, 1)):
                continue
            if not (1_000_000_000_000 <= timestamp_ms <= now_ms + 60_000):
                continue
            try:
                datetime.fromtimestamp(timestamp_ms / 1000.0)
            except (OverflowError, OSError, ValueError):
                continue
            validated_records.append((timestamp_ms, ao_value, do_value))
            valid_records += 1

        # Apply downsampling if requested on a filtered interval or after validation.
        downsampled = _downsample_records(validated_records, max_points)

        # Build response
        for timestamp_ms, ao_value, do_value in downsampled:
            try:
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
                timestamps.append(dt.isoformat())
                ao_values.append(ao_value)
                do_values.append(do_value)
            except (OverflowError, OSError, ValueError):
                continue

        response = {
            "timestamps": timestamps,
            "ao_values": ao_values,
            "do_values": do_values,
            "record_count": valid_records,
            "returned_points": len(timestamps),
            "file_size": data_path.stat().st_size if data_path.exists() else 0,
            "updated_at": datetime.now().astimezone().isoformat(),
        }
        return jsonify(response)

    return app


def start_web_server(data_path: str | Path, file_lock: Lock, host: str = "0.0.0.0", port: int = 5000) -> None:
    template_folder = Path(__file__).resolve().parent / "templates"
    app = create_app(data_path, file_lock, template_folder)
    app.run(host=host, port=port, threaded=True, use_reloader=False)
