"""
Agent 1: Note Parser - COLLABORATIVE INTELLIGENT VERSION

An intelligent agent that:
- Plans its extraction strategy
- Reasons through findings with chain-of-thought
- Uses tools to validate extractions
- Writes insights to shared memory
- Self-critiques and refines results
- Communicates with other agents

Capabilities: Collection, Planning, Reasoning, Tools, Memory

Performance optimizations:
- LRU caching for repeated note patterns
"""

import os
import json
import hashlib
from functools import lru_cache
from typing import Dict, List, Any, Optional
from datetime import datetime
from agents.state import PatientState, ParsedSymptom, REFERENCE_RANGES
from agents.tools import TOOL_REGISTRY, lookup_symptom_severity, validate_vital_signs
from agents.memory import AGENT_MEMORY
from agents.reasoning import ChainOfThought, SelfCritique, ReasoningEngine, validate_clinical_plausibility
from utils.retry import retry

try:
    import google.generativeai as genai
except Exception:
    genai = None


# Initialize Gemini with timeout configuration
if genai is not None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    # Configure with timeout (60 seconds) to prevent hanging
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        generation_config={
            'temperature': 0.7,
            'top_p': 0.9,
            'max_output_tokens': 2048,
        },
        # Note: Timeout is handled at request level in generate_content calls
    )
    reasoning_engine = ReasoningEngine(model)
else:
    class _FallbackModel:
        def generate_content(self, prompt):
            raise RuntimeError("Gemini SDK unavailable")
    
    model = _FallbackModel()
    reasoning_engine = ReasoningEngine(None)


def _create_extraction_plan(notes_text: str, context: Dict) -> Dict[str, Any]:
    """
    PLANNING PHASE: Create a strategy for extracting information.
    
    Args:
        notes_text: Combined clinical notes
        context: Patient context (vitals, labs)
        
    Returns:
        Extraction plan
    """
    # Analyze what types of information are likely present
    plan = {
        'strategy': 'comprehensive',
        'focus_areas': [],
        'validation_needed': [],
        'expected_findings': []
    }
    
    # Determine focus areas based on context
    if context.get('admission_diagnosis'):
        diagnosis = context['admission_diagnosis'].lower()
        if 'pneumonia' in diagnosis or 'infection' in diagnosis:
            plan['focus_areas'].append('infection_signals')
            plan['expected_findings'].append('respiratory_symptoms')
        if 'sepsis' in diagnosis:
            plan['focus_areas'].append('sepsis_indicators')
            plan['validation_needed'].append('vital_support')
    
    # Check vitals to guide extraction
    current_vitals = context.get('current_vitals', {})
    if current_vitals.get('temperature', 37) > 38:
        plan['expected_findings'].append('fever_mention')
    if current_vitals.get('systolic_bp', 120) < 100:
        plan['expected_findings'].append('hypotension_mention')
    
    AGENT_MEMORY.log_agent_action('note_parser', 'create_plan', plan)
    
    return plan


@lru_cache(maxsize=128)
def _cached_note_hash(notes_text: str, focus_areas: str) -> str:
    """Generate hash for caching note parsing results."""
    content = f"{notes_text}|{focus_areas}"
    return hashlib.md5(content.encode()).hexdigest()


# Cache for parsed notes (in-memory, session-level)
_PARSE_CACHE: Dict[str, Dict[str, Any]] = {}


@retry(max_attempts=3, backoff=2.0, exceptions=(Exception,))
def _call_gemini_with_retry(prompt: str) -> str:
    """Call Gemini API with retry logic."""
    if genai is None or model is None:
        return "{}"  # Fallback to empty response
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        raise  # Retry decorator will handle this


