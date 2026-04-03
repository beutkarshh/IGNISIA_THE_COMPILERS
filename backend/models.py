"""Pydantic models for the phase 2 backend API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Safety disclaimer for all assessments
SAFETY_DISCLAIMER = """⚠️ CLINICAL DECISION SUPPORT TOOL - NOT A DIAGNOSTIC DEVICE

This system is designed to assist healthcare professionals in clinical 
decision-making and is NOT intended to replace clinical judgment. All 
recommendations must be validated by qualified medical personnel.

IMPORTANT LIMITATIONS:
• This tool has not been FDA-approved for diagnostic use
• Results are based on AI analysis and may contain errors
• Clinical decisions should be made by qualified healthcare providers
• Always verify critical findings with additional testing
• Not suitable as the sole basis for patient care decisions

Use of this system constitutes acceptance of these limitations."""


class VitalSignsModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    temperature: float
    spo2: int


class LabValuesModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    wbc: float
    lactate: float
    creatinine: float
    bun: int
    platelets: int


class TimelinePointModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: str
    time_label: str
    hours_since_admission: int
    vitals: VitalSignsModel
    labs: LabValuesModel
    notes: str


class PatientAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    patient_id: str
    admission_id: str
    age: int
    gender: str
    admission_diagnosis: str
    timeline: List[TimelinePointModel] = Field(default_factory=list)
    current_timepoint_index: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssessmentSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    assessment_id: str
    patient_id: str
    admission_id: str
    risk_score: int
    risk_level: str
    current_timepoint_index: int
    timeline_length: int
    generated_at: str
    processing_time_ms: Optional[int] = None


class AssessmentResponse(AssessmentSummary):
    model_config = ConfigDict(extra="allow")

    age: int
    gender: str
    admission_diagnosis: str
    raw_risk_score: Optional[int] = None
    diagnostic_criteria_met: List[str] = Field(default_factory=list)
    outlier_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    risk_flags: List[Dict[str, Any]] = Field(default_factory=list)
    treatment_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    final_report: str = ""
    firebase_stored: bool = False
    storage_backend: str = "memory"
    
    # NEW: Safety disclaimer
    safety_disclaimer: str = Field(
        default=SAFETY_DISCLAIMER,
        description="Legal disclaimer for clinical decision support"
    )


class HealthResponse(BaseModel):
    status: str
    service: str
    firebase_enabled: bool
    storage_backend: str
    timestamp: str


class ErrorResponse(BaseModel):
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
