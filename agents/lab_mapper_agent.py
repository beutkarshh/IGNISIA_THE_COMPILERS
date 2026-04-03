"""
Agent 2: Temporal Lab Mapper - COLLABORATIVE INTELLIGENT VERSION

An intelligent agent that:
- Plans which trends are clinically significant
- Reasons through trend patterns with LLM
- Uses statistical tools for validation
- Reads insights from Note Parser (COLLABORATION!)
- Writes findings to shared memory
- Self-critiques trend interpretations

Capabilities: Collection, Planning, Reasoning, Tools, Memory
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from agents.state import PatientState, LabTrend, REFERENCE_RANGES
from agents.tools import (TOOL_REGISTRY, calculate_trend_statistics, 
                          detect_pattern_anomaly, validate_lab_value, create_agent_query)
from agents.memory import AGENT_MEMORY
from agents.reasoning import ChainOfThought, validate_trend_direction, generate_confidence_score

try:
    import google.generativeai as genai
except Exception:
    genai = None


# Initialize Gemini
if genai is not None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None


def _calculate_basic_trend(values: List[float]) -> str:
    """
    Basic trend calculation (kept for fallback).
    
    Args:
        values: List of values in chronological order
        
    Returns:
        Trend description
    """
    if len(values) < 2:
        return "insufficient_data"
    
    first = values[0]
    last = values[-1]
    
    if first == 0:
        return "stable"
    
    change_pct = ((last - first) / first) * 100
    
    if abs(change_pct) < 5:
        return "stable"
    elif change_pct > 50:
        return "rising_sharply"
    elif change_pct > 10:
        return "rising"
    elif change_pct < -50:
        return "falling_sharply"
    elif change_pct < -10:
        return "falling"
    else:
        return "stable"


def _collect_context_from_note_parser() -> Dict[str, Any]:
    """
    COLLECTION PHASE: Read what Note Parser discovered.
    This is AGENT-TO-AGENT COLLABORATION!
    
    Returns:
        Context from Note Parser's findings
    """
    context = {
        'symptoms': [],
        'infection_signals': [],
        'flags': []
    }
    
    # Read insights from Note Parser
    note_parser_insights = AGENT_MEMORY.shared_context.read_insights(agent='note_parser')
    
    for insight in note_parser_insights:
        if insight['category'] == 'symptom':
            context['symptoms'].append(insight['insight'])
        elif insight['category'] == 'infection':
            context['infection_signals'].append(insight['insight'])
    
    # Read flags from Note Parser
    flags = AGENT_MEMORY.shared_context.read_flags()
    context['flags'] = [f['message'] for f in flags if f.get('agent') == 'note_parser']
    
    if note_parser_insights:
        print(f"[lab_mapper] Collected {len(note_parser_insights)} insights from Note Parser")
    
    return context


def _create_analysis_plan(timeline: List[Dict], note_parser_context: Dict) -> Dict[str, Any]:
    """
    PLANNING PHASE: Decide which trends to focus on based on clinical context.
    
    Args:
        timeline: Patient timeline
        note_parser_context: What Note Parser found
        
    Returns:
        Analysis plan
    """
    plan = {
        'priority_parameters': [],
        'focus_areas': [],
        'expected_correlations': [],
        'validation_needed': []
    }
    
    # If Note Parser found infection signals, prioritize inflammatory markers
    if any('infection' in sig.lower() for sig in note_parser_context.get('infection_signals', [])):
        plan['priority_parameters'].extend(['wbc', 'lactate'])
        plan['focus_areas'].append('infection_markers')
        plan['expected_correlations'].append('WBC and lactate should correlate with infection')
    
    # If fever mentioned, prioritize temperature and inflammatory markers
    if any('fever' in sym.lower() for sym in note_parser_context.get('symptoms', [])):
        plan['priority_parameters'].append('wbc')
        plan['expected_correlations'].append('WBC should be elevated with fever')
    
    # If hypotension mentioned, check renal function
    if any('hypotension' in sym.lower() or 'blood pressure' in sym.lower() 
           for sym in note_parser_context.get('symptoms', [])):
        plan['priority_parameters'].extend(['creatinine', 'bun'])
        plan['focus_areas'].append('renal_function')
        plan['expected_correlations'].append('Hypotension may affect renal perfusion')
    
    # Always validate sharp changes
    plan['validation_needed'].append('statistical_analysis_for_outliers')
    
    AGENT_MEMORY.log_agent_action('lab_mapper', 'create_plan', plan)
    
    return plan


def _analyze_trends_with_reasoning(lab_trends: List[Dict], vital_trends: Dict,
                                   note_parser_context: Dict, plan: Dict) -> Dict[str, Any]:
    """
    REASONING PHASE: Use LLM to interpret trends clinically.
    
    Args:
        lab_trends: Detected lab trends
        vital_trends: Detected vital trends
        note_parser_context: Note Parser findings
        plan: Analysis plan
        
    Returns:
        Clinical interpretation of trends
    """
    if not model:
        return {'interpretation': 'LLM not available', 'confidence': 0.5}
    
    # Build context for reasoning
    context_summary = {
        'lab_trends': [{
            'parameter': t['parameter'],
            'trend': t['trend'],
            'change': f"{t['values'][0]} → {t['values'][-1]} ({t['change_percentage']:+.1f}%)"
        } for t in lab_trends],
        'vital_trends': vital_trends,
        'note_parser_findings': note_parser_context,
        'priority_parameters': plan.get('priority_parameters', [])
    }
    
    # Use chain-of-thought reasoning
    prompt = f"""You are analyzing ICU patient lab and vital trends. Use step-by-step reasoning.

