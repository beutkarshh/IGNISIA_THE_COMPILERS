"""
Outlier Detection Module

Detects statistically anomalous lab values that likely represent lab errors
rather than true physiological changes.

Uses two methods:
1. Z-score: |z| > 3 indicates outlier
2. IQR (Interquartile Range): Values outside 1.5*IQR from Q1/Q3

Now includes confidence scoring based on:
- Sample size (more historical values = higher confidence)
- Data consistency (lower variance = higher confidence)
- Deviation magnitude (moderate deviation = higher confidence)

Note: Uses pure Python statistics library for cross-platform compatibility.
"""

from statistics import mean, stdev
from typing import List, Dict, Optional, Any


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])

    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


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
    
    # Use pure Python statistics for cross-platform stability
    try:
        mean_value = mean(historical_values)
        std_value = stdev(historical_values)
        
        if std_value == 0:
            return 0.0
        
        return abs((value - mean_value) / std_value)
    except Exception:
        return 0.0


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
    
    # Use pure Python percentile calculation
    q1 = _percentile(historical_values, 25)
    q3 = _percentile(historical_values, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return value < lower_bound or value > upper_bound


def calculate_confidence(
    z_score: float,
    historical_count: int,
    historical_variance: float
) -> float:
    """
    Calculate confidence score (0-1) for outlier detection.
    
    Factors:
    - Number of historical values (more = higher confidence)
    - Consistency of historical data (low variance = higher confidence)
    - Magnitude of deviation (moderate deviation = higher confidence)
    
    Args:
        z_score: Absolute z-score of the value
        historical_count: Number of historical values used
        historical_variance: Variance of historical values
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence from sample size
    if historical_count < 3:
        return 0.0  # Not enough data
    elif historical_count < 5:
        size_confidence = 0.5
    elif historical_count < 10:
        size_confidence = 0.75
    else:
        size_confidence = 0.9
    
    # Confidence from data consistency (inverse of variance)
    # Lower variance = more confident in outlier detection
    if historical_variance < 0.1:
        variance_confidence = 0.9
    elif historical_variance < 1.0:
        variance_confidence = 0.7
    elif historical_variance < 5.0:
        variance_confidence = 0.5
    else:
        variance_confidence = 0.3
    
    # Confidence from z-score magnitude
    # Very extreme values might be data entry errors
    abs_z = abs(z_score)
    if 3.0 <= abs_z <= 5.0:
        magnitude_confidence = 1.0  # Sweet spot
    elif abs_z > 5.0:
        magnitude_confidence = 0.7  # Might be too extreme
    else:
        magnitude_confidence = 0.5
    
    # Weighted average
    confidence = (
        size_confidence * 0.4 +
        variance_confidence * 0.3 +
        magnitude_confidence * 0.3
    )
    
    return round(confidence, 2)


def _get_recommendation(parameter: str, z_score: float, confidence: float) -> str:
    """Generate recommendation based on confidence."""
    if confidence >= 0.8:
        return f"High confidence outlier detected. Strongly recommend redrawing {parameter}."
    elif confidence >= 0.6:
        return f"Moderate confidence outlier. Consider redrawing {parameter} if clinically inconsistent."
    else:
        return f"Low confidence outlier. Verify {parameter} value and consider redraw if concerning."


def flag_outlier(
    parameter: str,
    value: float,
    historical_values: List[float],
    timestamp: str
) -> Optional[Dict[str, Any]]:
    """
    Flag value as outlier if statistically anomalous.
    
    NOW REQUIRES: ≥3 historical values for detection
    NOW INCLUDES: Confidence score (0-1)
    
    Args:
        parameter: Lab parameter name (e.g., "WBC", "Lactate")
        value: Current value to test
        historical_values: List of previous values (should NOT include current value)
        timestamp: ISO timestamp of the current value
        
    Returns:
        OutlierAlert dict if outlier detected, None otherwise
    """
    # Require minimum 3 historical values (CHANGED from 2)
    if len(historical_values) < 3:
        return None
    
    z_score = calculate_z_score(value, historical_values)
    is_iqr_outlier = calculate_iqr_outlier(value, historical_values)
    
    # Calculate variance for confidence
    try:
        variance = stdev(historical_values) ** 2
    except:
        variance = 0.0
    
    # Calculate confidence score
    confidence = calculate_confidence(
        z_score=z_score,
        historical_count=len(historical_values),
        historical_variance=variance
    )
    
    # Detect outlier
    if z_score > 3.0 or is_iqr_outlier:
        return {
            'parameter': parameter,
            'value': value,
            'timestamp': timestamp,
            'outlier_detected': True,
            'confidence': confidence,  # NEW
            'historical_count': len(historical_values),  # NEW
            'historical_values': historical_values,
            'z_score': round(z_score, 2),
            'iqr_outlier': is_iqr_outlier,
            'reason': f"Z-score = {z_score:.2f} (>3.0 threshold)" if z_score > 3.0 else "IQR outlier",
            'recommendation': _get_recommendation(parameter, z_score, confidence)  # Enhanced
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
