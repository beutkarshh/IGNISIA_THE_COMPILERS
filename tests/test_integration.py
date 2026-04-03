"""Integration tests for the phase 2 backend API."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


CLIENT = TestClient(app)
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "mimic_samples"


def load_patient(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


def test_assess_patient_returns_expected_sepsis_score() -> None:
    patient = load_patient("patient_001_sepsis.json")

    response = CLIENT.post("/assess-patient", json=patient)

    assert response.status_code == 201
    payload = response.json()

    assert payload["patient_id"] == "001"
    assert payload["risk_score"] == 90
    assert payload["risk_level"] == "CRITICAL"
    assert payload["current_timepoint_index"] == 3
    assert "SIRS" in payload["diagnostic_criteria_met"]
    assert "qSOFA" in payload["diagnostic_criteria_met"]
    assert "Elevated_Lactate" in payload["diagnostic_criteria_met"]
    assert payload["firebase_stored"] is True
    assert payload["final_report"]


def test_assessment_can_be_retrieved_and_listed() -> None:
    patient = load_patient("patient_001_sepsis.json")
    created = CLIENT.post("/assess-patient", json=patient).json()

    retrieved = CLIENT.get(f"/assessments/{created['assessment_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["assessment_id"] == created["assessment_id"]

    listing = CLIENT.get(f"/patients/{created['patient_id']}/assessments")
    assert listing.status_code == 200
    assert any(item["assessment_id"] == created["assessment_id"] for item in listing.json())


def test_timeline_generator_handles_critical_timepoint() -> None:
    patient = load_patient("patient_001_sepsis.json")
    patient.pop("timeline")
    patient["metadata"]["critical_timepoint"] = "2024-03-02T02:00:00Z"

    response = CLIENT.post("/assess-patient", json=patient)
    assert response.status_code == 201

    payload = response.json()
    assert payload["risk_score"] == 90
    assert payload["timeline_length"] >= 4
    assert payload["current_timepoint_index"] == 3
