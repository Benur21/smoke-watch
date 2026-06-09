#!/usr/bin/env python3
"""
Quick test script for the new /data endpoint with downsampling.
Verifies:
  - max_points parameter works
  - start/end filtering works
  - downsampling reduces records appropriately
  - JSON response structure is correct
"""
import sys
import tempfile
from pathlib import Path
from threading import Lock

# Add the pi folder to path for imports
sys.path.insert(0, str(Path(__file__).parent / "smokewatch_vCopilot" / "pi"))

from bitstream import append_records
from web_server import create_app

def test_downsampling():
    """Test the downsampling logic."""
    print("Testing downsampling with max_points parameter...")
    
    # Create a temporary data file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        temp_data_path = Path(f.name)
    
    try:
        # Create test records: more points than the default max_points
        test_records = []
        base_time = 1718000000000  # Some timestamp in milliseconds
        for i in range(1500):
            timestamp_ms = base_time + (i * 1000)  # 1 second apart
            ao_value = (500 + i % 500)  # Varying values 500-999
            do_value = i % 2  # Alternating 0 and 1
            test_records.append((timestamp_ms, ao_value, do_value))
        
        # Write test records to file
        file_lock = Lock()
        append_records(temp_data_path, test_records, lock=file_lock)
        
        # Create Flask app
        template_folder = Path(__file__).parent / "smokewatch_vCopilot" / "pi" / "templates"
        app = create_app(temp_data_path, file_lock, template_folder)
        
        # Test with Flask test client
        with app.test_client() as client:
            # Test 1: Get all data with max_points=100
            print("\nTest 1: Requesting max_points=100 for 1500 records...")
            resp = client.get('/data?max_points=100')
            data = resp.get_json()
            print(f"  Returned {len(data['timestamps'])} points out of {data['record_count']} total")
            print(f"  Expected: ~100, Got: {len(data['timestamps'])}")
            assert data['record_count'] == 1500, "Should report total complete records in the file"
            assert len(data['timestamps']) <= 100, "Should have at most 100 points"
            print("  ✓ Pass")
            
            # Test 2: Get all data without max_points (should default to 1000)
            print("\nTest 2: Requesting without max_points (default 1000)...")
            resp = client.get('/data')
            data = resp.get_json()
            print(f"  Returned {len(data['timestamps'])} points")
            assert data['record_count'] == 1500, "Should report 1500 total records"
            assert len(data['timestamps']) <= 1000, "Should use default max_points"
            print("  ✓ Pass")
            
            # Test 3: Request with time interval
            print("\nTest 3: Requesting with time interval (start/end)...")
            start_time = base_time + 200000  # Start at record 200
            end_time = base_time + 300000    # End at record 300
            resp = client.get(f'/data?start={start_time}&end={end_time}&max_points=50')
            data = resp.get_json()
            print(f"  Returned {len(data['timestamps'])} points in interval")
            assert len(data['timestamps']) > 0, "Should have returned some points"
            assert len(data['timestamps']) <= 50, "Should have at most 50 points"
            assert data['filtered_record_count'] == 101, "Should count records in the selected interval"
            print("  ✓ Pass")
            
            # Test 4: Check response structure
            print("\nTest 4: Checking response structure...")
            resp = client.get('/data?max_points=100')
            data = resp.get_json()
            required_keys = {'timestamps', 'ao_values', 'do_values', 'record_count', 'filtered_record_count', 'returned_points', 'file_size', 'updated_at'}
            assert all(k in data for k in required_keys), f"Missing keys. Got: {set(data.keys())}"
            print(f"  Response keys: {set(data.keys())}")
            print("  ✓ Pass")
        
        print("\n✅ All tests passed!")
        
    finally:
        # Cleanup
        temp_data_path.unlink(missing_ok=True)

if __name__ == "__main__":
    test_downsampling()
