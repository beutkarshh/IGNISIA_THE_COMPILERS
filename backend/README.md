# Backend API - Quick Start Guide

## Overview

The backend provides a REST API for the ICU Clinical Assistant, enabling real-time sepsis risk assessment using multi-agent AI.

**Tech Stack**: FastAPI + Python 3.13 + Google Gemini + Firebase/Firestore

---

## ⚠️ IMPORTANT SAFETY NOTICE

**THIS IS A CLINICAL DECISION SUPPORT TOOL - NOT A DIAGNOSTIC DEVICE**

This system:
- ❌ Is NOT FDA-approved for diagnostic use
- ❌ Should NOT replace clinical judgment
- ❌ Should NOT be used as the sole basis for treatment decisions
- ✅ Is designed to ASSIST qualified healthcare professionals
- ✅ Requires validation by medical personnel

All users must acknowledge these limitations before use.

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+ (3.13 recommended)
python --version

# Virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in project root:

```env
# Required: Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Firebase (uses in-memory storage if not configured)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
# OR
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Optional: Supabase (for MIMIC-III data)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 4. Start the Server

```bash
# Development mode (auto-reload)
uvicorn backend.main:app --reload --port 8000

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

---

## 📚 API Endpoints

### Health Check
```bash
GET /health
```

**Response**:
```json
{
  "status": "ok",
  "service": "icu-clinical-assistant",
  "firebase_enabled": false,
  "storage_backend": "memory",
  "timestamp": "2026-04-03T13:00:00Z"
}
```

---

### Assess Patient
```bash
POST /assess-patient
Content-Type: application/json
```

**Request Body**:
```json
{
  "patient_id": "001",
  "admission_id": "ADM001",
  "age": 68,
  "gender": "M",
  "admission_diagnosis": "Pneumonia",
  "timeline": [
    {
      "timestamp": "2024-01-15T08:00:00",
      "time_label": "Hour 0",
      "hours_since_admission": 0,
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
      "notes": "Patient admitted with pneumonia..."
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "assessment_id": "abc-123-def",
  "patient_id": "001",
  "risk_score": 90,
  "risk_level": "CRITICAL",
  "diagnostic_criteria_met": ["SIRS", "qSOFA", "Elevated_Lactate"],
  "treatment_recommendations": [
    {
      "priority": 1,
      "action": "Broad-spectrum antibiotics within 1 hour",
      "rationale": "Sepsis-3 guidelines: Early antimicrobial therapy",
      "guideline_source": "[Surviving Sepsis Campaign]"
    }
  ],
  "outlier_alerts": [],
  "final_report": "Patient meets sepsis criteria...",
  "generated_at": "2026-04-03T13:00:00Z",
  "firebase_stored": true
}
```

---

### Get Assessment
```bash
GET /assessments/{assessment_id}
```

**Response** (200 OK):
```json
{
  "assessment_id": "abc-123-def",
  "patient_id": "001",
  "risk_score": 90,
  ...
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Assessment not found"
}
```

---

### List Patient Assessments
```bash
GET /patients/{patient_id}/assessments
```

**Response** (200 OK):
```json
[
  {
    "assessment_id": "abc-123-def",
    "patient_id": "001",
    "risk_score": 90,
    "risk_level": "CRITICAL",
    "current_timepoint_index": 3,
    "timeline_length": 4,
    "generated_at": "2026-04-03T13:00:00Z"
  }
]
```

---

## 🧪 Testing

### Option 1: Using Test Data Files

```bash
# Test with sepsis patient
curl -X POST http://localhost:8000/assess-patient \
  -H "Content-Type: application/json" \
  -d @data/mimic_samples/patient_001_sepsis.json

# Expected: risk_score = 90, risk_level = "CRITICAL"
```

### Option 2: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/assess-patient",
    json={
        "patient_id": "TEST001",
        "admission_id": "ADM001",
        "age": 65,
        "gender": "F",
        "admission_diagnosis": "Pneumonia",
        "timeline": [...]
    }
)

print(response.json())
```

### Option 3: Interactive API Docs

Visit: **http://localhost:8000/docs**

FastAPI provides an interactive Swagger UI where you can:
- View all endpoints
- Try API calls directly in the browser
- See request/response schemas

---

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI App   │  ← main.py (API routes)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Workflow     │  ← workflow.py (orchestration)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│          Agent Pipeline                 │
│  1. Note Parser   (symptoms)            │
│  2. Lab Mapper    (trends)              │
│  3. RAG Agent     (criteria)            │
│  4. Chief Agent   (risk scoring)        │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Firebase/Memory │  ← firebase_service.py
└─────────────────┘
```

