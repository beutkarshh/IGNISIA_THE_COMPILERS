"""
Outlier Detection Module

Detects statistically anomalous lab values that likely represent lab errors
rather than true physiological changes.

Uses two methods:
1. Z-score: |z| > 3 indicates outlier
2. IQR (Interquartile Range): Values outside 1.5*IQR from Q1/Q3
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Optional


def calculate_z_score(value: float, historical_values: List[float]) -> float:
    """
    Calculate z-score for a value against historical data.
    
    Args:
        value: The value to test
        historical_values: List of previous values
        
    Returns:
        Z-score (number of standard deviations from mean)
    """
    if len(historical_values) < 2:
        return 0.0
    
    mean = np.mean(historical_values)
    std = np.std(historical_values, ddof=1)
    
    if std == 0:
        return 0.0
    
    return abs((value - mean) / std)


def calculate_iqr_outlier(value: float, historical_values: List[float]) -> bool:
    """
    Detect outlier using IQR method.
    
    Args:
        value: The value to test
        historical_values: List of previous values
        
    Returns:
        True if value is an outlier
    """
    if len(historical_values) < 3:
        return False
    
    q1 = np.percentile(historical_values, 25)
    q3 = np.percentile(historical_values, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return value < lower_bound or value > upper_bound


def flag_outlier(
    parameter: str,
    value: float,
    historical_values: List[float],
    timestamp: str,
    min_history: int = 3
) -> Optional[Dict]:
    """
    Detect if a lab value is a statistical outlier.
    
    Args:
        parameter: Lab parameter name (e.g., "wbc", "lactate")
        value: Current value to test
        historical_values: List of previous values (should NOT include current value)
        timestamp: ISO timestamp of the current value
        min_history: Minimum historical values required for detection
        
    Returns:
        OutlierAlert dict if outlier detected, None otherwise
    """
    # Need enough history to detect outliers
    if len(historical_values) < min_history:
        return None
    
    # Calculate z-score
    z_score = calculate_z_score(value, historical_values)
    z_score_outlier = z_score > 3.0
    
    # Calculate IQR
    iqr_outlier = calculate_iqr_outlier(value, historical_values)
    
    # Flag as outlier if BOTH methods agree (high confidence)
    if z_score_outlier and iqr_outlier:
        confidence = min(z_score / 5.0, 1.0)  # Normalize to 0-1
        
        return {
            "parameter": parameter,
            "value": value,
            "timestamp": timestamp,
            "detection_method": "z_score_and_iqr",
            "confidence": confidence,
            "historical_values": historical_values,
            "z_score": z_score,
            "recommendation": f"Value {value} deviates significantly from trend {historical_values}. Recommend redraw to confirm."
        }
    
    # Flag as potential outlier if only one method detects it (medium confidence)
    elif z_score_outlier or iqr_outlier:
        method = "z_score" if z_score_outlier else "iqr"
        confidence = 0.5
        
        return {
            "parameter": parameter,
            "value": value,
            "timestamp": timestamp,
            "detection_method": method,
            "confidence": confidence,
            "historical_values": historical_values,
            "z_score": z_score,
            "recommendation": f"Possible outlier detected. Consider clinical correlation."
        }
    
    return None


def analyze_all_labs(current_labs: Dict[str, float], 
                      timeline_history: List[Dict],
                      current_timestamp: str) -> List[Dict]:
    """
    Analyze all lab values for outliers.
    
    Args:
        current_labs: Current lab values dict
        timeline_history: List of all previous timepoints
        current_timestamp: Timestamp of current labs
        
    Returns:
        List of outlier alerts
    """
    outliers = []
    
    # Extract historical values for each parameter
    for param, current_value in current_labs.items():
        historical = [
            tp['labs'][param] 
            for tp in timeline_history 
            if param in tp.get('labs', {})
        ]
        
        outlier = flag_outlier(
            parameter=param,
            value=current_value,
            historical_values=historical,
            timestamp=current_timestamp
        )
        
        if outlier:
            outliers.append(outlier)
    
    return outliers
