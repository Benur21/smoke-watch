import time
from datetime import datetime
from pathlib import Path
from threading import Lock

from bitstream import RECORD_BITS, read_record_at_bytes
from flask import Flask, jsonify, render_template, request


def create_app(data_path: str | Path, file_lock: Lock, template_folder: str | Path) -> Flask:
    app = Flask(__name__, template_folder=str(template_folder))
    data_path = Path(data_path)

    DEFAULT_MAX_POINTS = 1000

    @app.route("/")
    def index():
        return render_template("index.html")

    def _downsample_records(records, max_points):
        """Reduce records to max_points while preserving the first and last point."""
        if len(records) <= max_points:
            return records
        if max_points == 1:
            return [records[0]]

        step = (len(records) - 1) / (max_points - 1)
        downsampled = []

        for i in range(max_points):
            idx = int(i * step)
            downsampled.append(records[idx])

        return downsampled

    def _timestamp_at(raw: bytes, index: int) -> int | None:
        record = read_record_at_bytes(raw, index)
        if record is None:
            return None
        return record[0]

    def _first_index_at_or_after(raw: bytes, num_records: int, timestamp_ms: int) -> int:
        low = 0
        high = num_records
        while low < high:
            mid = (low + high) // 2
            mid_timestamp = _timestamp_at(raw, mid)
            if mid_timestamp is None or mid_timestamp < timestamp_ms:
                low = mid + 1
            else:
                high = mid
        return low

    def _first_index_after(raw: bytes, num_records: int, timestamp_ms: int) -> int:
        low = 0
        high = num_records
        while low < high:
            mid = (low + high) // 2
            mid_timestamp = _timestamp_at(raw, mid)
            if mid_timestamp is None or mid_timestamp <= timestamp_ms:
                low = mid + 1
            else:
                high = mid
        return low

    def _select_index_window(raw: bytes, num_records: int, start_ms: int | None, end_ms: int | None) -> tuple[int, int]:
        if start_ms is not None and end_ms is not None and start_ms > end_ms:
            return 0, 0

        start_index = 0
        end_index = num_records

        if start_ms is not None:
            start_index = _first_index_at_or_after(raw, num_records, start_ms)
        if end_ms is not None:
            end_index = _first_index_after(raw, num_records, end_ms)

        if end_index < start_index:
            end_index = start_index
        return start_index, end_index

    def _sample_indices(start_index: int, end_index: int, max_points: int) -> list[int]:
        count = end_index - start_index
        if count <= 0:
            return []
        if count <= max_points:
            return list(range(start_index, end_index))
        if max_points == 1:
            return [start_index]

        span = count - 1
        return [
            start_index + int((i * span) / (max_points - 1))
            for i in range(max_points)
        ]

    @app.route("/data")
    def data():
        start_ms = request.args.get('start', type=int)
        end_ms = request.args.get('end', type=int)
        max_points = request.args.get('max_points', DEFAULT_MAX_POINTS, type=int)

        if max_points < 1:
            max_points = DEFAULT_MAX_POINTS

        with file_lock:
            raw = data_path.read_bytes() if data_path.exists() else b''

        num_records = (len(raw) * 8) // RECORD_BITS
        records = []
        filtered_record_count = 0

        if raw and num_records > 0:
            start_index, end_index = _select_index_window(raw, num_records, start_ms, end_ms)
            filtered_record_count = end_index - start_index
            indices = _sample_indices(start_index, end_index, max_points)

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
            "record_count": num_records,
            "filtered_record_count": filtered_record_count,
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