CONTEXT FROM NOTE PARSER:
{json.dumps(note_parser_context, indent=2)}

LAB TRENDS DETECTED:
{json.dumps(context_summary['lab_trends'], indent=2)}

VITAL TRENDS:
{json.dumps(vital_trends, indent=2)}

PRIORITY PARAMETERS: {', '.join(plan.get('priority_parameters', []))}

Reason through this step-by-step:

STEP 1: CORRELATION
- Do the lab trends correlate with symptoms from Note Parser?
- Do vitals support the lab findings?
- Are there expected correlations present or missing?

STEP 2: CLINICAL SIGNIFICANCE
- Which trends are most clinically significant?
- What do these patterns suggest about patient condition?
- Are there concerning combinations?

STEP 3: VALIDATION
- Do these trends make physiological sense?
- Are there any suspicious or unexpected patterns?
- Should any values be rechecked?

STEP 4: SYNTHESIS
- What is the overall clinical picture from these trends?
- How confident are you in this interpretation (0-1)?
- What should other agents know about these findings?

Respond in JSON:
{{
  "correlations_found": [...],
  "clinical_significance": "...",
  "concerning_patterns": [...],
  "validation_needed": [...],
  "overall_interpretation": "...",
  "confidence": 0.0-1.0,
  "key_insights_for_agents": [...]
}}"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(result_text)
        return analysis
        
    except Exception as e:
        print(f"[lab_mapper] Reasoning error: {e}")
        return {
            'interpretation': 'Reasoning failed',
            'confidence': 0.5,
            'error': str(e)
        }


def _validate_with_statistical_tools(lab_trends: List[Dict]) -> Dict[str, Any]:
    """
    TOOL USE PHASE: Validate trends using statistical tools.
    
    Args:
        lab_trends: Detected trends
        
    Returns:
        Validation results
    """
    validations = []
    
    for trend in lab_trends:
        param = trend['parameter']
        values = trend['values']
        trend_direction = trend['trend']
        
        # Use statistical analysis tool
        stats = calculate_trend_statistics(values)
        
        # Validate trend direction matches statistics
        direction_valid = validate_trend_direction(values, trend_direction)
        
        # Check for anomalies in latest value
        if len(values) >= 3:
            anomaly_check = detect_pattern_anomaly(values[:-1], values[-1])
        else:
            anomaly_check = {'anomaly': False}
        
        # Validate against reference ranges
        current_value = values[-1]
        range_check = validate_lab_value(param, current_value, REFERENCE_RANGES)
        
        validations.append({
            'parameter': param,
            'statistics': stats,
            'direction_valid': direction_valid,
            'anomaly': anomaly_check.get('anomaly', False),
            'range_check': range_check,
            'confidence': 1.0 if direction_valid and not anomaly_check.get('anomaly') else 0.7
        })
    
    return {'validations': validations}


