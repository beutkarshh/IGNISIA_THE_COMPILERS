"""
Complete MIMIC Integration Test
Tests the full pipeline: timeline building + agent assessment
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mimic_adapter import convert_to_agent_format
from backend.workflow import run_patient_assessment

def test_complete_mimic_integration():
    print("=" * 80)
    print("COMPLETE MIMIC INTEGRATION TEST")
    print("=" * 80)
    
    # Test with patient 10006 (SEPSIS)
    subject_id = 10006
    
    print(f"\n[Step 1] Building timeline for patient {subject_id}...")
    
    # Convert MIMIC data to agent format
    patient_data = convert_to_agent_format(subject_id)
    
    if not patient_data:
        print("❌ Failed to convert patient data")
        return False
    
    print(f"\n✅ Timeline built successfully!")
    print(f"   Patient: {patient_data['age']}y {patient_data['gender']}")
    print(f"   Diagnosis: {patient_data['admission_diagnosis']}")
    print(f"   Timeline: {len(patient_data['timeline'])} timepoints")
    
    # Show first timeline point data
    if patient_data['timeline']:
        first_point = patient_data['timeline'][0]
        vitals = first_point['vitals']
        labs = first_point['labs']
        
        print(f"\n📊 Hour 0 Data:")
        print(f"   Heart Rate: {vitals['heart_rate']} bpm")
        print(f"   Blood Pressure: {vitals['systolic_bp']}/{vitals['diastolic_bp']} mmHg")
        print(f"   Temperature: {vitals['temperature']}°F")
        print(f"   WBC: {labs['wbc']} K/uL")
        print(f"   Lactate: {labs['lactate']} mmol/L")
        print(f"   Creatinine: {labs['creatinine']} mg/dL")
    
    print(f"\n[Step 2] Running agent assessment...")
    
    try:
        # Run assessment through agent workflow
        result = run_patient_assessment(patient_data)
        
        print(f"\n✅ Assessment completed!")
        print(f"   Risk Score: {result['risk_score']}/100")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Processing Time: {result.get('processing_time_ms', 'N/A')}ms")
        
        if result.get('diagnostic_criteria_met'):
            print(f"   Criteria Met: {', '.join(result['diagnostic_criteria_met'])}")
        else:
            print(f"   Criteria Met: None")
        
        if result.get('outlier_alerts'):
            print(f"   Outlier Alerts: {len(result['outlier_alerts'])}")
            for alert in result['outlier_alerts'][:3]:  # Show first 3
                print(f"     - {alert.get('parameter', 'Unknown')}: {alert.get('message', 'No message')}")
        
        if result.get('treatment_recommendations'):
            print(f"   Treatment Recommendations: {len(result['treatment_recommendations'])}")
            for rec in result['treatment_recommendations'][:2]:  # Show first 2
                print(f"     - {rec.get('action', 'Unknown action')}")
        
        # Detailed analysis
        print(f"\n📈 Detailed Analysis:")
        
        # Check for sepsis indicators based on our timeline data
        if patient_data['timeline']:
            vitals = patient_data['timeline'][0]['vitals']
            labs = patient_data['timeline'][0]['labs']
            
            # SIRS criteria check
            sirs_count = 0
            sirs_details = []
            
            if vitals['temperature'] > 100.4 or vitals['temperature'] < 96.8:
                sirs_count += 1
                sirs_details.append(f"Temperature: {vitals['temperature']}°F (abnormal)")
            
            if vitals['heart_rate'] > 90:
                sirs_count += 1
                sirs_details.append(f"Heart Rate: {vitals['heart_rate']} bpm (tachycardia)")
            
            if vitals['respiratory_rate'] > 20:
                sirs_count += 1
                sirs_details.append(f"Respiratory Rate: {vitals['respiratory_rate']} (tachypnea)")
            
            if labs['wbc'] > 12 or labs['wbc'] < 4:
                sirs_count += 1
                sirs_details.append(f"WBC: {labs['wbc']} K/uL (abnormal)")
            
            print(f"   SIRS Criteria: {sirs_count}/4 met")
            for detail in sirs_details:
                print(f"     ✓ {detail}")
            
            # qSOFA check
            qsofa_score = 0
            qsofa_details = []
            
            if vitals['systolic_bp'] < 100:
                qsofa_score += 1
                qsofa_details.append(f"Hypotension: SBP {vitals['systolic_bp']} mmHg")
            
            if vitals['respiratory_rate'] >= 22:
                qsofa_score += 1
                qsofa_details.append(f"Tachypnea: RR {vitals['respiratory_rate']}")
            
            print(f"   qSOFA Score: {qsofa_score}/3")
            for detail in qsofa_details:
                print(f"     ✓ {detail}")
            
            # Lactate check
            if labs['lactate'] > 2.0:
                print(f"   ⚠️ Elevated Lactate: {labs['lactate']} mmol/L (>2.0)")
            
            # Expected vs Actual
            print(f"\n💭 Clinical Expectations:")
            print(f"   Diagnosis: SEPSIS")
            print(f"   Expected Risk: MEDIUM to HIGH")
            print(f"   Expected Criteria: SIRS ≥2, possible qSOFA ≥2")
            print(f"   Expected Lactate: Elevated (>2.0)")
            
            print(f"\n📊 Actual Results:")
            print(f"   Computed Risk: {result['risk_level']} ({result['risk_score']}/100)")
            print(f"   SIRS: {sirs_count}/4 ({'✓ Met' if sirs_count >= 2 else '✗ Not Met'})")
            print(f"   qSOFA: {qsofa_score}/3 ({'✓ Met' if qsofa_score >= 2 else '✗ Not Met'})")
            print(f"   Lactate: {labs['lactate']} ({'✓ Elevated' if labs['lactate'] > 2.0 else '✗ Normal'})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_mimic_integration()
    
    print(f"\n" + "=" * 80)
    if success:
        print("✅ MIMIC INTEGRATION COMPLETE!")
        print("✅ Timeline builder working")
        print("✅ Agent assessment working")  
        print("✅ Real MIMIC data flowing to agents")
    else:
        print("❌ MIMIC INTEGRATION FAILED")
        print("❌ Issues need to be resolved")
    print("=" * 80)
    
    sys.exit(0 if success else 1)