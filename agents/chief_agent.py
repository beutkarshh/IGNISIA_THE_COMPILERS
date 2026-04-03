"""
Agent 4: Chief Synthesis Agent

Integrates all agent outputs, performs outlier detection, calculates risk score,
generates treatment recommendations, and creates final report.
"""

import os
from typing import Dict, List
from datetime import datetime
# Gemini imports commented for testing
# import google.generativeai as genai
from agents.state import PatientState, OutlierAlert, RiskFlag, TreatmentRecommendation
from utils.outlier_detector import analyze_all_labs


# Initialize Gemini (commented for testing)
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel('gemini-1.5-flash')


# Safety disclaimer for all assessments
SAFETY_DISCLAIMER = """
⚠️ CLINICAL DECISION SUPPORT TOOL - NOT A DIAGNOSTIC DEVICE

This system is designed to assist healthcare professionals in clinical 
decision-making and is NOT intended to replace clinical judgment. All 
recommendations must be validated by qualified medical personnel.

IMPORTANT LIMITATIONS:
• This tool has not been FDA-approved for diagnostic use
• Results are based on AI analysis and may contain errors
• Clinical decisions should be made by qualified healthcare providers
• Always verify critical findings with additional testing
• Not suitable as the sole basis for patient care decisions

Use of this system constitutes acceptance of these limitations.
"""


def calculate_risk_score(state: PatientState) -> int:
    """
    Calculate risk score (0-100) based on all findings.
    
    Returns:
        Risk score
    """
    score = 0
    
    # Diagnostic criteria
    if "qSOFA" in state.get('diagnostic_criteria_met', []):
        score += 40
    if "SIRS" in state.get('diagnostic_criteria_met', []):
        score += 20
    if "Elevated_Lactate" in state.get('diagnostic_criteria_met', []):
        score += 20
    
    # Trends
    for trend in state.get('lab_trends', []):
        if trend['parameter'] == 'lactate' and trend['trend'] == 'rising_sharply':
            score += 15
        elif trend['parameter'] == 'wbc' and trend['trend'] in ['rising_sharply', 'rising']:
            score += 10
    
    # Infection signals
    infection_count = len(state.get('infection_signals', []))
    score += min(infection_count * 5, 15)
    
    return min(score, 100)


def generate_risk_level(score: int) -> str:
    """Map risk score to level."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


def generate_treatment_recommendations(state: PatientState) -> List[TreatmentRecommendation]:
    """
    Generate prioritized treatment recommendations with full citations.
    
    Returns:
        List of treatment recommendations with enhanced metadata
    """
    recommendations = []
    
    # Sepsis bundle if high risk
    if "qSOFA" in state.get('diagnostic_criteria_met', []) or \
       "SIRS" in state.get('diagnostic_criteria_met', []):
        recommendations.append({
            "priority": 1,
            "action": "Initiate sepsis bundle immediately (within 1 hour)",
            "rationale": "Patient meets sepsis criteria. Early intervention critical for survival.",
            "guideline_source": "Surviving Sepsis Campaign 2021 (Evans L, et al. Crit Care Med. 2021;49(11):e1063-e1143)"
        })
        
        recommendations.append({
            "priority": 2,
            "action": "Draw blood cultures before antibiotics",
            "rationale": "Identify causative organism for targeted therapy.",
            "guideline_source": "Surviving Sepsis Campaign 2021 - Blood Culture Recommendation (PMID: 34605781)"
        })
        
        recommendations.append({
            "priority": 3,
            "action": "Start broad-spectrum antibiotics",
            "rationale": "Empiric coverage pending culture results.",
            "guideline_source": "Sepsis-3 Guidelines (Singer M, et al. JAMA. 2016;315(8):801-810)"
        })
    
    # Elevated lactate
    if "Elevated_Lactate" in state.get('diagnostic_criteria_met', []):
        recommendations.append({
            "priority": 2,
            "action": "IV fluid resuscitation (30 mL/kg crystalloid)",
            "rationale": "Address tissue hypoperfusion indicated by elevated lactate.",
            "guideline_source": "Surviving Sepsis Campaign 2021 - Initial Resuscitation (DOI: 10.1097/CCM.0000000000005337)"
        })
    
    # Outlier redraws
    for outlier in state.get('outlier_alerts', []):
        if outlier['confidence'] > 0.7:
            recommendations.append({
                "priority": 4,
                "action": f"Redraw {outlier['parameter']} to confirm value",
                "rationale": outlier['recommendation'],
                "guideline_source": "Clinical Laboratory Standards Institute (CLSI) - Quality Control Guidelines"
            })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'])
    
    return recommendations


def generate_final_report(state: PatientState) -> str:
    """
    Generate human-readable final report with safety disclaimer.
    
    Returns:
        Final report string with disclaimer
    """
    # Format report sections
    criteria_text = ', '.join(state['diagnostic_criteria_met']) if state['diagnostic_criteria_met'] else 'None'
    
    lab_trends_text = '\n'.join([
        f"  • {t['parameter'].upper()}: {t['trend']} ({t['values'][0]} → {t['values'][-1]}, {t['change_percentage']:+.1f}%)"
        for t in state['lab_trends']
    ]) if state['lab_trends'] else '  None'
    
    infection_text = ', '.join(state['infection_signals']) if state['infection_signals'] else 'None'
    
    outlier_text = '\n'.join([
        f"  • {o['parameter']} = {o['value']} (Confidence: {o['confidence']:.0%})"
        for o in state['outlier_alerts']
    ]) if state['outlier_alerts'] else '  None'
    
    treatment_text = '\n'.join([
        f"  {i+1}. [Priority {r['priority']}] {r['action']}\n     Rationale: {r['rationale']}\n     Source: {r['guideline_source']}"
        for i, r in enumerate(state['treatment_recommendations'])
    ]) if state['treatment_recommendations'] else '  None'
    
    # Build complete report with disclaimer
    report = f"""{SAFETY_DISCLAIMER}

