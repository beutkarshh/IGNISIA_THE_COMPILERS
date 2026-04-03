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
    Generate prioritized treatment recommendations.
    
    Returns:
        List of treatment recommendations
    """
    recommendations = []
    
    # Sepsis bundle if high risk
    if "qSOFA" in state.get('diagnostic_criteria_met', []) or \
       "SIRS" in state.get('diagnostic_criteria_met', []):
        recommendations.append({
            "priority": 1,
            "action": "Initiate sepsis bundle immediately (within 1 hour)",
            "rationale": "Patient meets sepsis criteria. Early intervention critical for survival.",
            "guideline_source": "[Sepsis-3 Guidelines, Surviving Sepsis Campaign]"
        })
        
        recommendations.append({
            "priority": 2,
            "action": "Draw blood cultures before antibiotics",
            "rationale": "Identify causative organism for targeted therapy.",
            "guideline_source": "[Surviving Sepsis Campaign]"
        })
        
        recommendations.append({
            "priority": 3,
            "action": "Start broad-spectrum antibiotics",
            "rationale": "Empiric coverage pending culture results.",
            "guideline_source": "[Sepsis-3 Guidelines]"
        })
    
    # Elevated lactate
    if "Elevated_Lactate" in state.get('diagnostic_criteria_met', []):
        recommendations.append({
            "priority": 2,
            "action": "IV fluid resuscitation (30 mL/kg crystalloid)",
            "rationale": "Address tissue hypoperfusion indicated by elevated lactate.",
            "guideline_source": "[Sepsis-3, Fluid Resuscitation]"
        })
    
    # Outlier redraws
    for outlier in state.get('outlier_alerts', []):
        if outlier['confidence'] > 0.7:
            recommendations.append({
                "priority": 4,
                "action": f"Redraw {outlier['parameter']} to confirm value",
                "rationale": outlier['recommendation'],
                "guideline_source": "[Clinical Lab Standards]"
            })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'])
    
    return recommendations


def generate_final_report(state: PatientState) -> str:
    """
    Generate human-readable final report using Gemini.
    
    Returns:
        Final report string
    """
    # Prepare summary
    summary = f"""
Patient ID: {state['patient_id']}
Current Time: {state['timeline_history'][-1]['time_label']}
Risk Score: {state['risk_score']}/100
Risk Level: {state['risk_level']}

Diagnostic Criteria Met: {', '.join(state['diagnostic_criteria_met']) if state['diagnostic_criteria_met'] else 'None'}

Lab Trends:
{chr(10).join([f"- {t['parameter']}: {t['trend']} ({t['values'][0]} → {t['values'][-1]})" for t in state['lab_trends']])}

Infection Signals: {', '.join(state['infection_signals']) if state['infection_signals'] else 'None'}

Outlier Alerts:
{chr(10).join([f"- {o['parameter']} = {o['value']} (confidence: {o['confidence']:.0%})" for o in state['outlier_alerts']]) if state['outlier_alerts'] else 'None'}

Treatment Recommendations:
{chr(10).join([f"{i+1}. {r['action']}" for i, r in enumerate(state['treatment_recommendations'])])}
"""

    prompt = f"""Generate a clinical report summary for an ICU patient.

{summary}

Create a brief, professional report (3-4 paragraphs) that:
1. Summarizes the patient's condition
2. Highlights critical findings
3. Explains the risk level
4. Lists key recommendations

Include this disclaimer at the top:
⚠️ DECISION-SUPPORT ONLY - NOT A CLINICAL DIAGNOSIS

Keep it concise and actionable."""

    try:
        # Gemini disabled for testing
        # response = model.generate_content(prompt)
        # report = response.text.strip()
        report = f"⚠️ DECISION-SUPPORT ONLY - NOT A CLINICAL DIAGNOSIS\n\n{summary}"
    except Exception as e:
        print(f"Report generation error: {e}")
        report = f"⚠️ DECISION-SUPPORT ONLY - NOT A CLINICAL DIAGNOSIS\n\n{summary}"
    
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
