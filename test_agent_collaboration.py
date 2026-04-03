"""
Test collaborative agents working together!
Note Parser + Lab Mapper collaboration
"""

import json
from agents.note_parser_agent import note_parser_agent
from agents.lab_mapper_agent import lab_mapper_agent
from agents.memory import AGENT_MEMORY

# Clear memory from previous tests
AGENT_MEMORY.clear_all()

# Load sample patient data
with open('data/mimic_samples/patient_001_sepsis.json', 'r') as f:
    patient = json.load(f)

# Prepare state
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
print("TESTING AGENT COLLABORATION: NOTE PARSER + LAB MAPPER")
print("=" * 80)
print(f"\nPatient: {state['patient_id']}")
print(f"Diagnosis: {state['admission_diagnosis']}")
print(f"Current time: {timeline_history[-1]['time_label']}")

print("\n" + "=" * 80)
print("STEP 1: NOTE PARSER AGENT")
print("=" * 80 + "\n")

# Run Note Parser first
state = note_parser_agent(state)

print("\n" + "=" * 80)
print("STEP 2: LAB MAPPER AGENT (Reading Note Parser's findings)")
print("=" * 80 + "\n")

# Run Lab Mapper - it will read Note Parser's findings!
state = lab_mapper_agent(state)

print("\n" + "=" * 80)
print("COLLABORATION RESULTS")
print("=" * 80)

print("\n📋 Note Parser Found:")
print(f"  • {len(state['parsed_symptoms'])} symptoms")
print(f"  • {len(state['infection_signals'])} infection signals")

print("\n📊 Lab Mapper Found:")
print(f"  • {len(state['lab_trends'])} lab trends")
for trend in state['lab_trends']:
    print(f"    - {trend['parameter']}: {trend['trend']} ({trend['change_percentage']:+.1f}%)")

print("\n💬 Agent Communication:")
messages = AGENT_MEMORY.message_bus.messages
if messages:
    for msg in messages:
        print(f"  [{msg['type']}] {msg['sender']} → {msg['recipient']}")
        print(f"    {msg['content']}")
else:
    print("  No messages exchanged (good correlation between findings)")

print("\n🧠 Shared Memory State:")
memory_summary = AGENT_MEMORY.get_memory_summary()
print(f"  • Total insights: {memory_summary['shared_context']['total_insights']}")
print(f"  • Total findings: {memory_summary['total_findings']}")
print(f"  • Agent actions: {memory_summary['conversation_history']}")

print("\n💡 Lab Mapper's Clinical Interpretation:")
lab_mapper_insights = AGENT_MEMORY.shared_context.read_insights(agent='lab_mapper')
for insight in lab_mapper_insights[:3]:  # Show top 3
    print(f"  • [{insight['category']}] {insight['insight']}")
    print(f"    Confidence: {insight['confidence']:.2f}")

print("\n🚩 Flags Raised by Both Agents:")
all_flags = AGENT_MEMORY.shared_context.read_flags()
for flag in all_flags:
    msg = str(flag['message']) if isinstance(flag['message'], dict) else flag['message']
    print(f"  [{flag['agent']}] {flag['type']}: {msg[:100]}...")

print("\n🤝 Consensus Status:")
consensus = AGENT_MEMORY.findings_registry.get_consensus()
print(f"  • Agreed findings: {len(consensus['agreed'])}")
print(f"  • Disputed findings: {len(consensus['disputed'])}")
print(f"  • Unvalidated: {len(consensus['unvalidated'])}")

print("\n" + "=" * 80)
print("COLLABORATIVE AGENT TEST COMPLETE! ✅")
print("Note Parser and Lab Mapper successfully collaborated!")
print("=" * 80)
