"""
PatientState Schema - Shared state between all agents in the ICU diagnostic pipeline.

This TypedDict defines the data structure that flows through the LangGraph workflow.
Each agent reads from and writes to this state.
"""

from typing import TypedDict, List, Dict, Optional, Any


class VitalSigns(TypedDict):
    """Vital signs at a specific timepoint."""
    heart_rate: int  # bpm
    systolic_bp: int  # mmHg
    diastolic_bp: int  # mmHg
    respiratory_rate: int  # breaths/min
    temperature: float  # Celsius
    spo2: int  # Oxygen saturation %


class LabValues(TypedDict):
    """Laboratory values at a specific timepoint."""
    wbc: float  # White blood cell count (K/μL)
    lactate: float  # mmol/L
    creatinine: float  # mg/dL
    bun: int  # Blood urea nitrogen (mg/dL)
    platelets: int  # K/μL


class TimePoint(TypedDict):
    """Single timepoint in patient timeline."""
    timestamp: str  # ISO 8601 format
    time_label: str  # Human-readable (e.g., "Day 1 - 08:00")
    hours_since_admission: int
    vitals: VitalSigns
    labs: LabValues
    notes: str  # Clinical notes


class ParsedSymptom(TypedDict):
    """Structured symptom extracted from clinical notes."""
    symptom: str
    severity: Optional[str]  # "mild", "moderate", "severe"
    timestamp: str


class LabTrend(TypedDict):
    """Trend analysis for a single lab parameter."""
    parameter: str  # e.g., "lactate", "wbc"
    trend: str  # "rising", "falling", "stable", "rising_sharply", "falling_sharply"
    values: List[float]  # Historical values
    timestamps: List[str]
    change_percentage: Optional[float]  # % change from first to last


class GuidelineMatch(TypedDict):
    """Matched clinical guideline from RAG with full citation metadata."""
    guideline_name: str  # e.g., "Sepsis-3"
    guideline_title: str  # Full title: "The Third International Consensus Definitions for Sepsis"
    guideline_year: int  # Publication year (e.g., 2016)
    section: str  # e.g., "2.1"
    content: str  # The actual guideline text
    relevance_score: float  # Similarity score (0-1)
    citation: str  # Formatted citation (APA style)
    pubmed_id: Optional[str]  # PubMed ID if available (e.g., "26903338")
    doi: Optional[str]  # DOI if available (e.g., "10.1001/jama.2016.0287")


class OutlierAlert(TypedDict):
    """Alert for statistically anomalous lab value."""
    parameter: str  # e.g., "wbc"
    value: float  # The outlier value
    timestamp: str
    detection_method: str  # "z_score" or "iqr"
    confidence: float  # 0-1
    historical_values: List[float]
    recommendation: str  # e.g., "Redraw recommended"


class RiskFlag(TypedDict):
    """Risk flag raised by the system."""
    flag_type: str  # e.g., "SIRS_criteria", "qSOFA_score", "rising_lactate"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str
    evidence: List[str]  # Supporting evidence
    timestamp: str


class TreatmentRecommendation(TypedDict):
    """Treatment action recommended by the system."""
    priority: int  # 1 (highest) to 5 (lowest)
    action: str  # e.g., "Initiate sepsis bundle"
    rationale: str
    guideline_source: str  # Citation


class PatientState(TypedDict):
    """
    Complete state for the ICU diagnostic agent pipeline.
    
    This state is passed through all agents in sequence:
    1. Note Parser → adds parsed_symptoms
    2. Lab Mapper → adds lab_trends
    3. RAG Agent → adds retrieved_guidelines
    4. Chief Agent → adds risk_score, outliers, recommendations, final_report
    """
    
    # Input data (populated at start)
    patient_id: str
    admission_id: str
    age: int
    gender: str
    admission_diagnosis: str
    current_timepoint_index: int  # Which step in timeline we're analyzing
    timeline_history: List[TimePoint]  # All timepoints up to current
    
    # Agent 1 output: Note Parser
    parsed_symptoms: List[ParsedSymptom]
    infection_signals: List[str]  # Keywords indicating infection
    
    # Agent 2 output: Temporal Lab Mapper
    lab_trends: List[LabTrend]
    vital_trends: Dict[str, str]  # e.g., {"heart_rate": "increasing"}
    
    # Agent 3 output: RAG Agent
    retrieved_guidelines: List[GuidelineMatch]
    diagnostic_criteria_met: List[str]  # e.g., ["SIRS", "qSOFA"]
    
    # Agent 4 output: Chief Synthesis Agent
    outlier_alerts: List[OutlierAlert]
    risk_flags: List[RiskFlag]
    risk_score: int  # 0-100
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    treatment_recommendations: List[TreatmentRecommendation]
    
    # Final output
    final_report: str  # Human-readable summary with citations
    
    # Metadata
    generated_at: str  # ISO 8601 timestamp
    system_version: str
    processing_time_ms: Optional[int]


# Reference ranges for validation
REFERENCE_RANGES = {
    "vitals": {
        "heart_rate": (60, 100),
        "systolic_bp": (90, 140),
        "diastolic_bp": (60, 90),
        "respiratory_rate": (12, 20),
        "temperature": (36.5, 37.5),
        "spo2": (95, 100)
    },
    "labs": {
        "wbc": (4.5, 11.0),
        "lactate": (0.5, 2.0),
        "creatinine": (0.7, 1.3),
        "bun": (7, 20),
        "platelets": (150, 400)
    }
}

# SIRS criteria thresholds
SIRS_CRITERIA = {
    "temperature_high": 38.0,  # Celsius
    "temperature_low": 36.0,
    "heart_rate": 90,
    "respiratory_rate": 20,
    "wbc_high": 12.0,
    "wbc_low": 4.0
}

# qSOFA criteria
QSOFA_CRITERIA = {
    "systolic_bp": 100,  # Below this
    "respiratory_rate": 22,  # Above this
    # Altered mentation (detected in notes)
}
