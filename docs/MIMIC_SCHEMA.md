# MIMIC-III Database Schema and Key Relationships

## 🔑 Primary Keys in MIMIC-III

### Core Tables and Keys:

1. **patients** - Patient demographics
   - Primary Key: `subject_id` (unique patient identifier)
   - Fields: gender, dob, dod (date of death)

2. **admissions** - Hospital admissions
   - Primary Key: `hadm_id` (hospital admission ID)
   - Foreign Key: `subject_id` → patients
   - Fields: admittime, dischtime, diagnosis, admission_type

3. **icustays** - ICU stays
   - Primary Key: `icustay_id` (ICU stay identifier)
   - Foreign Keys: 
     - `subject_id` → patients
     - `hadm_id` → admissions
   - Fields: intime, outtime, first_careunit

4. **chartevents** - Vital signs and monitoring
   - Foreign Keys:
     - `subject_id` → patients
     - `hadm_id` → admissions
     - `icustay_id` → icustays
   - Fields: charttime, itemid, valuenum

5. **labevents** - Laboratory results
   - Foreign Keys:
     - `subject_id` → patients
     - `hadm_id` → admissions
   - Fields: charttime, itemid, valuenum

## 🔗 Key Relationships

```
patient (subject_id)
    ↓
    ├─→ admissions (hadm_id)
    │       ↓
    │       ├─→ icustays (icustay_id)
    │       │       ↓
    │       │       └─→ chartevents (vitals)
    │       │
    │       └─→ labevents (labs)
    │
    └─→ multiple admissions possible
```

## 📋 ID Mapping for Our Agent System

### MIMIC-III → Agent Format

| MIMIC Field | Agent Field | Description |
|-------------|-------------|-------------|
| `subject_id` | `patient_id` | **Primary identifier** - This is THE patient |
| `hadm_id` | `admission_id` | Hospital admission identifier |
| `icustay_id` | `icu_stay_id` | ICU stay identifier (optional) |

### Key Rules:

1. **One subject_id = One patient**
   - `subject_id` uniquely identifies a person
   - Multiple admissions can exist for same `subject_id`

2. **One hadm_id = One hospital admission**
   - `hadm_id` tracks a single hospital stay
   - Multiple ICU stays can exist within one admission

3. **One icustay_id = One ICU stay**
   - `icustay_id` tracks time in ICU
   - Used to query chartevents (vitals)

## 🎯 Agent Data Flow

### Correct Workflow:

```python
# 1. Search by diagnosis → get subject_id list
GET /mimic/patients?diagnosis=SEPSIS
→ Returns: [{"subject_id": 10006, "hadm_id": 142345, ...}]

# 2. Get patient data by subject_id
GET /mimic/patients/10006  # subject_id
→ Returns: Patient with ALL data mapped to agent format
→ patient_id = "10006" (string version of subject_id)

# 3. Assess patient
POST /mimic/patients/10006/assess
→ Uses subject_id to fetch complete patient timeline
→ Returns: Assessment results
```

## 🚫 What We're Avoiding

### ❌ Don't Do This:
- Using `row_id` as patient identifier (internal DB index)
- Mixing `subject_id` with `hadm_id` as patient ID
- Creating synthetic patient IDs like "P001"

### ✅ Do This:
- Always use `subject_id` as the patient identifier
- Convert `subject_id` → `patient_id` (string) for API
- Maintain FK relationships when querying related data

## 📊 Example Query Pattern

### Fetch Complete Patient Data:

```sql
-- 1. Get patient demographics
SELECT * FROM patients WHERE subject_id = 10006;

-- 2. Get most recent admission
SELECT * FROM admissions 
WHERE subject_id = 10006 
ORDER BY admittime DESC 
LIMIT 1;

-- 3. Get ICU stay for that admission
SELECT * FROM icustays 
WHERE subject_id = 10006 AND hadm_id = 142345
LIMIT 1;

-- 4. Get vitals from ICU stay
SELECT * FROM chartevents 
WHERE icustay_id = 200001 
AND itemid IN (211, 220045, ...) -- Heart rate
ORDER BY charttime;

-- 5. Get labs from admission
SELECT * FROM labevents 
WHERE hadm_id = 142345
AND itemid IN (51300, 50813, ...) -- WBC, Lactate
ORDER BY charttime;
```

## 🔧 Implementation Requirements

### 1. API Endpoints Must:
- Accept `subject_id` as path parameter
- Return `patient_id` (stringified subject_id) in responses
- Preserve MIMIC-III FK relationships

### 2. Data Adapter Must:
- Query by `subject_id` (primary key)
- Join tables using proper FKs (subject_id, hadm_id, icustay_id)
- Convert MIMIC format → Agent format consistently

### 3. Agents Must:
- Receive data with `patient_id` field
- Never see internal `row_id` or other DB indices
- Work with standardized timeline format

## 📝 Data Validation Checklist

Before sending data to agents:
- ✅ `patient_id` = string version of `subject_id`
- ✅ `admission_id` = string version of `hadm_id`
- ✅ All vitals linked to correct `icustay_id`
- ✅ All labs linked to correct `hadm_id`
- ✅ Timeline sorted chronologically
- ✅ No missing FK references

## 🎯 Current Status

### What's Working:
- ✅ Search patients by diagnosis (returns subject_id)
- ✅ Get patient by subject_id (returns demographics)

### What Needs Fixing:
- ⚠️ Timeline generation from chartevents/labevents
- ⚠️ Proper date/time parsing and grouping
- ⚠️ Age calculation from DOB
- ⚠️ Complete vital signs extraction

### Next Steps:
1. Enhance `convert_to_agent_format()` to build full timeline
2. Group chartevents by time windows (e.g., hourly)
3. Map MIMIC itemids to our vital/lab names
4. Validate all FK relationships
5. Test with multiple patients

---

## 📖 References

- MIMIC-III Documentation: https://mimic.mit.edu/docs/iii/
- MIMIC-III Tables: https://mimic.mit.edu/docs/iii/tables/
- D_ITEMS (itemid mappings): https://mimic.mit.edu/docs/iii/tables/d_items/
