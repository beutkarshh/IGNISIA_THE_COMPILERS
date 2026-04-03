# Phase 2 Integration - Teammate Handoff Document

**Date**: April 3, 2026  
**Project**: ICU Clinical Assistant - Agentic Sepsis Detection System  
**Repository**: https://github.com/beutkarshh/IGNISIA_THE_COMPILERS.git  
**Phase**: Phase 2 - Integration (8-10 hours estimated)

---

## 📋 What's Already Done (Phase 1 - COMPLETED)

### ✅ Components Built:
1. **Patient Data Schema** - `data/mimic_samples/*.json` (3 patient scenarios)
2. **Agent 2: Lab Mapper** - `agents/lab_mapper_agent.py` (trend detection)
3. **Agent 3: RAG Agent** - `agents/rag_agent.py` (diagnostic criteria)
4. **Agent 4: Chief Agent** - `agents/chief_agent.py` (risk scoring)
5. **Outlier Detector** - `utils/outlier_detector.py` (Z-score + IQR)
6. **Supabase Integration** - `tests/test_supabase.py` (real MIMIC-III data)
7. **Patient State Schema** - `agents/state_schema.py`

### ✅ Test Results:
- **All agents working**: Lab Mapper, RAG Agent, Chief Agent
- **Sepsis detection**: Successfully detected at Hour 18 (Risk Score: 90/100)
- **Diagnostic criteria**: SIRS, qSOFA, Elevated Lactate all working
- **Database**: Connected to Supabase with 100 patients, 758K vitals, 76K labs
- **Real data**: Processed Subject 10006 (SEPSIS case, Lactate 4.4 mmol/L)

### ✅ Files Created:
```
d:\Projects\MIT_Ignisia\
├── agents/
│   ├── lab_mapper_agent.py     ← Temporal trend detection
│   ├── rag_agent.py             ← Clinical guideline retrieval
│   ├── chief_agent.py           ← Risk scoring
│   └── state_schema.py          ← PatientState data model
├── data/
│   └── mimic_samples/           ← 3 patient JSON files
├── utils/
│   ├── outlier_detector.py      ← Anomaly detection
│   └── mimic_adapter.py         ← MIMIC-III format converter
├── tests/                       ← 6 test suites (all passing)
├── .env                         ← Supabase credentials
└── requirements.txt             ← All dependencies
```

---

## 🎯 Your Tasks (Phase 2)

You need to build **7 components** to integrate everything:

### 1. FastAPI Backend (`backend/main.py`)
**What**: Create REST API with 3 endpoints  
**Why**: Allow frontend/users to interact with agents via HTTP

**Endpoints to create**:
```python
POST   /assess-patient      # Run assessment on patient timeline
GET    /assessments         # Get all assessment history
GET    /patient/{id}        # Get specific patient data
```

**Input/Output Examples**: See Section 4 below

---

### 2. Firebase Service (`backend/firebase_service.py`)
**What**: Module for Firebase Auth + Firestore operations  
**Why**: Persist assessments and authenticate users

**Functions to create**:
```python
def verify_token(token: str) -> dict  # Verify Firebase ID token
def save_assessment(assessment: dict) -> str  # Save to Firestore
def get_user_assessments(user_id: str) -> list  # Fetch history
```

**Firebase Setup**:
- **Already done**: Supabase credentials in `.env`
- **You need to**: Use Firebase Admin SDK for Firestore
- **Collections**: `/assessments/{assessment_id}`

---

### 3. Pydantic Models (`backend/models.py`)
**What**: Request/response schemas for FastAPI validation  
**Why**: Type safety and automatic API documentation

**Models to create**:
```python
class VitalsInput(BaseModel):
    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    temperature: float
    spo2: int

class LabsInput(BaseModel):
    wbc: float
    lactate: float
    creatinine: float
    bun: int
    platelets: int

class TimePointInput(BaseModel):
    time_label: str
    hours_since_admission: int
    timestamp: str
    vitals: VitalsInput
    labs: LabsInput
    notes: str

class PatientDataInput(BaseModel):
    patient_id: str
    admission_id: str
    age: int
    gender: str
    admission_diagnosis: str
    timeline: List[TimePointInput]

class RiskReportOutput(BaseModel):
    patient_id: str
    risk_score: int
    risk_level: str
    lab_trends: list
    diagnostic_criteria_met: list
    treatment_recommendations: list
    outlier_alerts: list
    generated_at: str
```