def _communicate_with_note_parser(findings: Dict) -> Optional[str]:
    """
    COLLABORATION: Send query to Note Parser if needed.
    
    Args:
        findings: Current findings
        
    Returns:
        Message ID if sent
    """
    # If we found infection markers but Note Parser didn't mention infection
    if findings.get('infection_markers_elevated'):
        # Send query to Note Parser
        message = create_agent_query(
            'lab_mapper',
            'note_parser',
            'Lab trends show elevated infection markers (WBC, lactate). Did you find any infection-related keywords in notes?'
        )
        
        msg_id = AGENT_MEMORY.message_bus.send_message(
            'lab_mapper',
            'note_parser',
            'query',
            message.content,
            priority=1
        )
        
        print(f"[lab_mapper] Sent query to Note Parser: {msg_id}")
        return msg_id
    
    return None


def _write_to_shared_memory(lab_trends: List[Dict], vital_trends: Dict,
                            reasoning_result: Dict, validation: Dict,
                            patient_id: str):
    """
    MEMORY PHASE: Share findings with other agents.
    
    Args:
        lab_trends: Lab trends
        vital_trends: Vital trends
        reasoning_result: Reasoning output
        validation: Validation results
        patient_id: Patient ID
    """
    # Write insights for significant trends
    for trend in lab_trends:
        if trend['trend'] in ['rising_sharply', 'falling_sharply']:
            significance = reasoning_result.get('clinical_significance', 'Not analyzed')
            
            AGENT_MEMORY.shared_context.write_insight(
                'lab_mapper',
                f"{trend['parameter']} is {trend['trend']}: {trend['values'][0]} → {trend['values'][-1]} ({trend['change_percentage']:+.1f}%). {significance}",
                category='lab_trend',
                confidence=reasoning_result.get('confidence', 0.8),
                evidence=[trend]
            )
    
    # Write overall interpretation
    if reasoning_result.get('overall_interpretation'):
        AGENT_MEMORY.shared_context.write_insight(
            'lab_mapper',
            reasoning_result['overall_interpretation'],
            category='clinical_synthesis',
            confidence=reasoning_result.get('confidence', 0.8)
        )
    
    # Write concerning patterns as flags
    for pattern in reasoning_result.get('concerning_patterns', []):
        AGENT_MEMORY.shared_context.write_flag(
            'lab_mapper',
            'concerning_trend',
            pattern,
            severity='high',
            actionable=True
        )
    
    # Write structured findings
    AGENT_MEMORY.shared_context.write_finding(
        'lab_mapper',
        'trend_analysis',
        {
            'lab_trends': lab_trends,
            'vital_trends': vital_trends,
            'interpretation': reasoning_result.get('overall_interpretation'),
            'confidence': reasoning_result.get('confidence', 0.8)
        }
    )
    
    # Register in findings registry
    AGENT_MEMORY.findings_registry.register_finding(
        'lab_mapper',
        f'trend-analysis-{patient_id}',
        'temporal_trends',
        {
            'lab_trends': lab_trends,
            'vital_trends': vital_trends,
            'analysis': reasoning_result
        },
        confidence=reasoning_result.get('confidence', 0.8)
    )


