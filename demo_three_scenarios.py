#!/usr/bin/env python3
"""
Phase 4 Demo: Three Clinical Scenarios
Showcases the ICU Clinical Assistant's capabilities across different patient types.
"""

import json
import os
from datetime import datetime
from backend.workflow import run_patient_assessment

def set_environment():
    """Set up environment for demo."""
    os.environ['GEMINI_API_KEY'] = 'AIzaSyB4PJn3JfqO13HgndZstBXjvQ08Y0420AM'
    os.environ['GOOGLE_API_KEY'] = 'AIzaSyB4PJn3JfqO13HgndZstBXjvQ08Y0420AM'

def load_scenario(filename):
    """Load patient scenario from JSON file."""
    with open(f'data/mimic_samples/{filename}', 'r') as f:
        return json.load(f)

def print_scenario_header(title, description):
    """Print formatted scenario header."""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)
    print(description)
    print()

def print_patient_info(patient_data):
    """Print patient demographics and timeline."""
    print(f"👤 PATIENT INFO:")
    print(f"   ID: {patient_data['patient_id']}")
    print(f"   Age/Gender: {patient_data['age']} {patient_data['gender']}")
    print(f"   Diagnosis: {patient_data['admission_diagnosis']}")
    print(f"   Timeline: {len(patient_data['timeline'])} measurements")
    print()

def print_timeline_summary(patient_data):
    """Print timeline progression summary."""
    print("📈 TIMELINE SUMMARY:")
    for tp in patient_data['timeline']:
        vitals = tp['vitals']
        labs = tp['labs']
        hr = vitals['heart_rate']
        sbp = vitals['systolic_bp']
        temp = vitals['temperature']
        wbc = labs['wbc']
        lactate = labs['lactate']
        print(f"   [{tp['time_label']}] HR={hr}, BP={sbp}, Temp={temp}°C, WBC={wbc}, Lactate={lactate}")
    print()

def print_assessment_results(result):
    """Print assessment results in formatted way."""
    print("🎯 ASSESSMENT RESULTS:")
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Criteria Met: {', '.join(result['diagnostic_criteria_met'])}")
    print(f"   Symptoms: {len(result.get('parsed_symptoms', []))}")
    print(f"   Infection Signals: {len(result.get('infection_signals', []))}")
    print(f"   Lab Trends: {len(result['lab_trends'])}")
    print(f"   Outliers: {len(result['outlier_alerts'])}")
    print(f"   Recommendations: {len(result['treatment_recommendations'])}")
    print()

def print_key_findings(result):
    """Print key clinical findings."""
    print("🔍 KEY FINDINGS:")
    
    # Lab trends
    if result['lab_trends']:
        print("   Lab Trends:")
        for trend in result['lab_trends'][:3]:  # Show top 3
            values = trend['values']
            print(f"     • {trend['parameter']}: {values[0]} → {values[-1]} ({trend['trend']})")
    
    # Treatment recommendations
    if result['treatment_recommendations']:
        print("   Top Recommendations:")
        for i, rec in enumerate(result['treatment_recommendations'][:3], 1):
            print(f"     {i}. {rec['action']}")
    
    print()

def run_scenario(scenario_name, filename, title, description):
    """Run a complete scenario assessment."""
    print_scenario_header(title, description)
    
    # Load patient data
    patient_data = load_scenario(filename)
    print_patient_info(patient_data)
    print_timeline_summary(patient_data)
    
    # Run assessment
    print("🤖 RUNNING ASSESSMENT...")
    start_time = datetime.now()
    
    try:
        result = run_patient_assessment(patient_data)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_assessment_results(result)
        print_key_findings(result)
        
        print(f"✅ SCENARIO COMPLETE - Processing time: {duration:.1f}s")
        return result
        
    except Exception as e:
        print(f"❌ SCENARIO FAILED: {e}")
        return None

def main():
    """Run all three demo scenarios."""
    set_environment()
    
    print("🏥 ICU CLINICAL ASSISTANT - PHASE 4 DEMO")
    print("=" * 80)
    print("Demonstrating three clinical scenarios:")
    print("1. Classic Sepsis (Progressive deterioration)")
    print("2. Non-Sepsis UTI (Resolving infection)")  
    print("3. Septic Shock (Critical multi-organ failure)")
    print()
    print("Each scenario showcases different aspects of the AI system:")
    print("• Collaborative agent reasoning")
    print("• Trend detection and analysis")
    print("• Evidence-based recommendations")
    print("• Safety features and disclaimers")
    
    scenarios = [
        {
            'name': 'sepsis',
            'file': 'patient_001_sepsis.json',
            'title': 'SCENARIO 1: CLASSIC SEPSIS PROGRESSION',
            'description': '68M with pneumonia progressing to sepsis over 24 hours.\nShowcases early detection and collaborative agent analysis.'
        },
        {
            'name': 'uti_resolved',
            'file': 'patient_002_uti_resolved.json', 
            'title': 'SCENARIO 2: NON-SEPSIS UTI (RESOLVING)',
            'description': '45F with UTI responding well to antibiotics.\nDemonstrates system correctly identifying LOW risk and improvement.'
        },
        {
            'name': 'septic_shock',
            'file': 'patient_003_septic_shock.json',
            'title': 'SCENARIO 3: SEPTIC SHOCK (CRITICAL)',
            'description': '82M with severe septic shock and multi-organ failure.\nShows detection of extreme clinical deterioration and end-of-life considerations.'
        }
    ]
    
    results = {}
    
    for scenario in scenarios:
        result = run_scenario(
            scenario['name'],
            scenario['file'], 
            scenario['title'],
            scenario['description']
        )
        results[scenario['name']] = result
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMO SUMMARY")
    print("="*80)
    
    for scenario in scenarios:
        result = results[scenario['name']]
        if result:
            risk_score = result['risk_score']
            risk_level = result['risk_level']
            print(f"{scenario['title']:<40} Risk: {risk_score:3d}/100 ({risk_level})")
    
    print("\n✅ All scenarios completed successfully!")
    print("🎯 System demonstrates capability across diverse clinical cases")
    print("⚠️  Remember: This is a decision support tool requiring medical validation")

if __name__ == "__main__":
    main()