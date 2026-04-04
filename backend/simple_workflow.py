"""Simplified workflow for testing."""

import time
import random
from datetime import datetime
from typing import Dict, Any, Optional


def run_patient_assessment(patient_data: Dict[str, Any], current_timepoint_index: Optional[int] = None) -> Dict[str, Any]:
    """Simplified patient assessment for testing."""
    
    patient_id = patient_data.get('patient_id', 'UNKNOWN')
    
    # Mock assessment result
    result = {
        "patient_id": patient_id,
        "admission_id": patient_data.get('admission_id', 'ADM001'),
        "assessment_id": f"ASSESS_{patient_id}_{int(time.time())}",
        "risk_score": random.randint(15, 85),
        "risk_level": "MEDIUM",
        "confidence_score": random.uniform(0.7, 0.95),
        "sepsis_score": random.randint(10, 60),
        "overall_summary": "Patient showing stable vital signs with some elevation in inflammatory markers.",
        "treatment_recommendations": [
            {
                "priority": 1,
                "action": "Continue current monitoring protocol",
                "rationale": "Patient vitals are within acceptable range",
                "guideline_source": "[Standard ICU Protocol]"
            }
        ],
        "clinical_notes": [
            "Patient appears alert and oriented",
            "Blood pressure within normal limits",
            "No acute signs of sepsis at this time"
        ],
        "generated_at": datetime.now().isoformat(),
        "processing_time_ms": random.randint(1500, 4500),
        "diagnostic_criteria_met": [],
        "outlier_alerts": [],
        "lab_trends": [],
        "vital_trends": {},
        "risk_flags": []
    }
    
    # Determine risk level based on score
    if result["risk_score"] >= 70:
        result["risk_level"] = "HIGH"
        result["overall_summary"] = "Patient showing concerning trends requiring immediate attention."
        result["diagnostic_criteria_met"] = ["SIRS Criteria", "Elevated Lactate"]
    elif result["risk_score"] >= 40:
        result["risk_level"] = "MEDIUM"
        result["diagnostic_criteria_met"] = ["Elevated WBC"]
    else:
        result["risk_level"] = "LOW"
        result["overall_summary"] = "Patient stable with normal clinical indicators."
        
    return result