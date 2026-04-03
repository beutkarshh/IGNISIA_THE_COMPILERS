# API Documentation

**ICU Clinical Assistant - REST API Reference**

Version: 1.0.0  
Base URL: `http://localhost:8000`

---

## 🚀 Quick Start

### Authentication

Currently no authentication required for development. Production deployments should implement:
- API key authentication
- OAuth 2.0 / JWT tokens  
- Rate limiting per user/organization

### Content Types

- **Request**: `application/json`
- **Response**: `application/json`
- **Character Encoding**: UTF-8

### Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Assessment created |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource not found |
| 500 | Internal Error | Server error |
| 503 | Service Unavailable | AI service down |

---

## 📡 Endpoints

### 1. Health Check

Check if the service is running and healthy.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "icu-clinical-assistant",
  "timestamp": "2026-04-03T17:30:45Z",
  "uptime_seconds": 3600,
  "agents_status": {
    "note_parser": "healthy",
    "lab_mapper": "healthy", 
    "rag_agent": "healthy",
    "chief_agent": "healthy"
  },
  "gemini_status": "connected",
  "memory_usage_mb": 245
}
```

---

### 2. Assess Patient

Primary endpoint for clinical risk assessment using collaborative AI agents.

```http
POST /assess-patient
```

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**

```json
{
  "patient_id": "string (required)",
  "admission_id": "string (optional)", 
  "age": "integer (required, 0-120)",
  "gender": "string (required, M/F/Other)",
  "admission_diagnosis": "string (required)",
  "timeline": [
    {
      "timestamp": "ISO 8601 datetime (required)",
      "time_label": "string (optional, human-readable)",
      "hours_since_admission": "number (required)",
      "vitals": {
        "heart_rate": "number (30-250)",
        "systolic_bp": "number (50-300)", 
        "diastolic_bp": "number (20-200)",
        "respiratory_rate": "number (6-60)",
        "temperature": "number (25-45)",
        "spo2": "number (50-100)",
        "map": "number (optional, calculated if missing)"
      },
      "labs": {
        "wbc": "number (0-100)",
        "lactate": "number (0-30)",
        "creatinine": "number (0-20)",
        "bun": "number (0-200)",
        "platelets": "number (0-2000)",
        "bilirubin": "number (optional)",
        "procalcitonin": "number (optional)"
      },
      "notes": "string (required, clinical notes)"
    }
  ]
}
```

**Example Request:**
```json
{
  "patient_id": "PT001",
  "admission_id": "ADM2024001", 
  "age": 68,
  "gender": "M",
  "admission_diagnosis": "Community-acquired pneumonia",
  "timeline": [
    {
      "timestamp": "2024-01-15T08:00:00Z",
      "time_label": "Day 1 - Admission",
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
      "notes": "68M admitted with fever, cough, and right lower lobe infiltrate on CXR. Started on ceftriaxone and azithromycin."
    },
    {
      "timestamp": "2024-01-15T14:00:00Z", 
      "time_label": "Day 1 - 14:00",
      "hours_since_admission": 6,
      "vitals": {
        "heart_rate": 105,
        "systolic_bp": 118,
        "diastolic_bp": 70,
        "respiratory_rate": 22,
        "temperature": 38.1,
        "spo2": 94
      },
      "labs": {
        "wbc": 12.8,
        "lactate": 2.1,
        "creatinine": 1.1,
        "bun": 22,
        "platelets": 198
      },
      "notes": "Patient developing increased work of breathing. Requiring 2L O2 via nasal cannula. Blood cultures drawn."
    }
  ]
}
```

**Successful Response (200 OK):**

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "PT001",
  "admission_id": "ADM2024001",
  "assessment_timestamp": "2026-04-03T17:30:45Z",
  
  "risk_assessment": {
    "risk_score": 85,
    "risk_level": "CRITICAL",
    "confidence": 0.92,
    "trend": "INCREASING"
  },
  
  "diagnostic_criteria": {
    "sirs_criteria": {
      "met": true,
      "score": 3,
      "details": {
        "temperature": true,
        "heart_rate": true, 
        "respiratory_rate": true,
        "wbc": false
      }
    },
    "qsofa_score": {
      "met": true,
      "score": 2,
      "details": {
        "altered_mental_status": false,
        "respiratory_rate_gte_22": true,
        "systolic_bp_lte_100": true
      }
    },
    "sepsis_criteria": {
      "infection_suspected": true,
      "organ_dysfunction": true,
      "lactate_elevated": true
    }
  },
  
  "agent_findings": {
    "note_parser": {
      "symptoms_found": [
        {
          "symptom": "fever",
          "confidence": 0.95,
          "evidence": "temperature 38.1°C at Hour 6"
        },
        {
          "symptom": "dyspnea", 
          "confidence": 0.88,
          "evidence": "increased work of breathing, requiring O2"
        },
        {
          "symptom": "hypotension",
          "confidence": 0.82,
          "evidence": "BP 118/70, trending down from 128/78"
        }
      ],
      "infection_signals": [
        {
          "signal": "pneumonia",
          "confidence": 0.98,
          "evidence": "right lower lobe infiltrate, started antibiotics"
        }
      ],
      "processing_time_ms": 8450
    },
    
    "lab_mapper": {
      "trends_analyzed": [
        {
          "parameter": "lactate",
          "trend": "INCREASING",
          "change": "+61.5%",
          "clinical_significance": "HIGH",
          "values": [1.3, 2.1]
        },
        {
          "parameter": "wbc",
          "trend": "INCREASING", 
          "change": "+39.1%",
          "clinical_significance": "MODERATE",
          "values": [9.2, 12.8]
        }
      ],
      "statistical_analysis": {
        "outliers_detected": 0,
        "correlation_analysis": "High correlation between lactate rise and clinical deterioration",
        "trend_confidence": 0.89
      },
      "processing_time_ms": 6200
    },
    
    "rag_agent": {
      "guidelines_retrieved": [
        {
          "title": "Surviving Sepsis Campaign Guidelines 2021",
          "relevance": 0.94,
          "key_recommendations": [
            "Early recognition and treatment within 1 hour",
            "Lactate-guided resuscitation", 
            "Empiric antimicrobial therapy"
          ]
        }
      ],
      "processing_time_ms": 850
    },
    
    "chief_agent": {
      "synthesis_summary": "Patient shows clear progression from pneumonia to sepsis with rising lactate, hemodynamic instability, and organ dysfunction.",
      "confidence": 0.92,
      "agent_consensus": true,
      "conflicts_resolved": 0,
      "processing_time_ms": 95
    }
  },
  
  "outlier_alerts": [
    {
      "parameter": "lactate", 
      "current_value": 2.1,
      "expected_range": "0.5-2.0",
      "severity": "WARNING",
      "message": "Lactate trending upward - monitor for tissue hypoperfusion"
    }
  ],
  
  "treatment_recommendations": [
    {
      "category": "IMMEDIATE",
      "intervention": "Fluid resuscitation",
      "details": "30 mL/kg crystalloid within 3 hours", 
      "evidence_level": "Strong recommendation (Grade 1B)",
      "source": "Surviving Sepsis Campaign 2021"
    },
    {
      "category": "IMMEDIATE",
      "intervention": "Blood cultures",
      "details": "Obtain before antibiotics if feasible within 45 minutes",
      "evidence_level": "Strong recommendation (Grade 1C)",
      "source": "Surviving Sepsis Campaign 2021"
    },
    {
      "category": "URGENT",
      "intervention": "Broad-spectrum antibiotics",
      "details": "Initiate within 1 hour of sepsis recognition",
      "evidence_level": "Strong recommendation (Grade 1B)", 
      "source": "Surviving Sepsis Campaign 2021"
    }
  ],
  
  "final_report": "⚠️ CLINICAL DECISION SUPPORT TOOL - NOT FOR PRIMARY DIAGNOSIS\n\n🚨 CRITICAL RISK DETECTED (Score: 85/100)\n\n68-year-old male with community-acquired pneumonia showing progression to sepsis:\n\n📊 DIAGNOSTIC CRITERIA MET:\n✓ SIRS Criteria: 3/4 (fever, tachycardia, tachypnea) \n✓ qSOFA Score: 2/3 (respiratory distress, hemodynamic instability)\n✓ Rising lactate (+61.5%) indicating tissue hypoperfusion\n\n🔍 KEY FINDINGS:\n• Hemodynamic instability (BP trending down)\n• Respiratory compromise (increased O2 requirement)\n• Laboratory markers of infection and organ dysfunction\n\n⚡ IMMEDIATE ACTIONS RECOMMENDED:\n1. Fluid resuscitation (30 mL/kg crystalloid)\n2. Blood cultures (if not already obtained)\n3. Broad-spectrum antibiotics within 1 hour\n4. Serial lactate monitoring\n5. Consider ICU consultation\n\n📚 Evidence: Surviving Sepsis Campaign Guidelines 2021\n\n⚠️ This assessment requires validation by qualified healthcare providers.",
  
  "safety_disclaimer": "⚠️ CLINICAL DECISION SUPPORT TOOL - NOT FDA APPROVED FOR DIAGNOSTIC USE\n\nThis system is designed to ASSIST healthcare professionals, not replace clinical judgment. All findings must be validated by qualified medical personnel. Do not use as the sole basis for treatment decisions.",
  
  "metadata": {
    "processing_time_ms": 15595,
    "agent_coordination_rounds": 1,
    "total_insights_generated": 12,
    "memory_operations": 47,
    "gemini_api_calls": 4,
    "version": "1.0.0"
  }
}
```

