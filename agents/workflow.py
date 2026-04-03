"""
LangGraph Workflow

Orchestrates the multi-agent pipeline for ICU patient assessment.
Agents execute sequentially, each adding to the shared PatientState.
"""

from typing import Dict
from datetime import datetime
from langgraph.graph import StateGraph, END
from agents.state import PatientState
from agents.note_parser_agent import note_parser_agent
from agents.lab_mapper_agent import lab_mapper_agent
from agents.rag_agent import rag_agent
from agents.chief_agent import chief_agent


def create_workflow():
    """
    Create and compile the LangGraph workflow.
    
    Returns:
        Compiled workflow app
    """
    # Create graph
    workflow = StateGraph(PatientState)
    
    # Add nodes (agents)
    workflow.add_node("note_parser", note_parser_agent)
    workflow.add_node("lab_mapper", lab_mapper_agent)
    workflow.add_node("rag_agent", rag_agent)
    workflow.add_node("chief_agent", chief_agent)
    
    # Define edges (sequential flow)
    workflow.add_edge("note_parser", "lab_mapper")
    workflow.add_edge("lab_mapper", "rag_agent")
    workflow.add_edge("rag_agent", "chief_agent")
    workflow.add_edge("chief_agent", END)
    
    # Set entry point
    workflow.set_entry_point("note_parser")
    
    # Compile
    app = workflow.compile()
    
    return app


def run_assessment(patient_data: Dict, current_timepoint_index: int = None) -> Dict:
    """
    Run the complete assessment pipeline on patient data.
    
    Args:
        patient_data: Patient JSON data with timeline
        current_timepoint_index: Index of current timepoint (None = use all)
        
    Returns:
        Final PatientState dict with complete assessment
    """
    # Determine timeline history
    if current_timepoint_index is None:
        timeline_history = patient_data['timeline']
    else:
        timeline_history = patient_data['timeline'][:current_timepoint_index + 1]
    
    # Initialize state
    initial_state: PatientState = {
        # Input data
        'patient_id': patient_data['patient_id'],
        'admission_id': patient_data['admission_id'],
        'age': patient_data['age'],
        'gender': patient_data['gender'],
        'admission_diagnosis': patient_data['admission_diagnosis'],
        'current_timepoint_index': current_timepoint_index or len(timeline_history) - 1,
        'timeline_history': timeline_history,
        
        # Agent outputs (initialized empty)
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
        
        # Metadata
        'generated_at': '',
        'system_version': '1.0.0',
        'processing_time_ms': None
    }
    
    # Create workflow
    app = create_workflow()
    
    # Run workflow
    start_time = datetime.now()
    final_state = app.invoke(initial_state)
    end_time = datetime.now()
    
    # Add processing time
    final_state['processing_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
    
    return final_state


# Example usage
if __name__ == "__main__":
    import json
    
    # Load sample patient
    with open('data/mimic_samples/patient_001_sepsis.json', 'r') as f:
        patient = json.load(f)
    
    # Run assessment at hour 18 (critical timepoint)
    result = run_assessment(patient, current_timepoint_index=3)
    
    print("=" * 80)
    print("ICU CLINICAL ASSISTANT - RISK ASSESSMENT")
    print("=" * 80)
    print(f"\nPatient: {result['patient_id']}")
    print(f"Time: {result['timeline_history'][-1]['time_label']}")
    print(f"\nRisk Score: {result['risk_score']}/100")
    print(f"Risk Level: {result['risk_level']}")
    print(f"\nDiagnostic Criteria Met: {', '.join(result['diagnostic_criteria_met'])}")
    print(f"\nProcessing Time: {result['processing_time_ms']}ms")
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    print(result['final_report'])
    print("\n" + "=" * 80)
    print("TREATMENT RECOMMENDATIONS")
    print("=" * 80)
    for i, rec in enumerate(result['treatment_recommendations'], 1):
        print(f"\n{i}. [{rec['guideline_source']}]")
        print(f"   {rec['action']}")
        print(f"   Rationale: {rec['rationale']}")
