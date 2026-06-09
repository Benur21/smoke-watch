#!/usr/bin/env python3
"""Test /data endpoint with real data.bin to diagnose max_points issue."""

import sys
import time
from pathlib import Path
from threading import Lock

# Add pi directory to path
sys.path.insert(0, str(Path(__file__).parent / "smokewatch_vCopilot" / "pi"))

from web_server import create_app

# Setup
data_file = Path(__file__).parent / "smokewatch_vCopilot" / "pi" / "data.bin"
template_dir = Path(__file__).parent / "smokewatch_vCopilot" / "pi" / "templates"

if not data_file.exists():
    print(f"ERROR: {data_file} not found")
    sys.exit(1)

print(f"Data file: {data_file} ({data_file.stat().st_size} bytes)")
print()

# Create app with file lock
file_lock = Lock()
app = create_app(data_file, file_lock, template_dir)
client = app.test_client()

# Test 1: Full range with max_points=100
print("Test 1: Full range, max_points=100")
start = time.time()
response = client.get("/data?max_points=100")
elapsed = time.time() - start
payload = response.get_json()
print(f"  Status: {response.status_code}")
print(f"  Time: {elapsed:.3f}s")
print(f"  Record count: {payload['record_count']}")
print(f"  Returned points: {payload['returned_points']}")
print(f"  Expected: ~100, Got: {payload['returned_points']}")
print()

# Test 2: Full range with max_points=50
print("Test 2: Full range, max_points=50")
start = time.time()
response = client.get("/data?max_points=50")
elapsed = time.time() - start
payload = response.get_json()
print(f"  Status: {response.status_code}")
print(f"  Time: {elapsed:.3f}s")
print(f"  Record count: {payload['record_count']}")
print(f"  Returned points: {payload['returned_points']}")
print(f"  Expected: ~50, Got: {payload['returned_points']}")
print()

# Test 3: Full range with default (1000)
print("Test 3: Full range, default max_points")
start = time.time()
response = client.get("/data")
elapsed = time.time() - start
payload = response.get_json()
print(f"  Status: {response.status_code}")
print(f"  Time: {elapsed:.3f}s")
print(f"  Record count: {payload['record_count']}")
print(f"  Returned points: {payload['returned_points']}")
print()

# Test 4: Time range (first hour of data)
print("Test 4: Time range (first hour), max_points=100")
# Get first timestamp from full data
response = client.get("/data")
payload = response.get_json()
if payload['timestamps']:
    first_ts_str = payload['timestamps'][0]
    import dateutil.parser
    first_dt = dateutil.parser.isoparse(first_ts_str)
    first_ms = int(first_dt.timestamp() * 1000)
    end_ms = first_ms + 3600000  # +1 hour
    
    start = time.time()
    response = client.get(f"/data?start={first_ms}&end={end_ms}&max_points=100")
    elapsed = time.time() - start
    payload = response.get_json()
    print(f"  Status: {response.status_code}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Record count: {payload['record_count']}")
    print(f"  Returned points: {payload['returned_points']}")
    print(f"  Expected: ~100, Got: {payload['returned_points']}")

print("\n✅ Tests complete!")