{'='*80}
SEPSIS RISK ASSESSMENT REPORT
{'='*80}

Patient ID: {state['patient_id']}
Admission ID: {state['admission_id']}
Assessment Time: {state['generated_at']}
Current Timepoint: {state['timeline_history'][-1]['time_label'] if state['timeline_history'] else 'N/A'}

{'='*80}
RISK ASSESSMENT
{'='*80}

Risk Score: {state['risk_score']}/100
Risk Level: {state['risk_level']}

{'='*80}
DIAGNOSTIC CRITERIA MET
{'='*80}

{criteria_text}

{'='*80}
LABORATORY TRENDS
{'='*80}

{lab_trends_text}

{'='*80}
INFECTION SIGNALS
{'='*80}

{infection_text}

{'='*80}
OUTLIER ALERTS
{'='*80}

{outlier_text}

{'='*80}
TREATMENT RECOMMENDATIONS
{'='*80}

{treatment_text}

{'='*80}
END OF REPORT
{'='*80}

Generated by ICU Clinical Assistant v{state.get('system_version', '1.0.0')}
Report ID: {state.get('patient_id', 'N/A')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}
"""
    
    return report


def chief_agent(state: PatientState) -> PatientState:
    """
    Chief synthesis agent: integrates all outputs and generates final assessment.
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with complete assessment
    """
    # 1. Outlier detection
    if state['timeline_history']:
        current_tp = state['timeline_history'][-1]
        history = state['timeline_history'][:-1]
        
        outliers = analyze_all_labs(
            current_labs=current_tp['labs'],
            timeline_history=history,
            current_timestamp=current_tp['timestamp']
        )
        state['outlier_alerts'] = outliers
    else:
        state['outlier_alerts'] = []
    
    # 2. Calculate risk score
    state['risk_score'] = calculate_risk_score(state)
    state['risk_level'] = generate_risk_level(state['risk_score'])
    
    # 3. Generate risk flags
    risk_flags = []
    for criteria in state.get('diagnostic_criteria_met', []):
        risk_flags.append({
            "flag_type": criteria,
            "severity": state['risk_level'],
            "description": f"{criteria} criteria met",
            "evidence": [g['citation'] for g in state.get('retrieved_guidelines', [])],
            "timestamp": datetime.utcnow().isoformat()
        })
    state['risk_flags'] = risk_flags
    
    # 4. Generate treatment recommendations
    state['treatment_recommendations'] = generate_treatment_recommendations(state)
    
    # 5. Generate final report
    state['final_report'] = generate_final_report(state)
    
    # 6. Add metadata
    state['generated_at'] = datetime.utcnow().isoformat()
    state['system_version'] = "1.0.0"
    
    return state