**Error Response (400 Bad Request):**

```json
{
  "error": "Invalid input data",
  "details": [
    {
      "field": "age",
      "message": "Age must be between 0 and 120"
    },
    {
      "field": "timeline[0].vitals.heart_rate",
      "message": "Heart rate must be between 30 and 250"
    }
  ],
  "request_id": "req_123456789"
}
```

**Error Response (500 Internal Server Error):**

```json
{
  "error": "Internal server error",
  "message": "Gemini API service temporarily unavailable",
  "request_id": "req_123456789",
  "fallback_data": {
    "risk_score": null,
    "status": "Unable to complete assessment - please retry"
  }
}
```

---

### 3. Retrieve Assessment

Get a previously completed assessment by ID.

```http
GET /assessments/{assessment_id}
```

**Path Parameters:**
- `assessment_id` (string, required): UUID of the assessment

**Example:**
```http
GET /assessments/550e8400-e29b-41d4-a716-446655440000
```

**Response:** Same structure as POST `/assess-patient` response.

---

### 4. List Patient Assessments

Get all assessments for a specific patient.

```http
GET /patients/{patient_id}/assessments
```

**Path Parameters:**
- `patient_id` (string, required): Patient identifier

**Query Parameters:**
- `limit` (integer, optional): Number of results (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `start_date` (string, optional): ISO 8601 date for filtering
- `end_date` (string, optional): ISO 8601 date for filtering

**Example:**
```http
GET /patients/PT001/assessments?limit=10&start_date=2024-01-01T00:00:00Z
```

**Response:**
```json
{
  "patient_id": "PT001",
  "total_assessments": 25,
  "assessments": [
    {
      "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
      "assessment_timestamp": "2026-04-03T17:30:45Z",
      "risk_score": 85,
      "risk_level": "CRITICAL",
      "admission_id": "ADM2024001"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

---

### 5. Agent Memory Status

Get current state of agent shared memory (debugging/monitoring).

```http
GET /agents/memory
```

**Response:**
```json
{
  "memory_status": {
    "total_insights": 12,
    "active_findings": 8,
    "agent_messages": 3,
    "last_updated": "2026-04-03T17:30:45Z"
  },
  "insights_by_agent": {
    "note_parser": 6,
    "lab_mapper": 4, 
    "rag_agent": 2,
    "chief_agent": 0
  },
  "recent_messages": [
    {
      "from_agent": "lab_mapper",
      "to_agent": "note_parser", 
      "message": "Lactate trending up - confirm infection signals",
      "timestamp": "2026-04-03T17:30:40Z"
    }
  ]
}
```

---

## 🔄 Data Models

### Patient Timeline Entry

```typescript
interface TimelineEntry {
  timestamp: string;           // ISO 8601 datetime
  time_label?: string;         // Human-readable label
  hours_since_admission: number;
  vitals: {
    heart_rate: number;        // beats/min (30-250)
    systolic_bp: number;       // mmHg (50-300) 
    diastolic_bp: number;      // mmHg (20-200)
    respiratory_rate: number;  // breaths/min (6-60)
    temperature: number;       // Celsius (25-45)
    spo2: number;             // % (50-100)
    map?: number;             // Mean arterial pressure
  };
  labs: {
    wbc: number;              // K/uL (0-100)
    lactate: number;          // mmol/L (0-30)
    creatinine: number;       // mg/dL (0-20)
    bun: number;              // mg/dL (0-200)
    platelets: number;        // K/uL (0-2000)
    bilirubin?: number;       // mg/dL
    procalcitonin?: number;   // ng/mL
  };
  notes: string;              // Clinical notes
}
```

### Risk Assessment

```typescript
interface RiskAssessment {
  risk_score: number;         // 0-100
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  confidence: number;         // 0-1
  trend: "STABLE" | "IMPROVING" | "WORSENING" | "INCREASING";
}
```

### Diagnostic Criteria

```typescript
interface DiagnosticCriteria {
  sirs_criteria: {
    met: boolean;
    score: number;            // 0-4
    details: {
      temperature: boolean;    // >38°C or <36°C
      heart_rate: boolean;     // >90 bpm
      respiratory_rate: boolean; // >20 or PaCO2 <32
      wbc: boolean;            // >12K or <4K or >10% bands
    };
  };
  qsofa_score: {
    met: boolean;             // Score ≥2
    score: number;            // 0-3
    details: {
      altered_mental_status: boolean; // GCS <15
      respiratory_rate_gte_22: boolean;
      systolic_bp_lte_100: boolean;
    };
  };
  sepsis_criteria: {
    infection_suspected: boolean;
    organ_dysfunction: boolean;
    lactate_elevated: boolean; // >2 mmol/L
  };
}
```

---

## 🧪 Testing

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Quick assessment test
curl -X POST http://localhost:8000/assess-patient \
  -H "Content-Type: application/json" \
  -d @data/mimic_samples/patient_001_sepsis.json

# Agent memory status
curl http://localhost:8000/agents/memory
```

### Sample Data

Sample patient files are provided in `data/mimic_samples/`:
- `patient_001_sepsis.json` - Classic sepsis progression
- `patient_002_uti_resolved.json` - Non-sepsis case
- `patient_003_septic_shock.json` - Severe septic shock

---

## 🔧 Configuration

### Environment Variables

The API behavior can be configured via environment variables:

```bash
# Core API settings
PORT=8000                    # Server port
HOST=0.0.0.0                # Bind address
WORKERS=1                   # Uvicorn workers

# AI Configuration  
GEMINI_API_KEY=xxx          # Google Gemini API key
GEMINI_MODEL=gemini-2.0-flash # Model version

# Database (optional)
SUPABASE_URL=xxx            # Supabase URL
SUPABASE_ANON_KEY=xxx       # Supabase anon key

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
STRUCTURED_LOGS=true        # JSON logging format

# Performance
MAX_CONCURRENT_REQUESTS=10  # Request concurrency
AGENT_TIMEOUT_SECONDS=30    # Agent timeout
RETRY_ATTEMPTS=3            # API retry attempts
```

### Deployment Settings

```bash
# Production
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]

# Development  
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["*"]
```

---

## 🚨 Error Handling

### Error Response Format

All errors follow this consistent format:

```json
{
  "error": "Error category",
  "message": "Human-readable description",
  "details": "Additional technical details", 
  "request_id": "Unique request identifier",
  "timestamp": "2026-04-03T17:30:45Z"
}
```

### Common Errors

#### 400 Bad Request - Invalid Input

```json
{
  "error": "Invalid input data",
  "details": [
    {
      "field": "timeline[0].vitals.heart_rate",
      "message": "Value must be between 30 and 250",
      "received": 300
    }
  ]
}
```

#### 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 60 requests per minute allowed",
  "retry_after": 45
}
```

#### 503 Service Unavailable

```json
{
  "error": "Service temporarily unavailable", 
  "message": "Gemini API service is down",
  "fallback_available": true
}
```

---

## 📊 Rate Limits

### Current Limits (Development)

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/health` | 100/min | per IP |
| `/assess-patient` | 60/min | per IP |
| `/assessments/*` | 300/min | per IP |
| `/agents/*` | 20/min | per IP |