def lab_mapper_agent(state: PatientState) -> PatientState:
    """
    COLLABORATIVE LAB MAPPER AGENT
    
    Intelligently analyzes lab and vital trends using:
    - Collection: Reads Note Parser's findings
    - Planning: Prioritizes analysis based on clinical context
    - Reasoning: LLM interprets trends clinically
    - Tools: Statistical validation
    - Memory: Shares insights with other agents
    - Communication: Queries Note Parser when needed
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with lab_trends and vital_trends
    """
    agent_name = 'lab_mapper'
    AGENT_MEMORY.log_agent_action(agent_name, 'start', {'patient_id': state['patient_id']})
    
    timeline = state['timeline_history']
    
    if len(timeline) < 2:
        state['lab_trends'] = []
        state['vital_trends'] = {}
        return state
    
    # PHASE 1: COLLECTION - Read Note Parser's findings
    print(f"[{agent_name}] Collecting context from Note Parser...")
    note_parser_context = _collect_context_from_note_parser()
    
    # PHASE 2: PLANNING - Create analysis strategy
    print(f"[{agent_name}] Creating analysis plan...")
    analysis_plan = _create_analysis_plan(timeline, note_parser_context)
    
    # PHASE 3: BASIC TREND DETECTION (using original logic)
    print(f"[{agent_name}] Detecting trends...")
    lab_params = ['wbc', 'lactate', 'creatinine', 'bun', 'platelets']
    vital_params = ['heart_rate', 'systolic_bp', 'respiratory_rate', 'temperature', 'spo2']
    
    lab_trends = []
    vital_trends = {}
    
    # Analyze lab trends
    for param in lab_params:
        values = []
        timestamps = []
        
        for tp in timeline:
            if param in tp.get('labs', {}):
                values.append(tp['labs'][param])
                timestamps.append(tp['timestamp'])
        
        if len(values) >= 2:
            trend = _calculate_basic_trend(values)
            change_pct = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            
            lab_trends.append({
                "parameter": param,
                "trend": trend,
                "values": values,
                "timestamps": timestamps,
                "change_percentage": round(change_pct, 1)
            })
    
    # Analyze vital trends
    for param in vital_params:
        values = []
        
        for tp in timeline:
            if param in tp.get('vitals', {}):
                values.append(tp['vitals'][param])
        
        if len(values) >= 2:
            trend = _calculate_basic_trend(values)
            vital_trends[param] = trend
    
    # PHASE 4: REASONING - Clinical interpretation with LLM
    print(f"[{agent_name}] Reasoning through clinical significance...")
    reasoning_result = _analyze_trends_with_reasoning(
        lab_trends,
        vital_trends,
        note_parser_context,
        analysis_plan
    )
    
    # PHASE 5: TOOL USE - Statistical validation
    print(f"[{agent_name}] Validating with statistical tools...")
    validation = _validate_with_statistical_tools(lab_trends)
    
    # PHASE 6: COMMUNICATION - Query Note Parser if needed
    infection_markers_elevated = any(
        t['parameter'] in ['wbc', 'lactate'] and t['trend'] in ['rising', 'rising_sharply']
        for t in lab_trends
    )
    
    if infection_markers_elevated and not note_parser_context.get('infection_signals'):
        print(f"[{agent_name}] Infection markers elevated but no signals from Note Parser...")
        _communicate_with_note_parser({'infection_markers_elevated': True})
    
    # PHASE 7: MEMORY - Write findings to shared memory
    print(f"[{agent_name}] Writing to shared memory...")
    _write_to_shared_memory(
        lab_trends,
        vital_trends,
        reasoning_result,
        validation,
        state['patient_id']
    )
    
    # Update state
    state['lab_trends'] = lab_trends
    state['vital_trends'] = vital_trends
    
    # Log completion
    AGENT_MEMORY.log_agent_action(
        agent_name,
        'complete',
        {
            'lab_trends_found': len(lab_trends),
            'vital_trends_found': len(vital_trends),
            'confidence': reasoning_result.get('confidence', 0.8),
            'correlations': len(reasoning_result.get('correlations_found', []))
        }
    )
    
    print(f"[{agent_name}] Complete! Analyzed {len(lab_trends)} lab trends, "
          f"{len(vital_trends)} vital trends "
          f"(confidence: {reasoning_result.get('confidence', 0.8):.2f})")
    
    return state
