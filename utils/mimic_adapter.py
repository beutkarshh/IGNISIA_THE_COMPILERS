"""
MIMIC-III Data Adapter for Supabase

Converts MIMIC-III database format to our agent-compatible format.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# MIMIC-III ITEMID mappings for common lab values
LAB_ITEM_IDS = {
    'wbc': [51300, 51301],  # White blood cells
    'lactate': [50813],  # Lactate
    'creatinine': [50912],  # Creatinine
    'bun': [51006],  # Blood urea nitrogen
    'platelets': [51265],  # Platelets
}

# Chart event ITEMID mappings for vitals
VITAL_ITEM_IDS = {
    'heart_rate': [211, 220045],
    'systolic_bp': [51, 442, 455, 6701, 220179, 220050],
    'diastolic_bp': [8368, 8440, 8441, 8555, 220180, 220051],
    'respiratory_rate': [618, 615, 220210, 224690],
    'temperature': [223761, 678],
    'spo2': [646, 220277],
}


def get_patient_by_diagnosis(diagnosis_keyword: str = 'SEPSIS', limit: int = 5) -> List[Dict]:
    """
    Find patients by admission diagnosis.
    
    Args:
        diagnosis_keyword: Keyword to search in diagnosis
        limit: Maximum number of patients to return
        
    Returns:
        List of patient records with admission info
    """
    try:
        response = supabase.table('admissions').select(
            'subject_id, hadm_id, admittime, diagnosis'
        ).ilike('diagnosis', f'%{diagnosis_keyword}%').limit(limit).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error finding patients: {e}")
        return []


def get_patient_vitals(subject_id: int, hadm_id: int, icustay_id: int) -> List[Dict]:
    """
    Fetch vital signs for a patient ICU stay.
    
    Returns:
        List of vital sign measurements grouped by time
    """
    try:
        # Get all vital chart events
        all_item_ids = []
        for item_list in VITAL_ITEM_IDS.values():
            all_item_ids.extend(item_list)
        
        response = supabase.table('chartevents').select(
            'charttime, itemid, valuenum'
        ).eq('icustay_id', icustay_id).in_('itemid', all_item_ids).order('charttime').execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching vitals: {e}")
        return []


def get_patient_labs(subject_id: int, hadm_id: int) -> List[Dict]:
    """
    Fetch lab values for a patient admission.
    
    Returns:
        List of lab measurements
    """
    try:
        all_item_ids = []
        for item_list in LAB_ITEM_IDS.values():
            all_item_ids.extend(item_list)
        
        response = supabase.table('labevents').select(
            'charttime, itemid, valuenum'
        ).eq('hadm_id', hadm_id).in_('itemid', all_item_ids).order('charttime').execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching labs: {e}")
        return []


def convert_to_agent_format(subject_id: int) -> Optional[Dict]:
    """
    Convert MIMIC-III patient data to agent-compatible format.
    
    Args:
        subject_id: MIMIC-III subject ID
        
    Returns:
        Patient data dict in agent format or None
    """
    try:
        # Get patient demographics
        patient = supabase.table('patients').select('*').eq('subject_id', subject_id).execute()
        if not patient.data:
            return None
        patient_data = patient.data[0]
        
        # Get admission
        admission = supabase.table('admissions').select('*').eq('subject_id', subject_id).limit(1).execute()
        if not admission.data:
            return None
        adm_data = admission.data[0]
        
        # Get ICU stay
        icustay = supabase.table('icustays').select('*').eq('subject_id', subject_id).limit(1).execute()
        if not icustay.data:
            return None
        icu_data = icustay.data[0]
        
        # Calculate age (simplified)
        dob = patient_data.get('dob', '')
        admittime = adm_data.get('admittime', '')
        age = 65  # Default for demo
        
        # Build patient object
        result = {
            'patient_id': str(subject_id),
            'admission_id': str(adm_data.get('hadm_id')),
            'age': age,
            'gender': patient_data.get('gender'),
            'admission_diagnosis': adm_data.get('diagnosis', 'Unknown'),
            'timeline': []
        }
        
        # Note: Full timeline conversion would require grouping vitals and labs by time
        # For now, return basic structure
        print(f"✅ Converted patient {subject_id}")
        print(f"   Diagnosis: {result['admission_diagnosis']}")
        
        return result
        
    except Exception as e:
        print(f"Error converting patient data: {e}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("MIMIC-III TO AGENT FORMAT CONVERTER")
    print("=" * 80)
    
    # Find sepsis patients
    print("\n1. Finding SEPSIS patients...")
    sepsis_patients = get_patient_by_diagnosis('SEPSIS', limit=3)
    print(f"   Found {len(sepsis_patients)} sepsis patients")
    
    for p in sepsis_patients:
        print(f"\n   - Subject {p['subject_id']}: {p['diagnosis']}")
        print(f"     Admission: {p['admittime']}")
    
    if sepsis_patients:
        # Convert first patient
        test_subject_id = sepsis_patients[0]['subject_id']
        print(f"\n2. Converting patient {test_subject_id} to agent format...")
        converted = convert_to_agent_format(test_subject_id)
        
        if converted:
            print("\n   ✅ Conversion successful!")
            print(f"   Patient ID: {converted['patient_id']}")
            print(f"   Age: {converted['age']} {converted['gender']}")
            print(f"   Diagnosis: {converted['admission_diagnosis']}")
