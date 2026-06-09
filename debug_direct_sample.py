#!/usr/bin/env python3
"""Debug time filtering using direct binary access."""

import sys
from pathlib import Path
from datetime import datetime

# Add pi directory to path
sys.path.insert(0, str(Path(__file__).parent / "smokewatch_vCopilot" / "pi"))

from bitstream import read_record_at_bytes

# Setup
data_file = Path(__file__).parent / "smokewatch_vCopilot" / "pi" / "data.bin"

if not data_file.exists():
    print(f"ERROR: {data_file} not found")
    sys.exit(1)

raw = data_file.read_bytes()
num_records = (len(raw) * 8) // 75

print(f"Data file: {data_file} ({len(raw)} bytes)")
print(f"Total records (estimate): {num_records}")
print()

# Sample every Nth record to see timestamp distribution
print("Sampling every 100th record:")
for i in range(0, num_records, max(1, num_records // 20)):
    record = read_record_at_bytes(raw, i)
    if record:
        ts_ms, ao, do = record
        dt = datetime.fromtimestamp(ts_ms / 1000.0)
        print(f"  Record {i:6d}: {dt.isoformat()}")

print()

# Get first record details
first_record = read_record_at_bytes(raw, 0)
if first_record:
    first_ts_ms = first_record[0]
    first_dt = datetime.fromtimestamp(first_ts_ms / 1000.0)
    print(f"First record: {first_ts_ms} ms = {first_dt.isoformat()}")

# Get last record details
last_record = read_record_at_bytes(raw, num_records - 1)
if last_record:
    last_ts_ms = last_record[0]
    last_dt = datetime.fromtimestamp(last_ts_ms / 1000.0)
    print(f"Last record:  {last_ts_ms} ms = {last_dt.isoformat()}")

print()

# Estimate records per hour
if first_record and last_record:
    duration_ms = last_ts_ms - first_ts_ms
    duration_hours = duration_ms / (1000 * 3600)
    records_per_hour = num_records / max(1, duration_hours)
    print(f"Duration: {duration_hours:.1f} hours")
    print(f"Records per hour: {records_per_hour:.0f}")
