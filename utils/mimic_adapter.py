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


def calculate_age(dob: str, admittime: str) -> int:
    """
    Calculate age from DOB and admission time.
    
    MIMIC-III privacy: patients >89 have DOB shifted to year 300+
    """
    try:
        from datetime import datetime
        
        dob_date = datetime.fromisoformat(dob.replace('Z', '+00:00').replace(' ', 'T'))
        admit_date = datetime.fromisoformat(admittime.replace('Z', '+00:00').replace(' ', 'T'))
        
        age = (admit_date - dob_date).days // 365
        
        # MIMIC-III privacy: ages >89 are shifted to year 300+
        if age > 200:  # Shifted age detected
            return 90  # Use 90 as representative for >89
        
        return max(18, min(age, 120))  # Reasonable bounds
    except Exception as e:
        print(f"Age calculation error: {e}")
        return 65  # Fallback


def map_itemid_to_vital(itemid: int) -> Optional[str]:
    """Map MIMIC-III chartevents itemid to vital sign name."""
    for vital, item_list in VITAL_ITEM_IDS.items():
        if itemid in item_list:
            return vital
    return None


def map_itemid_to_lab(itemid: int) -> Optional[str]:
    """Map MIMIC-III labevents itemid to lab test name."""
    for lab, item_list in LAB_ITEM_IDS.items():
        if itemid in item_list:
            return lab
    return None


