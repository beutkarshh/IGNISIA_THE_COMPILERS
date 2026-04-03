"""FastAPI application for the ICU clinical assistant."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from backend.firebase_service import FirebaseService
from backend.models import AssessmentResponse, AssessmentSummary, HealthResponse, PatientAssessmentRequest
from backend.workflow import run_patient_assessment


app = FastAPI(
    title="ICU Clinical Assistant API",
    version="2.0.0",
    description="Phase 2 integration layer for the ICU sepsis assessment agents.",
)

firebase_service = FirebaseService()
app.state.firebase_service = firebase_service


def _build_response(assessment_id: str, request: PatientAssessmentRequest, result: Dict[str, Any]) -> AssessmentResponse:
    timeline_length = len(result.get("timeline_history", []))
    return AssessmentResponse(
        assessment_id=assessment_id,
        patient_id=request.patient_id,
        admission_id=request.admission_id,
        age=request.age,
        gender=request.gender,
        admission_diagnosis=request.admission_diagnosis,
        risk_score=int(result.get("risk_score", 0)),
        risk_level=str(result.get("risk_level", "LOW")),
        current_timepoint_index=int(result.get("current_timepoint_index", request.current_timepoint_index or 0)),
        timeline_length=timeline_length,
        generated_at=str(result.get("generated_at", datetime.utcnow().isoformat())),
        processing_time_ms=result.get("processing_time_ms"),
        raw_risk_score=result.get("raw_risk_score"),
        diagnostic_criteria_met=list(result.get("diagnostic_criteria_met", [])),
        outlier_alerts=list(result.get("outlier_alerts", [])),
        risk_flags=list(result.get("risk_flags", [])),
        treatment_recommendations=list(result.get("treatment_recommendations", [])),
        final_report=str(result.get("final_report", "")),
        firebase_stored=False,
        storage_backend=firebase_service.storage_backend,
    )


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="icu-clinical-assistant",
        firebase_enabled=firebase_service.enabled,
        storage_backend=firebase_service.storage_backend,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/assess-patient", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def assess_patient(request: PatientAssessmentRequest) -> AssessmentResponse:
    result = run_patient_assessment(
        request.model_dump(exclude_none=True),
        current_timepoint_index=request.current_timepoint_index,
    )

    assessment_id = str(uuid4())
    response = _build_response(assessment_id, request, result)
    response.firebase_stored = True
    response.storage_backend = firebase_service.storage_backend
    stored = firebase_service.save_assessment(response.model_dump())
    response.assessment_id = stored["assessment_id"]
    return response


@app.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str) -> AssessmentResponse:
    assessment = firebase_service.get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@app.get("/patients/{patient_id}/assessments", response_model=List[AssessmentSummary])
def list_patient_assessments(patient_id: str) -> List[AssessmentSummary]:
    assessments = firebase_service.list_patient_assessments(patient_id)
    return [AssessmentSummary.model_validate(item) for item in assessments]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
