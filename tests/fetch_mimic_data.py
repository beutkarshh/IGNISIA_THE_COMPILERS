"""
Fetch MIMIC-III data from Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("=" * 80)
print("FETCHING MIMIC-III DATA FROM SUPABASE")
print("=" * 80)

# Check for common MIMIC-III tables
mimic_tables = [
    'patients',
    'admissions', 
    'chartevents',
    'labevents',
    'noteevents',
    'diagnoses_icd',
    'icustays'
]

available_tables = []

print("\n1. Discovering tables...")
for table in mimic_tables:
    try:
        response = supabase.table(table).select('*').limit(1).execute()
        if response.data is not None:
            available_tables.append(table)
            row_count_response = supabase.table(table).select('*', count='exact').limit(0).execute()
            count = row_count_response.count if hasattr(row_count_response, 'count') else '?'
            print(f"   ✅ {table}: {count} rows")
            if len(response.data) > 0:
                print(f"      Columns: {', '.join(list(response.data[0].keys())[:10])}")
    except:
        pass

print(f"\n2. Found {len(available_tables)} tables: {', '.join(available_tables)}")

# Get sample patient
print("\n3. Fetching sample patient data...")
try:
    patients = supabase.table('patients').select('*').limit(5).execute()
    print(f"   Retrieved {len(patients.data)} patients")
    
    if patients.data:
        sample_patient = patients.data[0]
        print(f"\n   Sample patient:")
        print(f"   Subject ID: {sample_patient.get('subject_id')}")
        print(f"   Gender: {sample_patient.get('gender')}")
        print(f"   DOB: {sample_patient.get('dob')}")
        
        subject_id = sample_patient.get('subject_id')
        
        # Try to get admissions for this patient
        if 'admissions' in available_tables:
            print(f"\n4. Fetching admissions for subject {subject_id}...")
            admissions = supabase.table('admissions').select('*').eq('subject_id', subject_id).execute()
            print(f"   Found {len(admissions.data)} admissions")
            if admissions.data:
                adm = admissions.data[0]
                print(f"   Admission ID: {adm.get('hadm_id')}")
                print(f"   Admission time: {adm.get('admittime')}")
                print(f"   Diagnosis: {adm.get('diagnosis')}")
        
        # Try to get ICU stays
        if 'icustays' in available_tables:
            print(f"\n5. Fetching ICU stays for subject {subject_id}...")
            icustays = supabase.table('icustays').select('*').eq('subject_id', subject_id).execute()
            print(f"   Found {len(icustays.data)} ICU stays")
            
        # Try to get lab events
        if 'labevents' in available_tables:
            print(f"\n6. Fetching lab events for subject {subject_id}...")
            labs = supabase.table('labevents').select('*').eq('subject_id', subject_id).limit(10).execute()
            print(f"   Found {len(labs.data)} lab events (showing first 10)")

except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 80)
print("EXPLORATION COMPLETE")
print("=" * 80)