def build_timeline(subject_id: int, hadm_id: int, icustay_id: int, admittime: str) -> List[Dict]:
    """
    Build timeline from MIMIC-III chartevents and labevents.
    
    Groups measurements by hour and creates timeline points.
    """
    from datetime import datetime, timedelta
    import json
    
    timeline = []
    
    try:
        # Parse admission time
        admit_dt = datetime.fromisoformat(admittime.replace('Z', '+00:00').replace(' ', 'T'))
        
        # Get vitals from chartevents (linked to icustay_id)
        vitals_response = supabase.table('chartevents').select(
            'charttime, itemid, valuenum'
        ).eq('icustay_id', icustay_id).order('charttime').limit(100).execute()
        
        # Get labs from labevents (linked to hadm_id)
        labs_response = supabase.table('labevents').select(
            'charttime, itemid, valuenum'
        ).eq('hadm_id', hadm_id).order('charttime').limit(100).execute()
        
        vitals_data = vitals_response.data if vitals_response.data else []
        labs_data = labs_response.data if labs_response.data else []
        
        print(f"   Found {len(vitals_data)} vital measurements, {len(labs_data)} lab measurements")
        
        # Group by time buckets (6-hour windows)
        time_buckets = {}
        
        # Process vitals
        for vital in vitals_data:
            if not vital.get('valuenum') or vital['valuenum'] is None:
                continue
                
            vital_name = map_itemid_to_vital(vital['itemid'])
            if not vital_name:
                continue
                
            try:
                chart_dt = datetime.fromisoformat(vital['charttime'].replace('Z', '+00:00').replace(' ', 'T'))
                hours_since_admit = int((chart_dt - admit_dt).total_seconds() / 3600)
                
                # Group into 6-hour buckets
                bucket = (hours_since_admit // 6) * 6
                bucket = max(0, bucket)  # Don't go negative
                
                if bucket not in time_buckets:
                    time_buckets[bucket] = {
                        'vitals': {},
                        'labs': {},
                        'timestamp': admit_dt + timedelta(hours=bucket),
                        'hours_since_admission': bucket
                    }
                
                time_buckets[bucket]['vitals'][vital_name] = float(vital['valuenum'])
                
            except Exception as e:
                continue
        
        # Process labs
        for lab in labs_data:
            if not lab.get('valuenum') or lab['valuenum'] is None:
                continue
                
            lab_name = map_itemid_to_lab(lab['itemid'])
            if not lab_name:
                continue
                
            try:
                chart_dt = datetime.fromisoformat(lab['charttime'].replace('Z', '+00:00').replace(' ', 'T'))
                hours_since_admit = int((chart_dt - admit_dt).total_seconds() / 3600)
                
                # Group into 6-hour buckets
                bucket = (hours_since_admit // 6) * 6
                bucket = max(0, bucket)
                
                if bucket not in time_buckets:
                    time_buckets[bucket] = {
                        'vitals': {},
                        'labs': {},
                        'timestamp': admit_dt + timedelta(hours=bucket),
                        'hours_since_admission': bucket
                    }
                
                time_buckets[bucket]['labs'][lab_name] = float(lab['valuenum'])
                
            except Exception as e:
                continue
        
        # Convert to timeline format
        for bucket in sorted(time_buckets.keys())[:6]:  # Limit to first 6 buckets (36 hours)
            bucket_data = time_buckets[bucket]
            
            # Fill in default values for missing vitals
            vitals = {
                'heart_rate': int(bucket_data['vitals'].get('heart_rate', 80)),
                'systolic_bp': int(bucket_data['vitals'].get('systolic_bp', 120)),
                'diastolic_bp': int(bucket_data['vitals'].get('diastolic_bp', 70)),
                'respiratory_rate': int(bucket_data['vitals'].get('respiratory_rate', 16)),
                'temperature': round(bucket_data['vitals'].get('temperature', 98.6), 1),
                'spo2': int(bucket_data['vitals'].get('spo2', 98))
            }
            
            # Fill in default values for missing labs
            labs = {
                'wbc': round(bucket_data['labs'].get('wbc', 7.0), 1),
                'lactate': round(bucket_data['labs'].get('lactate', 1.5), 1),
                'creatinine': round(bucket_data['labs'].get('creatinine', 1.0), 1),
                'bun': int(bucket_data['labs'].get('bun', 18)),
                'platelets': int(bucket_data['labs'].get('platelets', 220))
            }
            
            timeline_point = {
                'timestamp': bucket_data['timestamp'].isoformat(),
                'time_label': f"Hour {bucket}",
                'hours_since_admission': bucket,
                'vitals': vitals,
                'labs': labs,
                'notes': f"Patient assessment at {bucket} hours post-admission"
            }
            
            timeline.append(timeline_point)
        
        print(f"   Built timeline with {len(timeline)} timepoints")
        return timeline
        
    except Exception as e:
        print(f"Error building timeline: {e}")
        # Return minimal timeline if data fetch fails
        return [{
            'timestamp': admit_dt.isoformat(),
            'time_label': "Hour 0",
            'hours_since_admission': 0,
            'vitals': {
                'heart_rate': 80, 'systolic_bp': 120, 'diastolic_bp': 70,
                'respiratory_rate': 16, 'temperature': 98.6, 'spo2': 98
            },
            'labs': {
                'wbc': 7.0, 'lactate': 1.5, 'creatinine': 1.0, 'bun': 18, 'platelets': 220
            },
            'notes': "Default timeline point - actual measurements unavailable"
        }]


def convert_to_agent_format(subject_id: int) -> Optional[Dict]:
    """
    Convert MIMIC-III patient data to agent-compatible format.
    
    Args:
        subject_id: MIMIC-III subject ID
        
    Returns:
        Patient data dict in agent format or None
    """
    try:
        print(f"Converting patient {subject_id}...")
        
        # Get patient demographics
        patient = supabase.table('patients').select('*').eq('subject_id', subject_id).execute()
        if not patient.data:
            print(f"   ❌ Patient {subject_id} not found")
            return None
        patient_data = patient.data[0]
        
        # Get admission (most recent)
        admission = supabase.table('admissions').select('*').eq('subject_id', subject_id).order('admittime', desc=True).limit(1).execute()
        if not admission.data:
            print(f"   ❌ No admission found for patient {subject_id}")
            return None
        adm_data = admission.data[0]
        
        hadm_id = adm_data['hadm_id']
        admittime = adm_data['admittime']
        
        # Get ICU stay (if exists)
        icustay = supabase.table('icustays').select('*').eq('subject_id', subject_id).eq('hadm_id', hadm_id).limit(1).execute()
        icustay_id = None
        if icustay.data:
            icustay_id = icustay.data[0]['icustay_id']
            print(f"   ✅ ICU stay found: {icustay_id}")
        else:
            print(f"   ⚠️ No ICU stay found for admission {hadm_id}")
        
        # Calculate age
        dob = patient_data.get('dob', '')
        age = calculate_age(dob, admittime) if dob else 65
        
        print(f"   Patient: {age}y {patient_data.get('gender')} - {adm_data.get('diagnosis', 'Unknown')}")
        
        # Build timeline from MIMIC data
        timeline = []
        if icustay_id:
            timeline = build_timeline(subject_id, hadm_id, icustay_id, admittime)
        else:
            print("   ⚠️ Creating minimal timeline (no ICU stay)")
            timeline = build_timeline(subject_id, hadm_id, 0, admittime)  # Use 0 for missing icustay_id
        
        # Build patient object
        result = {
            'patient_id': str(subject_id),
            'admission_id': str(hadm_id),
            'age': age,
            'gender': patient_data.get('gender'),
            'admission_diagnosis': adm_data.get('diagnosis', 'Unknown'),
            'timeline': timeline
        }
        
        print(f"   ✅ Converted patient {subject_id} with {len(timeline)} timeline points")
        
        return result
        
    except Exception as e:
        print(f"Error converting patient data: {e}")
        import traceback
        traceback.print_exc()
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