---

### 4. LangGraph Workflow (`backend/workflow.py`)
**What**: Orchestration module that runs all agents in sequence  
**Why**: Connect Lab Mapper → RAG → Chief → Outlier Detection

**Function to create**:
```python
def run_assessment(patient_data: dict) -> dict:
    """
    Run full agent pipeline on patient data
    
    Steps:
    1. Initialize state from patient data
    2. Run Lab Mapper Agent (detect trends)
    3. Run RAG Agent (apply criteria)
    4. Run Chief Agent (calculate risk)
    5. Run Outlier Detection
    6. Return final report
    """
    # Import existing agents
    from agents.lab_mapper_agent import lab_mapper_agent
    from agents.rag_agent import rag_agent
    from agents.chief_agent import calculate_risk_score, generate_risk_level
    from utils.outlier_detector import analyze_all_labs
    
    # Build state (see state_schema.py for structure)
    # Run agents in sequence
    # Return final report
```

---

### 5. Timeline Generator (`utils/timeline_generator.py`)
**What**: Step-by-step simulation engine  
**Why**: Process patient timeline incrementally (not all at once)

**Function to create**:
```python
def generate_timeline_assessment(patient_data: dict) -> list:
    """
    Process patient timeline step-by-step
    
    Returns:
    [
        {
            "timepoint": "Hour 0",
            "event": "stable",
            "risk_score": 20,
            "key_findings": []
        },
        {
            "timepoint": "Hour 6",
            "event": "mild fever",
            "risk_score": 35,
            "key_findings": ["Temperature rising"]
        },
        # ... etc
    ]
    """
    # For each timepoint in timeline:
    #   - Run assessment on history up to that point
    #   - Track risk score progression
    #   - Identify key events
```

---

### 6. Treatment Recommendation Engine (Enhance `agents/chief_agent.py`)
**What**: Expand existing treatment function  
**Why**: Generate actionable, prioritized treatment plans

**Already exists**: `generate_treatment_recommendations()` in `chief_agent.py`

**You need to**: Enhance it to return more detailed recommendations:
```python
{
    "priority": 1,
    "action": "Broad-spectrum antibiotics within 1 hour",
    "rationale": "Sepsis-3: Early antimicrobial therapy reduces mortality",
    "guideline_source": "[Surviving Sepsis Campaign, 2021]",
    "specific_medications": ["Piperacillin-tazobactam 4.5g IV", "Vancomycin 15-20mg/kg IV"],
    "monitoring": "Monitor for allergic reactions, obtain cultures first"
}
```

---

### 7. End-to-End Integration Tests (`tests/test_integration.py`)
**What**: Full pipeline tests for 3 scenarios  
**Why**: Validate entire system before demo

**Test scenarios**:
```python
def test_scenario_1_early_sepsis():
    """Patient 001: Should detect sepsis at Hour 18, Risk=90"""
    # Load patient_001_sepsis.json
    # Call POST /assess-patient
    # Assert risk_score == 90
    # Assert "SIRS" in diagnostic_criteria_met
    # Assert "Early sepsis" in final_report

def test_scenario_2_lab_error():
    """Patient 002: Should flag WBC=50 as outlier"""
    # Load patient_002_lab_error.json
    # Call POST /assess-patient
    # Assert WBC outlier detected
    # Assert recommendation to redraw labs

def test_scenario_3_stable_patient():
    """Patient 003: Should maintain low risk throughout"""
    # Load patient_003_stable.json
    # Call POST /assess-patient
    # Assert risk_score < 30
    # Assert risk_level == "LOW"
```

---

## 📚 Key Information You Need

### Patient Data Format
The patient timeline data looks like this (see `data/mimic_samples/patient_001_sepsis.json`):

