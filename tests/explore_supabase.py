"""
Explore Supabase schema and available tables
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("=" * 80)
print("SUPABASE SCHEMA EXPLORATION")
print("=" * 80)

# Common table names to try
table_names = [
    'patients', 
    'patient', 
    'patient_data',
    'patient_timeline',
    'timeline',
    'vitals',
    'labs',
    'assessments',
    'mimic_patients',
    'icu_patients'
]

print("\nTrying to find tables...")
for table in table_names:
    try:
        response = supabase.table(table).select('*').limit(1).execute()
        if response.data is not None:
            print(f"\n✅ Found table: {table}")
            if len(response.data) > 0:
                print(f"   Columns: {list(response.data[0].keys())}")
                print(f"   Sample row count: {len(response.data)}")
            else:
                # Try to get schema by selecting with limit
                response_schema = supabase.table(table).select('*').limit(0).execute()
                print(f"   Table exists but is empty")
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' not in error_msg and '42P01' not in error_msg:
            print(f"\n⚠️ Table {table}: {error_msg[:100]}")

print("\n" + "=" * 80)
