#!/usr/bin/env python3
"""Detailed test showing full system outputs."""

import json
import os
from backend.workflow import run_patient_assessment

def test_detailed_outputs():
    # Set API key
    os.environ['GEMINI_API_KEY'] = 'AIzaSyB4PJn3JfqO13HgndZstBXjvQ08Y0420AM'
    os.environ['GOOGLE_API_KEY'] = 'AIzaSyB4PJn3JfqO13HgndZstBXjvQ08Y0420AM'

    # Load patient data
    with open('data/mimic_samples/patient_001_sepsis.json', 'r') as f:
        patient_data = json.load(f)

    print('🏥 PATIENT DATA INPUT:')
    print('=' * 50)
    print(f'Patient ID: {patient_data["patient_id"]}')
    print(f'Age/Gender: {patient_data["age"]} {patient_data["gender"]}') 
    print(f'Diagnosis: {patient_data["admission_diagnosis"]}')
    print(f'Timeline Points: {len(patient_data["timeline"])}')
    print()

    # Show timeline progression
    print('📈 TIMELINE PROGRESSION:')
    print('=' * 50)
    for i, tp in enumerate(patient_data['timeline']):
        vitals = tp['vitals']
        labs = tp['labs']
        print(f'[{tp["time_label"]}] HR={vitals["heart_rate"]}, BP={vitals["systolic_bp"]}/{vitals["diastolic_bp"]}, WBC={labs["wbc"]}, Lactate={labs["lactate"]}')

    print()
    print('🤖 RUNNING ASSESSMENT...')
    print('=' * 50)

    # Run assessment
    result = run_patient_assessment(patient_data)

    print()
    print('📊 ASSESSMENT RESULTS:')
    print('=' * 50)
    print(f'Risk Score: {result["risk_score"]}/100')
    print(f'Risk Level: {result["risk_level"]}')
    print(f'Criteria Met: {result["diagnostic_criteria_met"]}')
    print(f'Symptoms Found: {len(result.get("parsed_symptoms", []))}')
    print(f'Infection Signals: {len(result.get("infection_signals", []))}')
    print(f'Lab Trends: {len(result["lab_trends"])}')
    print(f'Outlier Alerts: {len(result["outlier_alerts"])}')
    print(f'Treatment Recommendations: {len(result["treatment_recommendations"])}')
    print()

    print('💊 TREATMENT RECOMMENDATIONS:')
    print('=' * 50)
    for i, rec in enumerate(result['treatment_recommendations'][:5], 1):
        print(f'{i}. {rec["action"]}')
        print(f'   Priority: {rec["priority"]}')
        print(f'   Rationale: {rec["rationale"][:60]}...')
        print()

    print('🧬 LAB TRENDS DETECTED:')
    print('=' * 50)
    for trend in result['lab_trends']:
        print(f'{trend["parameter"]}: {trend["trend"]} ({trend["values"][0]} → {trend["values"][-1]})')

    print()
    print('⚠️ OUTLIER ALERTS:')
    print('=' * 50)
    for alert in result['outlier_alerts']:
        print(f'{alert["parameter"]} = {alert["value"]} (confidence: {alert["confidence"]:.0%})')

    print()
    print('🔍 DETAILED SYMPTOM EXTRACTION:')
    print('=' * 50)
    for symptom in result.get("parsed_symptoms", [])[:5]:
        print(f'• {symptom["symptom"]} (severity: {symptom["severity"]}, confidence: {symptom["confidence"]:.0%})')

    print()
    print('🦠 INFECTION SIGNALS:')
    print('=' * 50)
    for signal in result.get("infection_signals", [])[:5]:
        print(f'• {signal}')

    print()
    print('📄 FINAL REPORT (First 500 chars):')
    print('=' * 50)
    report = result.get('final_report', '')
    print(report[:500] + '...' if len(report) > 500 else report)

    print()
    print('✅ DETAILED TEST COMPLETE!')

if __name__ == "__main__":
    test_detailed_outputs()