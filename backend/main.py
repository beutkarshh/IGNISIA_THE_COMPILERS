"""FastAPI application for the ICU clinical assistant."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.firebase_service import FirebaseService
from backend.models import (
    AssessmentResponse, 
    AssessmentSummary, 
    HealthResponse, 
    PatientAssessmentRequest,
    MIMICPatientListItem,
    MIMICPatientResponse
)
from backend.workflow import run_patient_assessment
from utils.logger import setup_logger
from utils.mimic_adapter import get_patient_by_diagnosis, convert_to_agent_format

logger = setup_logger('api', level='INFO')


app = FastAPI(
    title="ICU Clinical Assistant API",
    version="2.0.0",
    description="Phase 2 integration layer for the ICU sepsis assessment agents.",
)

firebase_service = FirebaseService()
app.state.firebase_service = firebase_service


# Simple in-memory response cache (for repeated assessments)
_RESPONSE_CACHE: Dict[str, tuple[AssessmentResponse, float]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _generate_request_hash(request: PatientAssessmentRequest) -> str:
    """Generate hash for caching identical requests."""
    request_dict = request.model_dump(exclude={'current_timepoint_index'})
    # Include timepoint index in hash
    request_dict['timepoint'] = request.current_timepoint_index or 0
    content = json.dumps(request_dict, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def _get_cached_response(request_hash: str) -> Optional[AssessmentResponse]:
    """Get cached response if still valid."""
    if request_hash in _RESPONSE_CACHE:
        cached_response, timestamp = _RESPONSE_CACHE[request_hash]
        age = time.time() - timestamp
        
        if age < CACHE_TTL_SECONDS:
            logger.info(f"Cache hit for request {request_hash[:8]} (age: {age:.1f}s)")
            return cached_response
        else:
            # Remove expired entry
            del _RESPONSE_CACHE[request_hash]
    
    return None


def _cache_response(request_hash: str, response: AssessmentResponse):
    """Cache response with timestamp."""
    _RESPONSE_CACHE[request_hash] = (response, time.time())
    
    # Limit cache size (FIFO eviction)
    if len(_RESPONSE_CACHE) > 100:
        oldest_key = next(iter(_RESPONSE_CACHE))
        del _RESPONSE_CACHE[oldest_key]


# API request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests with timing."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'event': 'api_request'
        }
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred during assessment",
            "error_type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


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
    # Check cache first
    request_hash = _generate_request_hash(request)
    cached = _get_cached_response(request_hash)
    
    if cached:
        # Return cached response with note
        logger.info(f"Returning cached assessment for patient {request.patient_id}")
        return cached
    
    # Run fresh assessment
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
    
    # Cache the response
    _cache_response(request_hash, response)
    
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


# MIMIC-III Supabase Integration Endpoints
@app.get("/mimic/patients", response_model=List[MIMICPatientListItem])
def search_mimic_patients(
    diagnosis: str = "SEPSIS",
    limit: int = 10
) -> List[MIMICPatientListItem]:
    """
    Search for MIMIC-III patients by diagnosis from Supabase.
    
    Args:
        diagnosis: Diagnosis keyword to search (default: "SEPSIS")
        limit: Maximum number of results (default: 10, max: 50)
        
    Returns:
        List of matching patients with basic info
    """
    if limit > 50:
        limit = 50
    
    logger.info(f"Searching MIMIC-III patients with diagnosis: {diagnosis}, limit: {limit}")
    
    try:
        patients = get_patient_by_diagnosis(diagnosis, limit)
        
        if not patients:
            logger.warning(f"No patients found with diagnosis: {diagnosis}")
            return []
        
        logger.info(f"Found {len(patients)} MIMIC-III patients")
        return [MIMICPatientListItem.model_validate(p) for p in patients]
        
    except Exception as e:
        logger.error(f"Error searching MIMIC patients: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching MIMIC-III patients: {str(e)}"
        )


@app.get("/mimic/patients/{subject_id}", response_model=MIMICPatientResponse)
def get_mimic_patient(subject_id: int) -> MIMICPatientResponse:
    """
    Get a specific MIMIC-III patient by subject_id in agent-compatible format.
    
    Args:
        subject_id: MIMIC-III subject ID
        
    Returns:
        Patient data formatted for agent processing
    """
    logger.info(f"Fetching MIMIC-III patient: {subject_id}")
    
    try:
        patient_data = convert_to_agent_format(subject_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {subject_id} not found in MIMIC-III database"
            )
        
        logger.info(f"Successfully retrieved patient {subject_id}")
        return MIMICPatientResponse.model_validate(patient_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching MIMIC patient {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching patient data: {str(e)}"
        )


@app.post("/mimic/patients/{subject_id}/assess", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def assess_mimic_patient(
    subject_id: int,
    current_timepoint_index: Optional[int] = None
) -> AssessmentResponse:
    """
    Fetch a MIMIC-III patient from Supabase and run assessment.
    
    This is a convenience endpoint that combines:
    1. Fetching patient data from Supabase
    2. Running the agent assessment workflow
    
    Args:
        subject_id: MIMIC-III subject ID
        current_timepoint_index: Optional timeline index to assess
        
    Returns:
        Complete assessment results
    """
    logger.info(f"Assessing MIMIC-III patient: {subject_id}")
    
    try:
        # Fetch patient data from Supabase
        patient_data = convert_to_agent_format(subject_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {subject_id} not found in MIMIC-III database"
            )
        
        # Run assessment
        result = run_patient_assessment(patient_data, current_timepoint_index)
        
        # Build response
        assessment_id = str(uuid4())
        
        # Create a request-like object for _build_response
        class TempRequest:
            def __init__(self, data):
                self.patient_id = data['patient_id']
                self.admission_id = data['admission_id']
                self.age = data['age']
                self.gender = data['gender']
                self.admission_diagnosis = data['admission_diagnosis']
                self.current_timepoint_index = current_timepoint_index
        
        temp_request = TempRequest(patient_data)
        response = _build_response(assessment_id, temp_request, result)
        
        # Store in Firebase
        response.firebase_stored = True
        response.storage_backend = firebase_service.storage_backend
        stored = firebase_service.save_assessment(response.model_dump())
        response.assessment_id = stored["assessment_id"]
        
        logger.info(f"Assessment complete for MIMIC patient {subject_id}: {response.risk_level}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing MIMIC patient {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during assessment: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
