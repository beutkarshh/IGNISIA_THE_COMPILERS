"""
Test the enhanced MIMIC timeline builder
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mimic_adapter import convert_to_agent_format

def test_timeline_builder():
    print("=" * 60)
    print("Testing Enhanced MIMIC Timeline Builder")
    print("=" * 60)
    
    # Test with patient 10006 (SEPSIS)
    subject_id = 10006
    
    print(f"\nTesting patient {subject_id}...")
    
    data = convert_to_agent_format(subject_id)
    
    if not data:
        print("❌ Failed to convert patient data")
        return False
    
    print(f"\n📊 Results:")
    print(f"   Patient ID: {data['patient_id']}")
    print(f"   Age: {data['age']}")
    print(f"   Gender: {data['gender']}")
    print(f"   Diagnosis: {data['admission_diagnosis']}")
    print(f"   Timeline length: {len(data['timeline'])} timepoints")
    
    if data['timeline']:
        print(f"\n🔍 First timeline point:")
        first_point = data['timeline'][0]
        print(json.dumps(first_point, indent=2))
        
        print(f"\n📈 Vitals at first timepoint:")
        vitals = first_point.get('vitals', {})
        for vital, value in vitals.items():
            print(f"   {vital}: {value}")
        
        print(f"\n🧪 Labs at first timepoint:")
        labs = first_point.get('labs', {})
        for lab, value in labs.items():
            print(f"   {lab}: {value}")
    
    return True

if __name__ == "__main__":
    success = test_timeline_builder()
    sys.exit(0 if success else 1)