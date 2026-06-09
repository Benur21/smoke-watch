#!/usr/bin/env python3
"""Debug time filtering in /data endpoint."""

import sys
import time
from pathlib import Path
from threading import Lock
from datetime import datetime, timedelta

# Add pi directory to path
sys.path.insert(0, str(Path(__file__).parent / "smokewatch_vCopilot" / "pi"))

from bitstream import get_num_records, read_records

# Setup
data_file = Path(__file__).parent / "smokewatch_vCopilot" / "pi" / "data.bin"

if not data_file.exists():
    print(f"ERROR: {data_file} not found")
    sys.exit(1)

print(f"Data file: {data_file} ({data_file.stat().st_size} bytes)")
print()

# Read all records
records = read_records(data_file)
print(f"Total records: {len(records)}")
print()

# Show first few timestamps
print("First 10 timestamps:")
for i, (ts_ms, ao, do) in enumerate(records[:10]):
    dt = datetime.fromtimestamp(ts_ms / 1000.0)
    print(f"  {i}: {ts_ms} ms = {dt.isoformat()}")

print()

# Calculate first hour range
first_ts_ms = records[0][0]
first_dt = datetime.fromtimestamp(first_ts_ms / 1000.0)
end_dt = first_dt + timedelta(hours=1)
end_ts_ms = int(end_dt.timestamp() * 1000)

print(f"First timestamp: {first_ts_ms} ms = {first_dt.isoformat()}")
print(f"End of first hour: {end_ts_ms} ms = {end_dt.isoformat()}")
print()

# Count records in first hour
count_in_hour = 0
for ts_ms, ao, do in records:
    if first_ts_ms <= ts_ms <= end_ts_ms:
        count_in_hour += 1

print(f"Records in first hour: {count_in_hour}")
print()

# Show some records in first hour range
print("Sample records in first hour:")
for i, (ts_ms, ao, do) in enumerate(records):
    if ts_ms > end_ts_ms:
        break
    if i % max(1, count_in_hour // 5) == 0:
        dt = datetime.fromtimestamp(ts_ms / 1000.0)
        print(f"  {i}: {ts_ms} ms = {dt.isoformat()}")