### Production Limits

Rate limits in production should be:
- Per authenticated user/API key
- Tiered based on subscription level
- With burst allowances for emergency use

---

## 🔒 Security

### Input Validation

- All numeric values have range validation
- String fields are sanitized against injection
- File uploads not currently supported (security consideration)
- JSON payloads limited to 1MB

### Authentication (Future)

Planned authentication mechanisms:
- API key authentication for service-to-service
- OAuth 2.0 / OpenID Connect for user authentication
- JWT tokens with role-based access control
- Integration with hospital SSO systems

### Data Privacy

- Patient identifiers should be de-identified/hashed
- PHI (Protected Health Information) handling compliance
- Request/response logging excludes sensitive data
- Audit trails for all assessment requests

---

## 📈 Monitoring

### Metrics Exposed

The API exposes metrics for monitoring:

```bash
# Application metrics
GET /metrics

# Health with detailed status
GET /health/detailed
```

**Response:**
```json
{
  "performance": {
    "avg_response_time_ms": 15234,
    "requests_per_minute": 12,
    "success_rate_pct": 98.5,
    "error_rate_pct": 1.5
  },
  "agents": {
    "note_parser_avg_time_ms": 8450,
    "lab_mapper_avg_time_ms": 6200,
    "rag_agent_avg_time_ms": 850,
    "chief_agent_avg_time_ms": 95
  },
  "external_services": {
    "gemini_api_latency_ms": 2300,
    "gemini_api_success_rate": 99.2,
    "supabase_latency_ms": 45
  }
}
```

