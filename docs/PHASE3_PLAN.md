# Phase 3: Refinement & Safety - Implementation Plan

**Goal**: Polish the system for production readiness with safety measures, better error handling, and performance optimization.

**Duration**: 6-8 hours  
**Status**: 🚧 IN PROGRESS

---

## 📋 Phase 3 Tasks

### Task 1: Safety Disclaimers ⚠️
**Priority**: HIGH (Legal/Medical safety)

**What to add**:
- Disclaimer at top of every assessment report
- Warning in API documentation
- Footer in final report output

**Example Disclaimer**:
```
⚠️ CLINICAL DECISION SUPPORT TOOL - NOT A DIAGNOSTIC DEVICE
This system is designed to assist healthcare professionals in clinical 
decision-making and is NOT intended to replace clinical judgment. All 
recommendations must be validated by qualified medical personnel. This 
tool has not been FDA-approved for diagnostic use.
```

**Files to modify**:
- `agents/chief_agent.py` - Add disclaimer to final_report
- `backend/models.py` - Add disclaimer field to response
- `backend/README.md` - Add safety notice

---

### Task 2: Outlier Confidence Scoring 📊
**Priority**: HIGH (Safety/Accuracy)

**Improvements**:
1. Require minimum 3 historical values (currently 2)
2. Add confidence score (0-1) based on:
   - Number of historical values (more = higher confidence)
   - Consistency of historical data (low variance = higher confidence)
   - Magnitude of deviation (extreme = lower confidence)

**Example Output**:
```python
{
    "parameter": "WBC",
    "value": 50.0,
    "outlier_detected": true,
    "confidence": 0.85,  # NEW
    "reason": "Z-score = 4.2 (>3.0 threshold)",
    "historical_count": 5,  # NEW
    "recommendation": "Redraw labs - likely lab error"
}
```

**File to modify**: `utils/outlier_detector.py`

---

### Task 3: Enhanced Citations 📚
**Priority**: MEDIUM (Clinical credibility)

**Current**:
```python
{
    "guideline_source": "[Sepsis-3]"
}
```

**Enhanced**:
```python
{
    "guideline_source": "[Sepsis-3, Section 2.1]",
    "guideline_title": "Definition of Sepsis and Septic Shock",
    "guideline_year": 2016,
    "pubmed_id": "26903338",  # Optional
    "evidence_level": "1A"  # Optional
}
```

**Files to modify**:
- `agents/rag_agent.py` - Enhance guideline matches
- `agents/state.py` - Update GuidelineMatch schema

---

### Task 4: Error Handling & Retry Logic 🔄
**Priority**: HIGH (Reliability)

**Add error handling for**:
1. Gemini API failures (retry 3x with exponential backoff)
2. Firebase connection errors (fall back to memory)
3. Missing patient data (use defaults)
4. Malformed input (validation errors)

**Example**:
```python
@retry(max_attempts=3, backoff=2.0)
def call_gemini_api(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise  # Retry will handle this
```

**Files to modify**:
- `agents/note_parser_agent.py` - Retry on LLM failures
- `backend/firebase_service.py` - Already has fallback ✅
- `backend/workflow.py` - Catch agent errors

---

### Task 5: Performance Optimization 🚀
**Priority**: MEDIUM (User experience)

**Optimizations**:
1. **Cache LLM responses** (same input = same output)
   - Use LRU cache for note parsing
   - TTL: 1 hour
   
2. **Preload embeddings** (ChromaDB - when implemented)
   - Load on startup, not on first query
   
3. **Parallel agent execution** (where possible)
   - Lab Mapper + Note Parser can run in parallel
   - Use asyncio

4. **Database query optimization**
   - Index on patient_id, assessment_id
   - Limit query results

**Expected improvement**: 30-50% faster response times

**Files to modify**:
- `agents/note_parser_agent.py` - Add @lru_cache
- `backend/workflow.py` - Make agents async
- `backend/firebase_service.py` - Add indexes

---

### Task 6: Structured Logging 📝
**Priority**: MEDIUM (Debugging/Monitoring)

**Add logging for**:
- API request/response times
- Agent execution times
- LLM token usage
- Database query performance
- Error stack traces

**Example Log Output**:
```json
{
    "timestamp": "2026-04-03T14:00:00Z",
    "level": "INFO",
    "event": "assessment_completed",
    "patient_id": "001",
    "assessment_id": "abc-123",
    "execution_time_ms": 4521,
    "agent_timings": {
        "note_parser": 1200,
        "lab_mapper": 850,
        "rag_agent": 1100,
        "chief_agent": 1371
    },
    "risk_score": 90,
    "llm_tokens_used": 2450
}
```

**Files to create/modify**:
- `utils/logger.py` - NEW: Structured logger
- `backend/workflow.py` - Add timing instrumentation
- `backend/main.py` - Log API requests

---

## 🎯 Success Criteria

Phase 3 is complete when:
- ✅ Every assessment has a safety disclaimer
- ✅ Outlier detection has confidence scores (0-1)
- ✅ Outlier detection requires ≥3 historical values
- ✅ Citations include section references
- ✅ API calls have retry logic (3 attempts)
- ✅ LLM responses are cached (LRU)
- ✅ Structured logging captures all events
- ✅ No unhandled exceptions in normal operation

---

## 📊 Implementation Order

**Recommended sequence** (most critical first):

1. **Safety Disclaimers** (30 min) - Legal requirement
2. **Error Handling** (1.5 hours) - Prevent crashes
3. **Outlier Confidence** (1 hour) - Improve accuracy
4. **Structured Logging** (1.5 hours) - Enable debugging
5. **Enhanced Citations** (1 hour) - Clinical credibility
6. **Performance Optimization** (2 hours) - User experience

**Total**: ~7.5 hours

---

## 🚀 Let's Start!

**First task**: Safety Disclaimers

Ready to begin? I'll implement each task and test as we go.
