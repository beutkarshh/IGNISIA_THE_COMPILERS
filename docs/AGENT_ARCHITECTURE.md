# Agent Architecture Documentation

## Overview
The ICU Clinical Assistant uses a **multi-agent pipeline** where each agent specializes in a specific task. Agents work sequentially, each adding information to a shared `PatientState` object.

## System Flow

```
Patient Timeline (Hour 0, 6, 12, 18...)
          ↓
    [Load History]
          ↓
┌─────────────────────────────────────┐
│  PatientState (Shared Memory)       │
│  --------------------------------   │
│  • patient_id                       │
│  • timeline_history                 │
│  • parsed_symptoms          (empty) │
│  • lab_trends              (empty)  │
│  • retrieved_guidelines    (empty)  │
│  • outlier_alerts         (empty)   │
│  • risk_score             (empty)   │
│  • final_report           (empty)   │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Agent 1: Note Parser               │
│  --------------------------------   │
│  INPUT: notes from timeline         │
│  PROCESS: Use Gemini to extract     │
│           symptoms, infection signs │
│  OUTPUT: Add to state:              │
│    - parsed_symptoms                │
│    - infection_signals              │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Agent 2: Temporal Lab Mapper       │
│  --------------------------------   │
│  INPUT: All timeline_history        │
│  PROCESS: Calculate trends          │
│           lactate: [1.3→1.6→2.4→3.8]│
│           trend = "rising_sharply"  │
│  OUTPUT: Add to state:              │
│    - lab_trends                     │
│    - vital_trends                   │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Agent 3: RAG Agent                 │
│  --------------------------------   │
│  INPUT: symptoms + trends           │
│  PROCESS: Query ChromaDB            │
│    "rising lactate + hypotension"   │
│  OUTPUT: Add to state:              │
│    - retrieved_guidelines           │
│    - diagnostic_criteria_met        │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Agent 4: Chief Synthesis Agent     │
│  --------------------------------   │
│  INPUT: All agent outputs           │
│  PROCESS:                           │
│    1. Run outlier detection         │
│    2. Calculate risk score          │
│    3. Generate recommendations      │
│    4. Create final report           │
│  OUTPUT: Add to state:              │
│    - outlier_alerts                 │
│    - risk_flags                     │
│    - risk_score                     │
│    - treatment_recommendations      │
│    - final_report                   │
└─────────────────────────────────────┘
          ↓
    [Return Final State]
```

## Agent Details

### Agent 1: Note Parser
**File**: `agents/note_parser_agent.py`

**Responsibility**: Extract structured information from unstructured clinical notes.

**Example**:
```python
# Input
notes = "Patient reports fever, dyspnea, and confusion. Suspect pneumonia."

# Output added to state
state['parsed_symptoms'] = [
    {"symptom": "fever", "severity": "moderate", "timestamp": "..."},
    {"symptom": "dyspnea", "severity": "moderate", "timestamp": "..."},
    {"symptom": "confusion", "severity": "moderate", "timestamp": "..."}
]
state['infection_signals'] = ["fever", "pneumonia"]
```

**Technology**: Uses Gemini Flash for fast text extraction

---

### Agent 2: Temporal Lab Mapper
**File**: `agents/lab_mapper_agent.py`

**Responsibility**: Detect trends in vitals and lab values over time.

**Example**:
```python
# Input (from timeline_history)
lactate_values = [1.3, 1.6, 2.4, 3.8]
timestamps = ["0hr", "6hr", "12hr", "18hr"]

# Output added to state
state['lab_trends'] = [
    {
        "parameter": "lactate",
        "trend": "rising_sharply",
        "values": [1.3, 1.6, 2.4, 3.8],
        "change_percentage": 192.3  # (3.8-1.3)/1.3 * 100
    }
]
```

**Logic**:
- Rising: Last value > first value by >10%
- Rising sharply: >50% increase
- Uses scipy for statistical analysis

---

### Agent 3: RAG Agent
**File**: `agents/rag_agent.py`

**Responsibility**: Query medical knowledge base for relevant guidelines.

