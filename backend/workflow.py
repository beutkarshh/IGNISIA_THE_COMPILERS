"""Backend orchestration layer for calling the existing agent workflow."""

from __future__ import annotations

import time
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .agents.chief_agent import chief_agent
from .agents.lab_mapper_agent import lab_mapper_agent
from .agents.note_parser_agent import note_parser_agent
from .agents.rag_agent import rag_agent
from .utils.timeline_generator import generate_patient_timeline, resolve_current_timepoint_index
from .utils.logger import setup_logger, log_assessment_start, log_assessment_complete

logger = setup_logger('workflow', level='INFO')


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
    """Run patient assessment with error handling, validation, and structured logging."""
    
    start_time = time.time()
    assessment_id = str(uuid4())
    patient_id = patient_data.get('patient_id', 'UNKNOWN')
    
    # Log start
    log_assessment_start(logger, patient_id, assessment_id)
    
    # Validate required fields
    required_fields = ['patient_id', 'admission_id', 'age', 'gender', 'admission_diagnosis']
    missing = [field for field in required_fields if field not in patient_data]
    
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
    # Validate timeline exists (or can be generated)
    if 'timeline' not in patient_data and 'timepoints' not in patient_data:
        logger.warning(f"No timeline provided for patient {patient_data['patient_id']}, generating default")
    
    try:
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

        # Track agent timings
        agent_timings = {}
        
        # Note Parser
        t0 = time.time()
        state = note_parser_agent(state)
        agent_timings['note_parser'] = int((time.time() - t0) * 1000)
        
        # Lab Mapper
        t0 = time.time()
        state = lab_mapper_agent(state)
        agent_timings['lab_mapper'] = int((time.time() - t0) * 1000)
        
        # RAG Agent
        t0 = time.time()
        state = rag_agent(state)
        agent_timings['rag_agent'] = int((time.time() - t0) * 1000)
        
        # Chief Agent
        t0 = time.time()
        result = chief_agent(state)
        agent_timings['chief_agent'] = int((time.time() - t0) * 1000)
        
        # Calculate total time
        total_time_ms = int((time.time() - start_time) * 1000)
        result['processing_time_ms'] = total_time_ms
        
        # Log completion
        log_assessment_complete(
            logger,
            patient_id,
            assessment_id,
            result['risk_score'],
            total_time_ms,
            agent_timings
        )
        
        return normalize_assessment(result)
        
    except Exception as e:
        logger.error(
            f"Assessment failed: {e}",
            extra={
                'patient_id': patient_id,
                'assessment_id': assessment_id,
                'event': 'assessment_error'
            },
            exc_info=True
        )
        
        # Return safe fallback response
        return {
            'patient_id': patient_data.get('patient_id', 'UNKNOWN'),
            'admission_id': patient_data.get('admission_id', 'UNKNOWN'),
            'age': patient_data.get('age', 0),
            'gender': patient_data.get('gender', 'UNKNOWN'),
            'admission_diagnosis': patient_data.get('admission_diagnosis', 'UNKNOWN'),
            'risk_score': 0,
            'risk_level': 'UNKNOWN',
            'error': str(e),
            'diagnostic_criteria_met': [],
            'treatment_recommendations': [],
            'outlier_alerts': [],
            'risk_flags': [],
            'final_report': f"Assessment failed due to error: {str(e)}\n\nPlease review patient data and try again.",
            'generated_at': datetime.utcnow().isoformat(),
            'system_version': '1.0.0',
            'firebase_stored': False,
            'storage_backend': 'error'
        }
