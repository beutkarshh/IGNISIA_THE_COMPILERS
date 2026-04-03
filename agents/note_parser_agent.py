"""
Agent 1: Note Parser

Extracts structured information from unstructured clinical notes using Gemini.
Identifies symptoms, infection signals, and clinical events.
"""

import os
from typing import Dict, List
from datetime import datetime
import google.generativeai as genai
from agents.state import PatientState, ParsedSymptom


# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')


def note_parser_agent(state: PatientState) -> PatientState:
    """
    Parse clinical notes to extract symptoms and infection signals.
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with parsed_symptoms and infection_signals
    """
    # Collect all notes from timeline history
    all_notes = []
    for timepoint in state['timeline_history']:
        all_notes.append({
            'timestamp': timepoint['timestamp'],
            'time_label': timepoint['time_label'],
            'notes': timepoint['notes']
        })
    
    # Combine notes for analysis
    notes_text = "\n\n".join([
        f"[{n['time_label']}]: {n['notes']}" 
        for n in all_notes
    ])
    
    # Prompt for Gemini
    prompt = f"""You are a medical AI assistant analyzing ICU patient notes.

Patient Notes:
{notes_text}

Extract the following information:

1. SYMPTOMS: List all symptoms mentioned (fever, dyspnea, confusion, etc.)
2. INFECTION SIGNALS: Keywords suggesting infection (fever, elevated WBC, pneumonia, sepsis, etc.)
3. SEVERITY: For each symptom, estimate severity (mild/moderate/severe)

Respond in this exact JSON format:
{{
  "symptoms": [
    {{"symptom": "fever", "severity": "moderate", "timestamp": "..."}},
    {{"symptom": "dyspnea", "severity": "severe", "timestamp": "..."}}
  ],
  "infection_signals": ["fever", "pneumonia", "elevated_wbc"]
}}

Only include symptoms and signals explicitly mentioned in the notes.
Be conservative - don't infer beyond what's stated."""

    try:
        # Call Gemini
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Parse JSON response (remove markdown code blocks if present)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        import json
        parsed = json.loads(result_text)
        
        # Update state
        state['parsed_symptoms'] = parsed.get('symptoms', [])
        state['infection_signals'] = parsed.get('infection_signals', [])
        
    except Exception as e:
        print(f"Note parser error: {e}")
        # Fallback: basic keyword extraction
        state['parsed_symptoms'] = []
        state['infection_signals'] = []
        
        keywords = ['fever', 'infection', 'sepsis', 'pneumonia', 'elevated wbc']
        for keyword in keywords:
            if keyword.lower() in notes_text.lower():
                state['infection_signals'].append(keyword)
    
    return state
