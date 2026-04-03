# MIMIC-III Patient Data Samples

## Overview
This directory contains synthetic patient data based on the MIMIC-III format, designed for the ICU Clinical Assistant demo.

## Patient Samples

### Patient 001 - Early Sepsis Detection ⚠️
**Scenario**: Community-acquired pneumonia progressing to sepsis
- **Timeline**: 24 hours (5 timepoints)
- **Key Features**:
  - Progressive vital sign deterioration
  - Rising lactate (1.3 → 3.8 mmol/L)
  - Increasing WBC (9.2 → 16.2 K/μL)
  - Declining blood pressure
  - qSOFA score reaches 2 at hour 18
- **Expected System Behavior**: Flag sepsis risk at hour 18, recommend sepsis bundle

### Patient 002 - Stable Post-Op Patient ✅
**Scenario**: Elective cholecystectomy with normal recovery
- **Timeline**: 24 hours (4 timepoints)
- **Key Features**:
  - All vitals within normal limits
  - Stable lab values throughout
  - No trends suggesting deterioration
- **Expected System Behavior**: No risk flags, routine monitoring recommendations

### Patient 003 - Lab Error Detection 🔬
**Scenario**: CHF patient with spurious WBC result
- **Timeline**: 26 hours (5 timepoints)
- **Key Features**:
  - WBC spike: 10.2 → **52.4** → 9.9 (middle value is error)
  - Clinical stability despite lab anomaly
  - Confirmed hemolyzed sample
- **Expected System Behavior**: Flag WBC as outlier, refuse to alter diagnosis, recommend redraw

## Data Format

Each patient JSON contains:
```json
{
  "patient_id": "string",
  "admission_id": "string",
  "age": number,
  "gender": "M/F",
  "admission_diagnosis": "string",
  "timeline": [
    {
      "timestamp": "ISO8601",
      "time_label": "human readable",
      "hours_since_admission": number,
      "vitals": { ... },
      "labs": { ... },
      "notes": "clinical narrative"
    }
  ],
  "metadata": {
    "scenario_type": "string",
    "expected_flags": [],
    "teaching_points": "string"
  }
}
```

## Vital Signs Reference Ranges
- **Heart Rate**: 60-100 bpm
- **Blood Pressure**: 90-140 / 60-90 mmHg
- **Respiratory Rate**: 12-20 breaths/min
- **Temperature**: 36.5-37.5 °C
- **SpO2**: >95%

## Lab Values Reference Ranges
- **WBC**: 4.5-11.0 K/μL
- **Lactate**: 0.5-2.0 mmol/L
- **Creatinine**: 0.7-1.3 mg/dL
- **BUN**: 7-20 mg/dL
- **Platelets**: 150-400 K/μL

## Clinical Guidelines Applied
- **SIRS Criteria**: ≥2 of (Temp >38°C or <36°C, HR >90, RR >20, WBC >12K or <4K)
- **qSOFA**: Altered mentation, SBP <100, RR ≥22 (score ≥2 = high sepsis risk)
- **Sepsis-3**: Suspected infection + organ dysfunction (SOFA score increase ≥2)
- **Lactate**: >2.0 mmol/L suggests tissue hypoperfusion

## Usage
```python
import json

# Load patient data
with open('data/mimic_samples/patient_001_sepsis.json') as f:
    patient = json.load(f)

# Access timeline
for timepoint in patient['timeline']:
    print(f"Hour {timepoint['hours_since_admission']}: HR={timepoint['vitals']['heart_rate']}")
```