**Example**:
```python
# Input (from previous agents)
query = "rising lactate trend + hypotension + tachycardia"

# ChromaDB retrieval
# Output added to state
state['retrieved_guidelines'] = [
    {
        "guideline_name": "Sepsis-3",
        "section": "2.1",
        "content": "Lactate >2 mmol/L suggests tissue hypoperfusion...",
        "relevance_score": 0.89,
        "citation": "[Sepsis-3, Section 2.1]"
    }
]
state['diagnostic_criteria_met'] = ["SIRS", "qSOFA"]
```

**Technology**: ChromaDB + sentence-transformers embeddings

---

### Agent 4: Chief Synthesis Agent
**File**: `agents/chief_agent.py`

**Responsibility**: Final decision making, outlier detection, risk scoring.

**Example**:
```python
# Input: All previous agent outputs

# Process
1. Run outlier detection on each lab value
   - WBC: [10.2, 10.5, 52.4, 9.9] → Flag 52.4 as outlier
   
2. Calculate risk score (0-100)
   - qSOFA = 2 → +40 points
   - Rising lactate → +30 points
   - SIRS criteria met → +20 points
   - Total: 90/100 = CRITICAL
   
3. Generate recommendations
   - "Initiate sepsis bundle immediately"
   - "Draw blood cultures"
   
4. Create human-readable report with citations

# Output added to state
state['risk_score'] = 90
state['risk_level'] = "CRITICAL"
state['outlier_alerts'] = [...]
state['treatment_recommendations'] = [...]
state['final_report'] = "⚠️ CRITICAL SEPSIS RISK DETECTED..."
```

**Technology**: 
- Statistical outlier detection (scipy)
- Gemini for report generation

---

## LangGraph Workflow
**File**: `agents/workflow.py`

Orchestrates the sequential execution:

```python
from langgraph.graph import StateGraph

workflow = StateGraph(PatientState)

workflow.add_node("note_parser", note_parser_agent)
workflow.add_node("lab_mapper", lab_mapper_agent)
workflow.add_node("rag_agent", rag_agent)
workflow.add_node("chief_agent", chief_agent)

workflow.add_edge("note_parser", "lab_mapper")
workflow.add_edge("lab_mapper", "rag_agent")
workflow.add_edge("rag_agent", "chief_agent")

workflow.set_entry_point("note_parser")
workflow.set_finish_point("chief_agent")

app = workflow.compile()

# Usage
result = app.invoke(initial_state)
```

---

## Why This Architecture?

### ✅ **Separation of Concerns**
Each agent has ONE job → easier to debug and test

### ✅ **Explainability**
Each step is traceable → you can see WHY a decision was made

### ✅ **Parallelization (Future)**
Agents 1 and 2 could run in parallel (both only read input, don't depend on each other)

### ✅ **Modularity**
Easy to add new agents (e.g., "Imaging Analysis Agent") without rewriting existing ones

### ✅ **Safety**
Chief Agent acts as final gatekeeper with outlier detection

---

## Data Flow Example

**Patient 001 at Hour 18**:

```
INPUT:
  timeline_history = [t0, t6, t12, t18]
  current = t18

AGENT 1 (Note Parser):
  notes: "CRITICAL: Patient meets SIRS criteria..."
  → parsed_symptoms: ["altered_mentation", "hypotension"]

AGENT 2 (Lab Mapper):
  lactate: [1.3, 1.6, 2.4, 3.8]
  → lactate_trend: "rising_sharply"

AGENT 3 (RAG):
  query: "rising lactate + SIRS + hypotension"
  → retrieved: [Sepsis-3 guidelines]
  → criteria_met: ["SIRS", "qSOFA"]

AGENT 4 (Chief):
  → risk_score: 90
  → risk_level: "CRITICAL"
  → recommendations: ["Sepsis bundle", "Blood cultures", "Antibiotics"]

OUTPUT:
  final_report: "⚠️ CRITICAL: Early sepsis detected at hour 18..."
```

---

## Next Steps
1. Implement each agent (one by one)
2. Test each agent independently
3. Wire them together in LangGraph
4. End-to-end testing with 3 patient scenarios
