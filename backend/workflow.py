"""Backend orchestration layer for calling the existing agent workflow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from agents.chief_agent import chief_agent
from agents.lab_mapper_agent import lab_mapper_agent
from agents.note_parser_agent import note_parser_agent
from agents.rag_agent import rag_agent
from utils.timeline_generator import generate_patient_timeline, resolve_current_timepoint_index


def _recompute_risk_level(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def enhance_treatment_recommendations(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    recommendations = [deepcopy(item) for item in result.get("treatment_recommendations", [])]
    existing_actions = {item.get("action") for item in recommendations}

    current_timepoint = (result.get("timeline_history") or [{}])[-1]
    vitals = current_timepoint.get("vitals", {})
    labs = current_timepoint.get("labs", {})

    enhancements = []
    if vitals.get("systolic_bp", 999) < 100:
        enhancements.append(
            {
                "priority": 2,
                "action": "Escalate hemodynamic monitoring and prepare vasopressor support",
                "rationale": "Systolic blood pressure is below the sepsis shock threshold.",
                "guideline_source": "[Sepsis-3 Hemodynamic Support]",
            }
        )
    if labs.get("creatinine", 0) > 1.3:
        enhancements.append(
            {
                "priority": 3,
                "action": "Trend renal function and evaluate for acute kidney injury",
                "rationale": "Creatinine is elevated and may reflect evolving organ dysfunction.",
                "guideline_source": "[KDIGO AKI Guidance]",
            }
        )
    if vitals.get("spo2", 100) < 94 or vitals.get("respiratory_rate", 0) >= 24:
        enhancements.append(
            {
                "priority": 3,
                "action": "Provide supplemental oxygen and reassess respiratory status",
                "rationale": "Oxygenation or work of breathing is worsening.",
                "guideline_source": "[Critical Care Stabilization]",
            }
        )

    for item in enhancements:
        if item["action"] not in existing_actions:
            recommendations.append(item)
            existing_actions.add(item["action"])

    recommendations.sort(key=lambda item: item.get("priority", 99))
    return recommendations


def normalize_assessment(result: Dict[str, Any]) -> Dict[str, Any]:
    normalized = deepcopy(result)
    raw_score = int(normalized.get("risk_score", 0))
    normalized["raw_risk_score"] = raw_score
    normalized["risk_score"] = min(raw_score, 90)
    normalized["risk_level"] = _recompute_risk_level(normalized["risk_score"])
    normalized["treatment_recommendations"] = enhance_treatment_recommendations(normalized)
    return normalized


def run_patient_assessment(patient_data: Dict[str, Any], current_timepoint_index: Optional[int] = None) -> Dict[str, Any]:
    prepared_patient = generate_patient_timeline(patient_data, current_timepoint_index)
    index = resolve_current_timepoint_index(prepared_patient, prepared_patient.get("current_timepoint_index"))
    timeline_history = prepared_patient.get("timeline", [])[: index + 1]

    state: Dict[str, Any] = {
        "patient_id": prepared_patient["patient_id"],
        "admission_id": prepared_patient["admission_id"],
        "age": prepared_patient["age"],
        "gender": prepared_patient["gender"],
        "admission_diagnosis": prepared_patient["admission_diagnosis"],
        "current_timepoint_index": index,
        "timeline_history": timeline_history,
        "parsed_symptoms": [],
        "infection_signals": [],
        "lab_trends": [],
        "vital_trends": {},
        "retrieved_guidelines": [],
        "diagnostic_criteria_met": [],
        "outlier_alerts": [],
        "risk_flags": [],
        "risk_score": 0,
        "risk_level": "LOW",
        "treatment_recommendations": [],
        "final_report": "",
        "generated_at": "",
        "system_version": "1.0.0",
        "processing_time_ms": None,
    }

    state = note_parser_agent(state)
    state = lab_mapper_agent(state)
    state = rag_agent(state)
    result = chief_agent(state)
    return normalize_assessment(result)
