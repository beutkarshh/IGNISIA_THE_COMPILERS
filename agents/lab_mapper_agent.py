"""
Agent 2: Temporal Lab Mapper

Analyzes lab values and vitals over time to detect trends.
Identifies rising, falling, or stable patterns in critical parameters.
"""

from typing import Dict, List
from agents.state import PatientState, LabTrend


def calculate_trend(values: List[float]) -> str:
    """
    Determine trend direction and magnitude.
    
    Args:
        values: List of values in chronological order
        
    Returns:
        Trend description: "stable", "rising", "falling", "rising_sharply", "falling_sharply"
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


def lab_mapper_agent(state: PatientState) -> PatientState:
    """
    Map lab values and vitals over time to detect trends.
    
    Args:
        state: Current patient state
        
    Returns:
        Updated state with lab_trends and vital_trends
    """
    timeline = state['timeline_history']
    
    if len(timeline) < 2:
        state['lab_trends'] = []
        state['vital_trends'] = {}
        return state
    
    # Extract lab parameters
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
            trend = calculate_trend(values)
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
            trend = calculate_trend(values)
            vital_trends[param] = trend
    
    state['lab_trends'] = lab_trends
    state['vital_trends'] = vital_trends
    
    return state