---

## 📁 Project Structure

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application (97 lines)
├── models.py                # Pydantic schemas (97 lines)
├── workflow.py              # Agent orchestration (116 lines)
└── firebase_service.py      # Storage service (110 lines)

agents/
├── note_parser_agent.py     # Extract symptoms
├── lab_mapper_agent.py      # Detect trends
├── rag_agent.py             # Apply criteria
└── chief_agent.py           # Calculate risk

utils/
├── timeline_generator.py    # Timeline normalization
└── outlier_detector.py      # Statistical analysis

data/mimic_samples/
├── patient_001_sepsis.json  # Test: Sepsis case
├── patient_002_lab_error.json  # Test: Lab error
└── patient_003_stable.json  # Test: Stable patient
```

---

## ⚙️ Configuration

### Firebase Setup (Optional)

1. Create Firebase project: https://console.firebase.google.com
2. Enable Firestore
3. Download service account JSON
4. Add to `.env`:
   ```env
   FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
   ```

**Note**: If Firebase is not configured, the system automatically uses in-memory storage (perfect for development/testing).

### Gemini API Setup (Required)

1. Get API key: https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
```bash
# Solution: Ensure you're in the project root and PYTHONPATH is set
cd d:\Projects\MIT_Ignisia
set PYTHONPATH=d:\Projects\MIT_Ignisia  # Windows
export PYTHONPATH=/path/to/MIT_Ignisia  # Linux/Mac
```

### Issue: Numpy warnings on Windows
```bash
# These warnings are safe to ignore:
# "Numpy built with MINGW-W64 on Windows 64 bits is experimental"

# To suppress:
set PYTHONWARNINGS=ignore  # Windows
export PYTHONWARNINGS=ignore  # Linux/Mac
```

### Issue: API hangs on assessment
```bash
# Cause: Gemini API timeout
# Solution: Check your GOOGLE_API_KEY and internet connection
# The system now has 60s timeout on LLM calls
```

### Issue: Firebase errors
```bash
# Solution: Firebase is optional - remove Firebase env vars to use memory storage
# System will automatically fall back to in-memory storage
```

---

## 📊 Example Workflows

### Workflow 1: Single Assessment
```bash
# 1. Start server
uvicorn backend.main:app --reload

# 2. Assess patient
curl -X POST http://localhost:8000/assess-patient \
  -H "Content-Type: application/json" \
  -d @data/mimic_samples/patient_001_sepsis.json

# 3. Get assessment
curl http://localhost:8000/assessments/{assessment_id}
```

### Workflow 2: Monitor Patient Timeline
```bash
# Assess at different timepoints
curl -X POST http://localhost:8000/assess-patient \
  -d '{"patient_id": "001", "current_timepoint_index": 0, ...}'

curl -X POST http://localhost:8000/assess-patient \
  -d '{"patient_id": "001", "current_timepoint_index": 1, ...}'

# List all assessments
curl http://localhost:8000/patients/001/assessments
```

---

## 🔐 Security Notes

**Development Mode**:
- ✅ CORS disabled (localhost only)
- ✅ No authentication required
- ✅ Memory storage (no persistence)

**Production Recommendations**:
- 🔒 Enable CORS with specific origins
- 🔒 Add JWT authentication
- 🔒 Use Firebase/Firestore for persistence
- 🔒 Add rate limiting
- 🔒 Enable HTTPS
- 🔒 Add request validation middleware

---

## 📈 Performance

**Typical Response Times**:
- Health check: <10ms
- Assessment (simple): 2-5 seconds (LLM calls)
- Assessment (complex): 5-10 seconds
- Get assessment: <50ms
- List assessments: <100ms

**Bottlenecks**:
- Gemini API calls (2-8s per agent)
- RAG retrieval (<1s)
- Outlier detection (<100ms)

**Optimization**:
- Cache LLM responses for similar inputs
- Preload embeddings on startup
- Use async operations for parallel agent calls

---

## 📝 API Response Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Successful GET request |
| 201 | Created | Assessment created |
| 404 | Not Found | Assessment/patient not found |
| 422 | Validation Error | Invalid request body |
| 500 | Internal Error | Server error |

---

## 🤝 Support

**Issues**: Report to project lead  
**Documentation**: See `docs/` folder  
**API Docs**: http://localhost:8000/docs (when server running)

---

**Version**: 2.0.0  
**Last Updated**: April 3, 2026  
**Maintainer**: ICU Clinical Assistant Team