```json
{
  "patient_id": "001",
  "admission_id": "ADM001",
  "age": 68,
  "gender": "M",
  "admission_diagnosis": "Pneumonia",
  "timeline": [
    {
      "time_label": "Day 1 - 08:00",
      "hours_since_admission": 0,
      "timestamp": "2024-01-15T08:00:00",
      "vitals": {
        "heart_rate": 88,
        "systolic_bp": 128,
        "diastolic_bp": 78,
        "respiratory_rate": 16,
        "temperature": 37.2,
        "spo2": 98
      },
      "labs": {
        "wbc": 9.2,
        "lactate": 1.3,
        "creatinine": 0.9,
        "bun": 18,
        "platelets": 245
      },
      "notes": "Patient admitted with community-acquired pneumonia..."
    }
    // ... more timepoints
  ]
}
```

### Agent State Schema
The agents use this state structure (see `agents/state_schema.py`):

```python
state = {
    'patient_id': str,
    'admission_id': str,
    'age': int,
    'gender': str,
    'admission_diagnosis': str,
    'current_timepoint_index': int,
    'timeline_history': list,  # All timepoints up to current
    
    # Agent outputs
    'lab_trends': list,  # From Lab Mapper
    'vital_trends': dict,  # From Lab Mapper
    'diagnostic_criteria_met': list,  # From RAG Agent
    'retrieved_guidelines': list,  # From RAG Agent
    'risk_score': int,  # From Chief Agent (0-100)
    'risk_level': str,  # From Chief Agent (LOW/MEDIUM/HIGH/CRITICAL)
    'treatment_recommendations': list,  # From Chief Agent
    'outlier_alerts': list,  # From Outlier Detector
    
    'final_report': str,
    'generated_at': str,
    'system_version': '1.0.0'
}
```

### How to Call Existing Agents

```python
# 1. Lab Mapper Agent
from agents.lab_mapper_agent import lab_mapper_agent
state = lab_mapper_agent(state)
# Updates: state['lab_trends'], state['vital_trends']

# 2. RAG Agent
from agents.rag_agent import rag_agent
state = rag_agent(state)
# Updates: state['diagnostic_criteria_met'], state['retrieved_guidelines']

# 3. Chief Agent
from agents.chief_agent import calculate_risk_score, generate_risk_level, generate_treatment_recommendations
state['risk_score'] = calculate_risk_score(state)
state['risk_level'] = generate_risk_level(state['risk_score'])
state['treatment_recommendations'] = generate_treatment_recommendations(state)

# 4. Outlier Detector
from utils.outlier_detector import analyze_all_labs
outliers = analyze_all_labs(
    current_labs=current_timepoint['labs'],
    timeline_history=previous_timepoints,
    current_timestamp=current_timepoint['timestamp']
)
```

---

## 🔧 Environment Setup

### Dependencies (already in `requirements.txt`)
```bash
# Install dependencies
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Environment Variables (already in `.env`)
```env
# Supabase (already configured)
SUPABASE_URL=https://lmsrwdhebgrjbgqvjkkc.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# Gemini API (already configured)
GOOGLE_API_KEY=AIzaSy...

# You need to add Firebase:
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
```

---

## 📝 API Endpoint Specifications

### POST /assess-patient

**Request**:
```json
{
  "patient_id": "001",
  "admission_id": "ADM001",
  "age": 68,
  "gender": "M",
  "admission_diagnosis": "Pneumonia",
  "timeline": [...]  // See patient data format above
}
```

**Response**:
```json
{
  "patient_id": "001",
  "risk_score": 90,
  "risk_level": "CRITICAL",
  "lab_trends": [
    {
      "parameter": "lactate",
      "trend": "rising_sharply",
      "values": [1.3, 1.6, 2.4, 3.8],
      "change_percentage": 192.3
    }
  ],
  "diagnostic_criteria_met": ["SIRS", "qSOFA", "Elevated_Lactate"],
  "retrieved_guidelines": [
    {
      "guideline_name": "Sepsis-3",
      "section": "qSOFA",
      "content": "Quick SOFA score >= 2 indicates high risk",
      "citation": "[Sepsis-3, qSOFA]",
      "relevance_score": 0.92
    }
  ],
  "treatment_recommendations": [
    {
      "priority": 1,
      "action": "Broad-spectrum antibiotics within 1 hour",
      "rationale": "Sepsis-3 guidelines",
      "guideline_source": "[Surviving Sepsis Campaign]"
    }
  ],
  "outlier_alerts": [],
  "generated_at": "2026-04-03T10:00:00Z",
  "system_version": "1.0.0"
}
```

### GET /assessments

**Response**:
```json
{
  "assessments": [
    {
      "assessment_id": "abc123",
      "patient_id": "001",
      "risk_score": 90,
      "risk_level": "CRITICAL",
      "created_at": "2026-04-03T10:00:00Z"
    }
  ]
}
```

### GET /patient/{patient_id}

**Response**:
```json
{
  "patient_id": "001",
  "admission_id": "ADM001",
  "age": 68,
  "gender": "M",
  "timeline": [...]
}
```

---

## 🧪 Testing Instructions

### 1. Test Existing Agents (verify Phase 1 works)
```bash
# Run simple agent test
python test_agents_simple.py