---

## 📚 SDKs & Integration

### Python SDK

```python
from icu_assistant import ICUAssistantClient

client = ICUAssistantClient(
    base_url="http://localhost:8000",
    api_key="optional_api_key"
)

# Assess patient
result = client.assess_patient(patient_data)
print(f"Risk Score: {result.risk_score}/100")

# Get assessment
assessment = client.get_assessment("assessment_id")
```

### JavaScript SDK

```javascript
import { ICUAssistantClient } from 'icu-assistant-js';

const client = new ICUAssistantClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'optional_api_key'
});

// Assess patient
const result = await client.assessPatient(patientData);
console.log(`Risk Level: ${result.riskLevel}`);
```

---

## 🔄 Changelog

### Version 1.0.0 (Current)

- ✅ Complete collaborative agent system
- ✅ Real-time sepsis detection
- ✅ REST API with comprehensive endpoints
- ✅ Production safety features
- ✅ Comprehensive testing suite

### Planned Features (v1.1.0)

- 🔄 WebSocket support for real-time monitoring  
- 🔄 Bulk assessment endpoints
- 🔄 Advanced alert configuration
- 🔄 Integration with EHR systems
- 🔄 Mobile-optimized responses

---

**🎯 Ready to integrate AI-powered sepsis detection into your clinical workflow!**

For questions or support, see the main README or contact the development team.