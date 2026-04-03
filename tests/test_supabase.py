"""
Test Supabase connection and fetch patient data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("SUPABASE CONNECTION TEST")
print("=" * 80)

# Check environment variables
print("\n1. Checking environment variables...")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if supabase_url and supabase_key:
    print(f"   ✅ SUPABASE_URL: {supabase_url}")
    print(f"   ✅ SUPABASE_SERVICE_ROLE_KEY: {'*' * 20}...{supabase_key[-10:]}")
else:
    print("   ❌ Missing Supabase credentials in .env file")
    sys.exit(1)

# Test connection
print("\n2. Testing Supabase connection...")
from utils.supabase_client import test_connection, list_all_patients, get_patient_timeline

if test_connection():
    print("\n3. Fetching patient list...")
    patients = list_all_patients()
    
    if patients:
        print(f"   Found {len(patients)} patients:")
        for p in patients:
            print(f"   - ID: {p.get('patient_id')}")
            print(f"     Age: {p.get('age')} {p.get('gender')}")
            print(f"     Diagnosis: {p.get('admission_diagnosis')}")
            print()
        
        # Test fetching timeline for first patient
        if len(patients) > 0:
            test_patient_id = patients[0].get('patient_id')
            print(f"4. Fetching timeline for patient {test_patient_id}...")
            timeline = get_patient_timeline(test_patient_id)
            print(f"   Found {len(timeline)} timeline events")
            
            if timeline:
                print("\n   Timeline preview:")
                for event in timeline[:3]:  # Show first 3 events
                    print(f"   - Hour {event.get('hours_since_admission')}: {event.get('time_label')}")
                    vitals = event.get('vitals', {})
                    labs = event.get('labs', {})
                    print(f"     HR: {vitals.get('heart_rate')}, BP: {vitals.get('systolic_bp')}/{vitals.get('diastolic_bp')}")
                    print(f"     WBC: {labs.get('wbc')}, Lactate: {labs.get('lactate')}")
    else:
        print("   ⚠️ No patients found in database")
        print("   Make sure you've uploaded patient data to Supabase")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