# Expected output: Risk Score = 90, CRITICAL, Sepsis detected
```

### 2. Test Your FastAPI Backend
```bash
# Start server
uvicorn backend.main:app --reload

# Test with curl
curl -X POST http://localhost:8000/assess-patient \
  -H "Content-Type: application/json" \
  -d @data/mimic_samples/patient_001_sepsis.json
```

### 3. Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

---

## 📦 Deliverables Checklist

By the end of Phase 2, you should have:

- [ ] `backend/main.py` - FastAPI app with 3 routes
- [ ] `backend/firebase_service.py` - Firebase Auth + Firestore
- [ ] `backend/models.py` - Pydantic schemas
- [ ] `backend/workflow.py` - LangGraph orchestration
- [ ] `utils/timeline_generator.py` - Step-by-step simulation
- [ ] Enhanced `agents/chief_agent.py` - Better treatment recommendations
- [ ] `tests/test_integration.py` - 3 scenario tests passing
- [ ] **All tests passing** (Phase 1 + Phase 2)
- [ ] **Working API** accessible at `http://localhost:8000`

---

## 🚨 Common Pitfalls to Avoid

1. **Don't modify existing agent files** - They're working! Just import and use them
2. **Use the correct state schema** - See `agents/state_schema.py`
3. **Timeline history must be incremental** - Don't pass all timepoints at once
4. **Outlier detection needs ≥2 timepoints** - Handle edge case for first timepoint
5. **Risk score is 0-100** - Not percentage (0.0-1.0)
6. **Firebase vs Supabase** - We have Supabase for data, Firebase for auth/persistence

---

## 🆘 Need Help?

### Existing Working Code to Reference:
- **Agent Pipeline**: See `test_agents_simple.py` for working example
- **Patient Data**: See `data/mimic_samples/patient_001_sepsis.json`
- **State Schema**: See `agents/state_schema.py`
- **Test Cases**: See `docs/TEST_CASES_SUMMARY.md`

### Key Contacts:
- **Project Lead**: [Your name]
- **Repository**: https://github.com/beutkarshh/IGNISIA_THE_COMPILERS.git
- **Documentation**: See `docs/` folder

---

## ⏱️ Time Estimate

| Task | Estimated Time |
|------|----------------|
| FastAPI setup | 1 hour |
| Firebase service | 2 hours |
| Pydantic models | 30 minutes |
| LangGraph workflow | 1.5 hours |
| Timeline generator | 1.5 hours |
| Treatment enhancements | 1 hour |
| Integration tests | 2 hours |
| **Total** | **~9.5 hours** |

---

## ✅ Success Criteria

**Your Phase 2 is complete when**:
1. ✅ FastAPI server starts without errors
2. ✅ POST /assess-patient returns correct risk score for Patient 001 (should be 90)
3. ✅ All 3 integration test scenarios pass
4. ✅ Assessments save to Firebase and can be retrieved
5. ✅ Timeline shows risk progression over time
6. ✅ Treatment recommendations include specific actions with citations

---

**Good luck! The hard part (agents) is done. You're just connecting the pieces! 🚀**
