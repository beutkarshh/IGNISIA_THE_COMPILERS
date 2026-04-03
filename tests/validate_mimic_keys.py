"""
MIMIC-III Data Validation Script

This script validates that:
1. Patient data is correctly fetched from Supabase using subject_id
2. All foreign key relationships are maintained
3. Data is properly converted to agent format
4. patient_id = str(subject_id) consistently
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mimic_adapter import (
    get_patient_by_diagnosis,
    convert_to_agent_format,
    supabase
)

load_dotenv()


def validate_mimic_keys():
    """Validate MIMIC-III key relationships."""
    
    print("=" * 80)
    print("MIMIC-III DATA VALIDATION")
    print("=" * 80)
    
    # 1. Find a sepsis patient
    print("\n[Step 1] Searching for SEPSIS patient...")
    patients = get_patient_by_diagnosis('SEPSIS', limit=1)
    
    if not patients:
        print("❌ No patients found with SEPSIS diagnosis")
        return False
    
    test_patient = patients[0]
    subject_id = test_patient['subject_id']
    hadm_id = test_patient['hadm_id']
    
    print(f"✅ Found patient:")
    print(f"   subject_id: {subject_id} (PRIMARY KEY)")
    print(f"   hadm_id: {hadm_id} (admission FK)")
    print(f"   diagnosis: {test_patient['diagnosis']}")
    
    # 2. Verify patient exists in patients table
    print(f"\n[Step 2] Verifying subject_id={subject_id} in patients table...")
    patient_check = supabase.table('patients').select('*').eq('subject_id', subject_id).execute()
    
    if not patient_check.data:
        print(f"❌ subject_id {subject_id} not found in patients table!")
        return False
    
    print(f"✅ Patient found in patients table")
    print(f"   Gender: {patient_check.data[0]['gender']}")
    
    # 3. Verify admission exists
    print(f"\n[Step 3] Verifying hadm_id={hadm_id} in admissions table...")
    admission_check = supabase.table('admissions').select('*').eq('hadm_id', hadm_id).execute()
    
    if not admission_check.data:
        print(f"❌ hadm_id {hadm_id} not found in admissions table!")
        return False
    
    admission = admission_check.data[0]
    print(f"✅ Admission found")
    print(f"   Linked to subject_id: {admission['subject_id']}")
    print(f"   Admit time: {admission['admittime']}")
    
    # 4. Verify FK relationship
    if admission['subject_id'] != subject_id:
        print(f"❌ FK VIOLATION: admission.subject_id ({admission['subject_id']}) != patient.subject_id ({subject_id})")
        return False
    
    print(f"✅ Foreign key relationship valid")
    
    # 5. Check for ICU stay
    print(f"\n[Step 4] Checking for ICU stay...")
    icustay_check = supabase.table('icustays').select('*').eq('subject_id', subject_id).eq('hadm_id', hadm_id).execute()
    
    if icustay_check.data:
        icustay = icustay_check.data[0]
        icustay_id = icustay['icustay_id']
        print(f"✅ ICU stay found: icustay_id={icustay_id}")
        print(f"   subject_id: {icustay['subject_id']} (matches: {icustay['subject_id'] == subject_id})")
        print(f"   hadm_id: {icustay['hadm_id']} (matches: {icustay['hadm_id'] == hadm_id})")
        
        # 6. Check chartevents (vitals) linked to ICU stay
        print(f"\n[Step 5] Checking chartevents...")
        vitals_check = supabase.table('chartevents').select('charttime, itemid, valuenum').eq('icustay_id', icustay_id).limit(5).execute()
        
        if vitals_check.data:
            print(f"✅ Found {len(vitals_check.data)} vital measurements")
            print(f"   Sample: {vitals_check.data[0]}")
        else:
            print("⚠️  No chartevents found for this ICU stay")
    else:
        print("⚠️  No ICU stay found (patient may not have been in ICU)")
    
    # 7. Check labevents linked to admission
    print(f"\n[Step 6] Checking labevents...")
    labs_check = supabase.table('labevents').select('charttime, itemid, valuenum').eq('hadm_id', hadm_id).limit(5).execute()
    
    if labs_check.data:
        print(f"✅ Found {len(labs_check.data)} lab measurements")
        print(f"   Sample: {labs_check.data[0]}")
    else:
        print("⚠️  No labevents found for this admission")
    
    # 8. Test conversion to agent format
    print(f"\n[Step 7] Converting to agent format...")
    agent_data = convert_to_agent_format(subject_id)
    
    if not agent_data:
        print("❌ Conversion failed!")
        return False
    
    print(f"✅ Conversion successful!")
    print(f"\n📋 Agent Format:")
    print(f"   patient_id: {agent_data['patient_id']} (= str({subject_id}))")
    print(f"   admission_id: {agent_data['admission_id']} (= str({hadm_id}))")
    print(f"   age: {agent_data['age']}")
    print(f"   gender: {agent_data['gender']}")
    print(f"   diagnosis: {agent_data['admission_diagnosis']}")
    print(f"   timeline: {len(agent_data['timeline'])} timepoints")
    
    # 9. Validate patient_id mapping
    print(f"\n[Step 8] Validating patient_id mapping...")
    if agent_data['patient_id'] == str(subject_id):
        print(f"✅ patient_id correctly mapped: patient_id = str(subject_id)")
    else:
        print(f"❌ patient_id mismatch: {agent_data['patient_id']} != {str(subject_id)}")
        return False
    
    if agent_data['admission_id'] == str(hadm_id):
        print(f"✅ admission_id correctly mapped: admission_id = str(hadm_id)")
    else:
        print(f"❌ admission_id mismatch: {agent_data['admission_id']} != {str(hadm_id)}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL VALIDATIONS PASSED!")
    print("=" * 80)
    print("\n📊 Summary:")
    print(f"   • subject_id (MIMIC) → patient_id (Agent): {subject_id} → {agent_data['patient_id']}")
    print(f"   • hadm_id (MIMIC) → admission_id (Agent): {hadm_id} → {agent_data['admission_id']}")
    print(f"   • All foreign keys validated")
    print(f"   • Data correctly converted to agent format")
    
    return True


if __name__ == "__main__":
    try:
        success = validate_mimic_keys()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