def _extract_with_reasoning(notes_text: str, plan: Dict) -> Dict[str, Any]:
    """
    REASONING PHASE: Extract information using chain-of-thought.
    Uses LRU cache for repeated note patterns.
    
    Args:
        notes_text: Clinical notes
        plan: Extraction plan
        
    Returns:
        Extracted data with reasoning
    """
    # Check cache first
    focus_str = ','.join(sorted(plan.get('focus_areas', ['general'])))
    cache_key = _cached_note_hash(notes_text[:500], focus_str)  # Use first 500 chars for hash
    
    if cache_key in _PARSE_CACHE:
        print(f"[CACHE HIT] Returning cached parse result")
        return _PARSE_CACHE[cache_key]
    
    # Create context-aware prompt
    prompt = f"""You are a medical AI assistant analyzing ICU patient notes.

EXTRACTION PLAN:
- Focus areas: {', '.join(plan.get('focus_areas', ['general']))}
- Expected findings: {', '.join(plan.get('expected_findings', ['symptoms']))}

Patient Notes:
{notes_text}

Use step-by-step reasoning to extract information:

STEP 1: IDENTIFY
- What symptoms are explicitly mentioned?
- What infection signals are present?
- What clinical events are described?

STEP 2: CLASSIFY
- Severity of each symptom (mild/moderate/severe)
- Time context for each finding
- Confidence in each extraction (0-1)

STEP 3: VALIDATE
- Do the extracted items make clinical sense together?
- Are there any contradictions in the notes?
- What might be implied but not stated?

STEP 4: STRUCTURE
Format response as JSON:
{{
  "symptoms": [
    {{"symptom": "...", "severity": "...", "timestamp": "...", "confidence": 0.0-1.0}}
  ],
  "infection_signals": ["..."],
  "clinical_events": ["..."],
  "inconsistencies": ["..."],
  "reasoning": "Brief explanation of extraction logic"
}}

Only include explicitly mentioned items. Mark low confidence (<0.7) for ambiguous findings."""

    try:
        # Use retry wrapper
        result_text = _call_gemini_with_retry(prompt)
        
        # Parse JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        extracted = json.loads(result_text)
        
        # Store in cache
        _PARSE_CACHE[cache_key] = extracted
        
        # Limit cache size
        if len(_PARSE_CACHE) > 128:
            # Remove oldest entry (FIFO)
            _PARSE_CACHE.pop(next(iter(_PARSE_CACHE)))
        
        return extracted
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return {
            'symptoms': [],
            'infection_signals': [],
            'clinical_events': [],
            'reasoning': f'Error: {str(e)}'
        }


def _validate_with_tools(extracted: Dict, patient_context: Dict) -> Dict[str, Any]:
    """
    TOOL USE PHASE: Validate extractions using clinical tools.
    
    Args:
        extracted: Extracted data
        patient_context: Patient vitals and labs
        
    Returns:
        Validation results
    """
    validation_results = {
        'symptom_validations': [],
        'plausibility_checks': [],
        'vital_support': [],
        'issues_found': []
    }
    
    # Validate symptom severity against vitals
    for symptom_data in extracted.get('symptoms', []):
        symptom = symptom_data.get('symptom', '')
        severity = symptom_data.get('severity', 'moderate')
        
        # Use tool to check severity
        severity_check = lookup_symptom_severity(symptom, patient_context)
        
        validation_results['symptom_validations'].append({
            'symptom': symptom,
            'claimed_severity': severity,
            'tool_severity': severity_check.get('severity', 'unknown'),
            'match': severity_check.get('severity') == severity
        })
    
    # Validate infection signals against vitals
    if extracted.get('infection_signals'):
        vital_alerts = validate_vital_signs(
            patient_context.get('current_vitals', {}),
            REFERENCE_RANGES
        )
        validation_results['vital_support'] = vital_alerts
        
        # Check plausibility
        plausibility = validate_clinical_plausibility(
            {'type': 'infection', 'signals': extracted['infection_signals']},
            patient_context
        )
        validation_results['plausibility_checks'].append(plausibility)
    
    return validation_results


def _self_critique_and_refine(extracted: Dict, notes_text: str, 
                              validation: Dict) -> Dict[str, Any]:
    """
    SELF-CRITIQUE PHASE: Agent critiques its own extraction.
    
    Args:
        extracted: Initial extraction
        notes_text: Original notes
        validation: Validation results
        
    Returns:
        Refined extraction
    """
    # Build critique prompt
    critique_prompt = SelfCritique.critique_extraction(extracted, notes_text)
    
    try:
        response = model.generate_content(critique_prompt)
        result_text = response.text.strip()
        
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        
        critique = json.loads(result_text)
        
        # If critique suggests issues, refine
        if critique.get('issues_found'):
            # Log issues to memory
            for issue in critique['issues_found']:
                AGENT_MEMORY.shared_context.write_flag(
                    'note_parser',
                    'extraction_issue',
                    issue,
                    severity='medium'
                )
        
        # Apply suggested corrections
        refined = extracted.copy()
        for correction in critique.get('suggested_corrections', []):
            # Apply corrections (simplified - would be more sophisticated)
            pass
        
        # Update confidence based on critique
        final_confidence = critique.get('confidence_in_extraction', 0.8)
        
        return {
            'extracted': refined,
            'critique': critique,
            'confidence': final_confidence,
            'issues': critique.get('issues_found', [])
        }
        
    except Exception as e:
        # Fallback: return original with warning
        return {
            'extracted': extracted,
            'critique': {'error': str(e)},
            'confidence': 0.7,
            'issues': ['Critique failed']
        }


