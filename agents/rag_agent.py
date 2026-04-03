"""
Agent 3: RAG Agent

Queries medical knowledge base (ChromaDB) for relevant clinical guidelines.
Applies diagnostic criteria (SIRS, qSOFA, Sepsis-3).
"""

from typing import Dict, List
from agents.state import PatientState, GuidelineMatch, SIRS_CRITERIA, QSOFA_CRITERIA


def build_query(state: PatientState) -> str:
    """
    Build a query string from current patient state.
    
    Args:
        state: Current patient state
        
    Returns:
        Query string for RAG retrieval
    """
    query_parts = []
    
    # Add symptoms
    if state.get('infection_signals'):
        query_parts.append(' '.join(state['infection_signals']))
    
    # Add concerning lab trends
    for trend in state.get('lab_trends', []):
        if trend['trend'] in ['rising_sharply', 'rising', 'falling_sharply']:
            query_parts.append(f"{trend['parameter']} {trend['trend']}")
    
    # Add vital trends
    for param, trend in state.get('vital_trends', {}).items():
        if trend in ['rising_sharply', 'rising', 'falling_sharply']:
            query_parts.append(f"{param} {trend}")
    
    return ' '.join(query_parts) if query_parts else "patient assessment"


def check_sirs_criteria(state: PatientState) -> bool:
    """
    Check if patient meets SIRS criteria (≥2 of 4).
    
    Returns:
        True if SIRS criteria met
    """
    if not state['timeline_history']:
        return False
    
    current = state['timeline_history'][-1]
    vitals = current['vitals']
    labs = current['labs']
    
    criteria_met = 0
    
    # Temperature
    if vitals['temperature'] > SIRS_CRITERIA['temperature_high'] or \
       vitals['temperature'] < SIRS_CRITERIA['temperature_low']:
        criteria_met += 1
    
    # Heart rate
    if vitals['heart_rate'] > SIRS_CRITERIA['heart_rate']:
        criteria_met += 1
    
    # Respiratory rate
    if vitals['respiratory_rate'] > SIRS_CRITERIA['respiratory_rate']:
        criteria_met += 1
    
    # WBC
    if labs['wbc'] > SIRS_CRITERIA['wbc_high'] or labs['wbc'] < SIRS_CRITERIA['wbc_low']:
        criteria_met += 1
    
    return criteria_met >= 2


def check_qsofa_score(state: PatientState) -> int:
    """
    Calculate qSOFA score (0-3).
    
    Returns:
        qSOFA score
    """
    if not state['timeline_history']:
        return 0
    
    current = state['timeline_history'][-1]
    vitals = current['vitals']
    notes = current['notes'].lower()
    
    score = 0
    
    # Altered mentation
    if 'confusion' in notes or 'altered' in notes or 'mentation' in notes:
        score += 1
    
    # Systolic BP < 100
    if vitals['systolic_bp'] < QSOFA_CRITERIA['systolic_bp']:
        score += 1
    
    # Respiratory rate ≥ 22
    if vitals['respiratory_rate'] >= QSOFA_CRITERIA['respiratory_rate']:
        score += 1
    
    return score


def rag_agent(state: PatientState) -> PatientState:
    """
    Query medical knowledge base and apply diagnostic criteria.
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with retrieved_guidelines and diagnostic_criteria_met
    """
    # Build query
    query = build_query(state)
    
    # TODO: Implement ChromaDB retrieval
    # For now, use rule-based matching
    retrieved_guidelines = []
    diagnostic_criteria_met = []
    
    # Check SIRS
    if check_sirs_criteria(state):
        diagnostic_criteria_met.append("SIRS")
        retrieved_guidelines.append({
            "guideline_name": "SIRS Criteria",
            "section": "Diagnostic",
            "content": "Systemic Inflammatory Response Syndrome: ≥2 of (Temp >38°C or <36°C, HR >90, RR >20, WBC >12K or <4K)",
            "relevance_score": 0.95,
            "citation": "[SIRS Criteria]"
        })
    
    # Check qSOFA
    qsofa_score = check_qsofa_score(state)
    if qsofa_score >= 2:
        diagnostic_criteria_met.append("qSOFA")
        retrieved_guidelines.append({
            "guideline_name": "qSOFA",
            "section": "Sepsis-3",
            "content": f"Quick SOFA score = {qsofa_score}. Score ≥2 indicates high risk of poor outcome with suspected infection.",
            "relevance_score": 0.92,
            "citation": "[Sepsis-3, qSOFA]"
        })
    
    # Check elevated lactate
    if state['timeline_history']:
        current_lactate = state['timeline_history'][-1]['labs']['lactate']
        if current_lactate > 2.0:
            diagnostic_criteria_met.append("Elevated_Lactate")
            retrieved_guidelines.append({
                "guideline_name": "Sepsis-3",
                "section": "Lactate",
                "content": f"Lactate {current_lactate} mmol/L. Lactate >2.0 mmol/L suggests tissue hypoperfusion and septic shock risk.",
                "relevance_score": 0.90,
                "citation": "[Sepsis-3, Lactate Criteria]"
            })
    
    state['retrieved_guidelines'] = retrieved_guidelines
    state['diagnostic_criteria_met'] = diagnostic_criteria_met
    
    return state
