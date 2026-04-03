"""
Test the upgraded collaborative Note Parser agent
"""

import json
from agents.note_parser_agent import note_parser_agent
from agents.memory import AGENT_MEMORY

# Load sample patient data
with open('data/mimic_samples/patient_001_sepsis.json', 'r') as f:
    patient = json.load(f)

# Prepare state with timeline up to hour 18
timeline_history = patient['timeline'][:4]

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
    'system_version': '2.0.0',
    'processing_time_ms': None
}

print("=" * 80)
print("TESTING COLLABORATIVE NOTE PARSER AGENT")
print("=" * 80)
print(f"\nPatient: {state['patient_id']}")
print(f"Timeline points: {len(timeline_history)}")
print(f"Current time: {timeline_history[-1]['time_label']}")

print("\n" + "=" * 80)
print("RUNNING NOTE PARSER WITH FULL COLLABORATION...")
print("=" * 80 + "\n")

# Run the upgraded agent
state = note_parser_agent(state)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

print(f"\nSymptoms found: {len(state['parsed_symptoms'])}")
for symptom in state['parsed_symptoms']:
    print(f"  • {symptom.get('symptom', 'unknown')}: {symptom.get('severity', 'unknown')} "
          f"(confidence: {symptom.get('confidence', 0.8):.2f})")

print(f"\nInfection signals: {len(state['infection_signals'])}")
for signal in state['infection_signals']:
    print(f"  • {signal}")

print("\n" + "=" * 80)
print("SHARED MEMORY STATE")
print("=" * 80)

# Check what was written to memory
memory_summary = AGENT_MEMORY.get_memory_summary()
print(f"\nMemory Summary:")
print(json.dumps(memory_summary, indent=2))

print("\nInsights written:")
insights = AGENT_MEMORY.shared_context.read_insights()
for insight in insights:
    print(f"  [{insight['category']}] {insight['insight']} (confidence: {insight['confidence']:.2f})")

print("\nFlags raised:")
flags = AGENT_MEMORY.shared_context.read_flags()
for flag in flags:
    print(f"  [{flag['severity']}] {flag['message']}")

print("\nFindings registered:")
findings = AGENT_MEMORY.findings_registry.get_findings_by_agent('note_parser')
for finding in findings:
    print(f"  {finding['type']}: {finding['id']} (confidence: {finding['confidence']:.2f})")

print("\n" + "=" * 80)
print("COLLABORATIVE AGENT TEST COMPLETE! ✅")
print("=" * 80)
