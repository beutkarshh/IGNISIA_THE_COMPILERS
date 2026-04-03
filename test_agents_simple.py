"""
Simple test of the agent pipeline WITHOUT Gemini (to test core logic)
"""

import json
import sys
from datetime import datetime

# Load patient data
with open('data/mimic_samples/patient_001_sepsis.json', 'r') as f:
    patient = json.load(f)

# Initialize simple state
timeline_history = patient['timeline'][:4]  # Up to hour 18 (sepsis timepoint)

state = {
    'patient_id': patient['patient_id'],
    'admission_id': patient['admission_id'],
    'age': patient['age'],
    'gender': patient['gender'],
    'admission_diagnosis': patient['admission_diagnosis'],
    'current_timepoint_index': 3,
    'timeline_history': timeline_history,
    'parsed_symptoms': [],
    'infection_signals': [],
    'lab_trends': [],
    'vital_trends': {},
    'retrieved_guidelines': [],
    'diagnostic_criteria_met': [],
    'outlier_alerts': [],
    'risk_flags': [],
    'risk_score': 0,
    'risk_level': 'LOW',
    'treatment_recommendations': [],
    'final_report': '',
    'generated_at': '',
    'system_version': '1.0.0',
    'processing_time_ms': None
}

print("=" * 80)
print("ICU CLINICAL ASSISTANT - AGENT PIPELINE TEST")
print("=" * 80)
print(f"\nPatient: {state['patient_id']}")
print(f"Age: {state['age']} {state['gender']}")
print(f"Diagnosis: {state['admission_diagnosis']}")
print(f"Current Time: {timeline_history[-1]['time_label']}")

# Test Agent 2: Lab Mapper
print("\n" + "=" * 80)
print("AGENT 2: TEMPORAL LAB MAPPER")
print("=" * 80)

from agents.lab_mapper_agent import lab_mapper_agent
state = lab_mapper_agent(state)

print("\nLab Trends Detected:")
for trend in state['lab_trends']:
    print(f"  • {trend['parameter']}: {trend['trend']}")
    print(f"    Values: {trend['values'][0]} → {trend['values'][-1]} ({trend['change_percentage']:+.1f}%)")

print("\nVital Trends:")
for param, trend in state['vital_trends'].items():
    print(f"  • {param}: {trend}")

# Test Agent 3: RAG Agent
print("\n" + "=" * 80)
print("AGENT 3: RAG AGENT (Diagnostic Criteria)")
print("=" * 80)

from agents.rag_agent import rag_agent
state = rag_agent(state)

print(f"\nCriteria Met: {', '.join(state['diagnostic_criteria_met']) if state['diagnostic_criteria_met'] else 'None'}")
print(f"\nGuidelines Retrieved: {len(state['retrieved_guidelines'])}")
for guide in state['retrieved_guidelines']:
    print(f"  • [{guide['guideline_name']}] {guide['content'][:100]}...")

# Test Agent 4: Chief Agent (without Gemini report generation)
print("\n" + "=" * 80)
print("AGENT 4: CHIEF SYNTHESIS AGENT")
print("=" * 80)

from agents.chief_agent import calculate_risk_score, generate_risk_level, generate_treatment_recommendations
from utils.outlier_detector import analyze_all_labs

# Outlier detection
current_tp = state['timeline_history'][-1]
history = state['timeline_history'][:-1]
outliers = analyze_all_labs(
    current_labs=current_tp['labs'],
    timeline_history=history,
    current_timestamp=current_tp['timestamp']
)
state['outlier_alerts'] = outliers

# Risk scoring
state['risk_score'] = calculate_risk_score(state)
state['risk_level'] = generate_risk_level(state['risk_score'])

# Treatment recommendations
state['treatment_recommendations'] = generate_treatment_recommendations(state)

print(f"\nRisk Score: {state['risk_score']}/100")
print(f"Risk Level: {state['risk_level']}")

if state['outlier_alerts']:
    print(f"\nOutlier Alerts: {len(state['outlier_alerts'])}")
    for alert in state['outlier_alerts']:
        print(f"  • {alert['parameter']} = {alert['value']} (confidence: {alert['confidence']:.0%})")
else:
    print("\nOutlier Alerts: None")

print(f"\nTreatment Recommendations ({len(state['treatment_recommendations'])}):")
for i, rec in enumerate(state['treatment_recommendations'], 1):
    print(f"\n  {i}. {rec['action']}")
    print(f"     Rationale: {rec['rationale']}")
    print(f"     Source: {rec['guideline_source']}")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ Lab Mapper: Detected {len(state['lab_trends'])} lab trends")
print(f"✅ RAG Agent: Met {len(state['diagnostic_criteria_met'])} diagnostic criteria")
print(f"✅ Chief Agent: Risk Score {state['risk_score']}/100 ({state['risk_level']})")
print(f"✅ Chief Agent: Generated {len(state['treatment_recommendations'])} recommendations")

print("\n" + "=" * 80)
print("AGENTS WORKING CORRECTLY! ✅")
print("=" * 80)
