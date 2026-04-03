"""
Supabase Client for ICU Clinical Assistant

Connects to Supabase database to fetch patient data and store assessment results.
"""

import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_patient_data(patient_id: str) -> Optional[Dict]:
    """
    Fetch patient data from Supabase.
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Patient data dict or None if not found
    """
    try:
        response = supabase.table('patients').select('*').eq('patient_id', patient_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching patient data: {e}")
        return None


def get_patient_timeline(patient_id: str) -> List[Dict]:
    """
    Fetch patient timeline data from Supabase.
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        List of timeline events
    """
    try:
        response = supabase.table('patient_timeline').select('*').eq('patient_id', patient_id).order('hours_since_admission').execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching timeline: {e}")
        return []


def list_all_patients() -> List[Dict]:
    """
    List all patients in the database.
    
    Returns:
        List of patient records
    """
    try:
        response = supabase.table('patients').select('patient_id, age, gender, admission_diagnosis').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error listing patients: {e}")
        return []


def save_assessment(assessment_data: Dict) -> Optional[str]:
    """
    Save risk assessment results to Supabase.
    
    Args:
        assessment_data: Assessment results dict
        
    Returns:
        Assessment ID or None on error
    """
    try:
        response = supabase.table('assessments').insert(assessment_data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0].get('id')
        return None
    except Exception as e:
        print(f"Error saving assessment: {e}")
        return None


def get_patient_assessments(patient_id: str) -> List[Dict]:
    """
    Retrieve all assessments for a patient.
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        List of assessment records
    """
    try:
        response = supabase.table('assessments').select('*').eq('patient_id', patient_id).order('created_at', desc=True).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching assessments: {e}")
        return []


def test_connection():
    """Test Supabase connection."""
    try:
        # Try to list patients
        patients = list_all_patients()
        print(f"✅ Supabase connection successful!")
        print(f"Found {len(patients)} patients in database")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Supabase connection...")
    test_connection()
    
    # List patients
    patients = list_all_patients()
    if patients:
        print("\nPatients in database:")
        for p in patients:
            print(f"  - {p.get('patient_id')}: {p.get('admission_diagnosis')}")