def _write_to_shared_memory(extracted: Dict, validation: Dict, 
                           critique_result: Dict, patient_id: str):
    """
    MEMORY PHASE: Write findings to shared memory for other agents.
    
    Args:
        extracted: Extracted data
        validation: Validation results
        critique_result: Critique results
        patient_id: Patient identifier
    """
    # Write insights
    for symptom_data in extracted.get('symptoms', []):
        AGENT_MEMORY.shared_context.write_insight(
            'note_parser',
            f"Found symptom: {symptom_data['symptom']} (severity: {symptom_data.get('severity', 'unknown')})",
            category='symptom',
            confidence=symptom_data.get('confidence', 0.8)
        )
    
    if extracted.get('infection_signals'):
        AGENT_MEMORY.shared_context.write_insight(
            'note_parser',
            f"Infection signals detected: {', '.join(extracted['infection_signals'])}",
            category='infection',
            confidence=critique_result.get('confidence', 0.8),
            evidence=extracted['infection_signals']
        )
    
    # Write structured findings
    AGENT_MEMORY.shared_context.write_finding(
        'note_parser',
        'symptoms',
        {
            'symptoms': extracted.get('symptoms', []),
            'infection_signals': extracted.get('infection_signals', []),
            'confidence': critique_result.get('confidence', 0.8)
        }
    )
    
    # Register in findings registry
    AGENT_MEMORY.findings_registry.register_finding(
        'note_parser',
        f'note-parse-{patient_id}',
        'clinical_extraction',
        extracted,
        confidence=critique_result.get('confidence', 0.8)
    )
    
    # Log any inconsistencies found
    if extracted.get('inconsistencies'):
        for inconsistency in extracted['inconsistencies']:
            AGENT_MEMORY.shared_context.write_flag(
                'note_parser',
                'inconsistency',
                inconsistency,
                severity='medium',
                actionable=True
            )


def note_parser_agent(state: PatientState) -> PatientState:
    """
    COLLABORATIVE NOTE PARSER AGENT
    
    Intelligently extracts information from clinical notes using:
    - Planning: Creates extraction strategy
    - Reasoning: Chain-of-thought extraction
    - Tools: Validates findings
    - Memory: Shares insights with other agents
    - Self-critique: Refines results
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with parsed_symptoms and infection_signals
    """
    agent_name = 'note_parser'
    AGENT_MEMORY.log_agent_action(agent_name, 'start', {'patient_id': state['patient_id']})
    
    # Collect all notes from timeline history
    all_notes = []
    for timepoint in state['timeline_history']:
        all_notes.append({
            'timestamp': timepoint['timestamp'],
            'time_label': timepoint['time_label'],
            'notes': timepoint['notes']
        })
    
    notes_text = "\n\n".join([
        f"[{n['time_label']}]: {n['notes']}" 
        for n in all_notes
    ])
    
    # Prepare patient context for tools
    current_timepoint = state['timeline_history'][-1] if state['timeline_history'] else {}
    patient_context = {
        'current_vitals': current_timepoint.get('vitals', {}),
        'current_labs': current_timepoint.get('labs', {}),
        'admission_diagnosis': state.get('admission_diagnosis', ''),
        'age': state.get('age'),
        'gender': state.get('gender')
    }
    
    # PHASE 1: PLANNING
    print(f"[{agent_name}] Creating extraction plan...")
    extraction_plan = _create_extraction_plan(notes_text, patient_context)
    
    # PHASE 2: REASONING (Extraction with CoT)
    print(f"[{agent_name}] Extracting with reasoning...")
    extracted = _extract_with_reasoning(notes_text, extraction_plan)
    
    # PHASE 3: TOOL USE (Validation)
    print(f"[{agent_name}] Validating with tools...")
    validation = _validate_with_tools(extracted, patient_context)
    
    # PHASE 4: SELF-CRITIQUE
    print(f"[{agent_name}] Self-critiquing extraction...")
    critique_result = _self_critique_and_refine(extracted, notes_text, validation)
    
    # PHASE 5: MEMORY (Write to shared context)
    print(f"[{agent_name}] Writing to shared memory...")
    _write_to_shared_memory(
        critique_result['extracted'],
        validation,
        critique_result,
        state['patient_id']
    )
    
    # Update state with final refined results
    final_extraction = critique_result['extracted']
    state['parsed_symptoms'] = final_extraction.get('symptoms', [])
    state['infection_signals'] = final_extraction.get('infection_signals', [])
    
    # Add metadata about the agent's work
    AGENT_MEMORY.log_agent_action(
        agent_name,
        'complete',
        {
            'symptoms_found': len(state['parsed_symptoms']),
            'infection_signals': len(state['infection_signals']),
            'confidence': critique_result.get('confidence', 0.8),
            'issues': len(critique_result.get('issues', []))
        }
    )
    
    print(f"[{agent_name}] Complete! Found {len(state['parsed_symptoms'])} symptoms, "
          f"{len(state['infection_signals'])} infection signals "
          f"(confidence: {critique_result.get('confidence', 0.8):.2f})")
    
    return state
