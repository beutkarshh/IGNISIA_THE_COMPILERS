#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database.supabase_client import get_supabase_client

def main():
    client = get_supabase_client()
    
    # Check live_telemetry for patient 10006
    result = client.table('live_telemetry').select('*').eq('subject_id', 10006).limit(10).execute()
    print(f"Patient 10006 telemetry records: {len(result.data)}")
    
    if result.data:
        print("\nFirst few records:")
        for r in result.data[:3]:
            print(f"  subject_id: {r['subject_id']}, itemid: {r['itemid']}, valuenum: {r['valuenum']}, charttime: {r['charttime']}")
    
    # Check for HR data (itemids 211, 220045)
    hr_result = client.table('live_telemetry').select('*').eq('subject_id', 10006).in_('itemid', [211, 220045]).limit(5).execute()
    print(f"\nHeart Rate data (itemids 211, 220045): {len(hr_result.data)} records")
    
    # Check for MAP data
    map_itemids = [456, 52, 6702, 443, 220052, 220181, 225312]
    map_result = client.table('live_telemetry').select('*').eq('subject_id', 10006).in_('itemid', map_itemids).limit(5).execute()
    print(f"MAP data (itemids {map_itemids}): {len(map_result.data)} records")

if __name__ == "__main__":
    main()