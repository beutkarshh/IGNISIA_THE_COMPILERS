"""
Agent Tools Module

Provides tools that agents can use for:
- Clinical calculations (SOFA, APACHE, etc.)
- Data validation and verification
- Inter-agent communication
- Medical knowledge lookups
- Statistical analysis
"""

import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json

# Secure API key loading
try:
    from utils.secure_api_key import load_gemini_api_key, test_gemini_connection
    import google.generativeai as genai
    
    # Configure Gemini with secure key loading
    api_key = load_gemini_api_key()
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured with secure key")
    else:
        print("⚠️ No Gemini API key found - using fallback mode")
        genai = None
except Exception as e:
    print(f"⚠️ Gemini API setup failed: {e}")
    genai = None


# ============================================================================
# CLINICAL CALCULATION TOOLS
# ============================================================================

def calculate_sofa_score(vitals: Dict, labs: Dict) -> Dict[str, Any]:
    """
    Calculate Sequential Organ Failure Assessment (SOFA) score.
    
    Args:
        vitals: Dictionary with vital signs
        labs: Dictionary with lab values
        
    Returns:
        Dictionary with SOFA score and components
    """
    score = 0
    components = {}
    
    # Respiratory (PaO2/FiO2 ratio - approximated by SpO2)
    spo2 = vitals.get('spo2', 100)
    if spo2 < 90:
        resp_score = 2
    elif spo2 < 95:
        resp_score = 1
    else:
        resp_score = 0
    score += resp_score
    components['respiratory'] = resp_score
    
    # Cardiovascular (MAP and vasopressors)
    systolic = vitals.get('systolic_bp', 120)
    diastolic = vitals.get('diastolic_bp', 80)
    map_value = diastolic + (systolic - diastolic) / 3
    
    if map_value < 70:
        cardio_score = 1
    else:
        cardio_score = 0
    score += cardio_score
    components['cardiovascular'] = cardio_score
    
    # Hepatic (bilirubin - not in our data, skip)
    components['hepatic'] = 0
    
    # Coagulation (platelets)
    platelets = labs.get('platelets', 250)
    if platelets < 50:
        coag_score = 3
    elif platelets < 100:
        coag_score = 2
    elif platelets < 150:
        coag_score = 1
    else:
        coag_score = 0
    score += coag_score
    components['coagulation'] = coag_score
    
    # Renal (creatinine)
    creatinine = labs.get('creatinine', 1.0)
    if creatinine >= 3.5:
        renal_score = 3
    elif creatinine >= 2.0:
        renal_score = 2
    elif creatinine >= 1.2:
        renal_score = 1
    else:
        renal_score = 0
    score += renal_score
    components['renal'] = renal_score
    
    # Neurological (GCS - not in our data, skip)
    components['neurological'] = 0
    
    return {
        'total_score': score,
        'components': components,
        'interpretation': interpret_sofa_score(score),
        'timestamp': datetime.utcnow().isoformat()
    }


def interpret_sofa_score(score: int) -> str:
    """Interpret SOFA score."""
    if score >= 15:
        return "Very high mortality risk (>80%)"
    elif score >= 10:
        return "High mortality risk (40-50%)"
    elif score >= 6:
        return "Moderate mortality risk (~20%)"
    else:
        return "Low mortality risk (<10%)"


def calculate_map(systolic: int, diastolic: int) -> float:
    """Calculate Mean Arterial Pressure."""
    return diastolic + (systolic - diastolic) / 3


def calculate_shock_index(heart_rate: int, systolic_bp: int) -> Dict[str, Any]:
    """
    Calculate Shock Index (HR/SBP).
    
    Normal: 0.5-0.7
    Elevated: >0.9 suggests hypovolemia
    Critical: >1.0 suggests severe shock
    """
    if systolic_bp == 0:
        return {'value': None, 'interpretation': 'Cannot calculate - SBP is 0'}
    
    shock_index = heart_rate / systolic_bp
    
    if shock_index > 1.0:
        interpretation = "Critical - Severe shock likely"
    elif shock_index > 0.9:
        interpretation = "Elevated - Hypovolemia suspected"
    elif shock_index >= 0.5:
        interpretation = "Normal"
    else:
        interpretation = "Low - Consider bradycardia or hypertension"
    
    return {
        'value': round(shock_index, 2),
        'interpretation': interpretation,
        'hr': heart_rate,
        'sbp': systolic_bp,
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# VALIDATION TOOLS
# ============================================================================

def validate_lab_value(parameter: str, value: float, reference_ranges: Dict) -> Dict[str, Any]:
    """
    Validate a lab value against reference ranges.
    
    Args:
        parameter: Lab parameter name (e.g., 'wbc', 'lactate')
        value: The value to validate
        reference_ranges: Dictionary of reference ranges
        
    Returns:
        Validation result with status and interpretation
    """
    if parameter not in reference_ranges.get('labs', {}):
        return {
            'valid': None,
            'status': 'unknown',
            'message': f"No reference range for {parameter}"
        }
    
    min_val, max_val = reference_ranges['labs'][parameter]
    
    if value < min_val:
        severity = 'critical' if value < min_val * 0.5 else 'low'
        return {
            'valid': False,
            'status': severity,
            'message': f"{parameter} is {severity} ({value} < {min_val})",
            'value': value,
            'range': (min_val, max_val),
            'deviation_percent': round(((min_val - value) / min_val) * 100, 1)
        }
    elif value > max_val:
        severity = 'critical' if value > max_val * 2 else 'high'
        return {
            'valid': False,
            'status': severity,
            'message': f"{parameter} is {severity} ({value} > {max_val})",
            'value': value,
            'range': (min_val, max_val),
            'deviation_percent': round(((value - max_val) / max_val) * 100, 1)
        }
    else:
        return {
            'valid': True,
            'status': 'normal',
            'message': f"{parameter} is within normal range",
            'value': value,
            'range': (min_val, max_val)
        }


def validate_vital_signs(vitals: Dict, reference_ranges: Dict) -> List[Dict[str, Any]]:
    """Validate all vital signs and return alerts."""
    alerts = []
    
    for param, value in vitals.items():
        if param in reference_ranges.get('vitals', {}):
            result = validate_lab_value(param, value, {'labs': reference_ranges['vitals']})
            if not result.get('valid'):
                alerts.append({
                    'parameter': param,
                    'finding': result['message'],
                    'severity': result['status']
                })
    
    return alerts


# ============================================================================
# MEDICAL KNOWLEDGE TOOLS
# ============================================================================

def lookup_symptom_severity(symptom: str, context: Dict) -> Dict[str, Any]:
    """
    Assess symptom severity based on clinical context.
    
    Args:
        symptom: The symptom name
        context: Patient vitals and labs
        
    Returns:
        Severity assessment
    """
    # Simple rule-based severity assessment
    severity_map = {
        'fever': lambda ctx: 'severe' if ctx.get('vitals', {}).get('temperature', 37) > 39 else 'moderate',
        'hypotension': lambda ctx: 'severe' if ctx.get('vitals', {}).get('systolic_bp', 120) < 90 else 'moderate',
        'dyspnea': lambda ctx: 'severe' if ctx.get('vitals', {}).get('spo2', 100) < 90 else 'moderate',
        'tachycardia': lambda ctx: 'severe' if ctx.get('vitals', {}).get('heart_rate', 80) > 120 else 'moderate',
    }
    
    if symptom.lower() in severity_map:
        severity = severity_map[symptom.lower()](context)
    else:
        severity = 'unknown'
    
    return {
        'symptom': symptom,
        'severity': severity,
        'context_factors': list(context.keys())
    }


def check_medication_interactions(medications: List[str]) -> List[Dict[str, str]]:
    """
    Check for potential medication interactions.
    (Simplified - would use real drug database in production)
    """
    # Placeholder - would integrate with drug interaction API
    known_interactions = {
        ('warfarin', 'aspirin'): 'Increased bleeding risk',
        ('nsaid', 'ace_inhibitor'): 'Reduced antihypertensive effect'
    }
    
    interactions = []
    for i, med1 in enumerate(medications):
        for med2 in medications[i+1:]:
            if (med1, med2) in known_interactions:
                interactions.append({
                    'drug1': med1,
                    'drug2': med2,
                    'interaction': known_interactions[(med1, med2)]
                })
    
    return interactions


# ============================================================================
# STATISTICAL ANALYSIS TOOLS
# ============================================================================

def calculate_trend_statistics(values: List[float]) -> Dict[str, Any]:
    """
    Calculate statistical properties of a trend.
    
    Returns mean, std dev, coefficient of variation, etc.
    """
    if len(values) < 2:
        return {'error': 'Insufficient data'}
    
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = variance ** 0.5
    
    # Coefficient of variation
    cv = (std_dev / mean * 100) if mean != 0 else 0
    
    # Linear trend (simple slope)
    x_values = list(range(n))
    x_mean = sum(x_values) / n
    y_mean = mean
    
    numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    slope = numerator / denominator if denominator != 0 else 0
    
    return {
        'n': n,
        'mean': round(mean, 2),
        'std_dev': round(std_dev, 2),
        'min': min(values),
        'max': max(values),
        'range': max(values) - min(values),
        'coefficient_of_variation': round(cv, 2),
        'slope': round(slope, 4),
        'trend_direction': 'increasing' if slope > 0.1 else ('decreasing' if slope < -0.1 else 'stable')
    }


def detect_pattern_anomaly(values: List[float], current_value: float) -> Dict[str, Any]:
    """
    Detect if current value is anomalous compared to historical pattern.
    Uses simple z-score method.
    """
    if len(values) < 3:
        return {'anomaly': False, 'reason': 'Insufficient history'}
    
    stats = calculate_trend_statistics(values)
    mean = stats['mean']
    std_dev = stats['std_dev']
    
    if std_dev == 0:
        z_score = 0
    else:
        z_score = (current_value - mean) / std_dev
    
    is_anomaly = abs(z_score) > 2.0  # 2 standard deviations
    
    return {
        'anomaly': is_anomaly,
        'z_score': round(z_score, 2),
        'current_value': current_value,
        'historical_mean': mean,
        'historical_std': std_dev,
        'interpretation': f"Value is {abs(z_score):.1f} standard deviations from mean"
    }


# ============================================================================
# INTER-AGENT COMMUNICATION TOOLS
# ============================================================================

class AgentMessage:
    """Represents a message between agents."""
    
    def __init__(self, sender: str, recipient: str, message_type: str, content: Any):
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type  # 'query', 'response', 'alert', 'request'
        self.content = content
        self.timestamp = datetime.utcnow().isoformat()
        self.id = f"{sender}-{recipient}-{datetime.utcnow().timestamp()}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        msg = cls(data['sender'], data['recipient'], data['type'], data['content'])
        msg.timestamp = data['timestamp']
        msg.id = data['id']
        return msg


def create_agent_query(sender: str, recipient: str, question: str) -> AgentMessage:
    """Create a query message from one agent to another."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type='query',
        content={'question': question}
    )


def create_agent_alert(sender: str, recipient: str, alert_type: str, details: Dict) -> AgentMessage:
    """Create an alert message."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type='alert',
        content={'alert_type': alert_type, 'details': details}
    )


def create_agent_request(sender: str, recipient: str, action: str, parameters: Dict) -> AgentMessage:
    """Create a request for action."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type='request',
        content={'action': action, 'parameters': parameters}
    )


# ============================================================================
# TOOL REGISTRY
# ============================================================================

class ToolRegistry:
    """Registry of all available tools for agents."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {
            # Clinical calculations
            'calculate_sofa_score': calculate_sofa_score,
            'calculate_map': calculate_map,
            'calculate_shock_index': calculate_shock_index,
            
            # Validation
            'validate_lab_value': validate_lab_value,
            'validate_vital_signs': validate_vital_signs,
            
            # Medical knowledge
            'lookup_symptom_severity': lookup_symptom_severity,
            'check_medication_interactions': check_medication_interactions,
            
            # Statistical analysis
            'calculate_trend_statistics': calculate_trend_statistics,
            'detect_pattern_anomaly': detect_pattern_anomaly,
            
            # Communication
            'create_agent_query': create_agent_query,
            'create_agent_alert': create_agent_alert,
            'create_agent_request': create_agent_request,
        }
    
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self.tools.keys())
    
    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """Get description of a tool."""
        tool = self.get_tool(tool_name)
        if tool and tool.__doc__:
            return tool.__doc__.strip()
        return None
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a tool with arguments."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return tool(**kwargs)


# Global tool registry instance
TOOL_REGISTRY = ToolRegistry()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_tool_for_llm(tool_name: str, registry: ToolRegistry = TOOL_REGISTRY) -> Dict:
    """
    Format a tool description for LLM function calling.
    
    Returns OpenAI/Gemini function schema format.
    """
    tool = registry.get_tool(tool_name)
    if not tool:
        return {}
    
    # Extract function signature
    import inspect
    sig = inspect.signature(tool)
    
    parameters = {
        'type': 'object',
        'properties': {},
        'required': []
    }
    
    for param_name, param in sig.parameters.items():
        param_type = 'string'  # Simplified - would parse actual types
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = 'integer'
            elif param.annotation == float:
                param_type = 'number'
            elif param.annotation == bool:
                param_type = 'boolean'
        
        parameters['properties'][param_name] = {'type': param_type}
        
        if param.default == inspect.Parameter.empty:
            parameters['required'].append(param_name)
    
    return {
        'name': tool_name,
        'description': registry.get_tool_description(tool_name) or '',
        'parameters': parameters
    }


if __name__ == "__main__":
    # Test tools
    print("=== Testing Tools Module ===\n")
    
    # Test clinical calculations
    vitals = {'heart_rate': 110, 'systolic_bp': 95, 'diastolic_bp': 60, 'spo2': 92}
    labs = {'platelets': 120, 'creatinine': 1.8, 'wbc': 15.0}
    
    sofa = calculate_sofa_score(vitals, labs)
    print(f"SOFA Score: {sofa['total_score']} - {sofa['interpretation']}")
    
    shock = calculate_shock_index(110, 95)
    print(f"Shock Index: {shock['value']} - {shock['interpretation']}\n")
    
    # Test validation
    from agents.state import REFERENCE_RANGES
    validation = validate_lab_value('wbc', 15.0, REFERENCE_RANGES)
    print(f"WBC Validation: {validation['message']}\n")
    
    # Test statistics
    trend_values = [1.3, 1.6, 2.4, 3.8]
    stats = calculate_trend_statistics(trend_values)
    print(f"Trend Statistics: Mean={stats['mean']}, Slope={stats['slope']}, Direction={stats['trend_direction']}\n")
    
    # Test communication
    msg = create_agent_query('lab_mapper', 'note_parser', 'Did you find any infection keywords?')
    print(f"Message created: {msg.to_dict()}\n")
    
    # Test tool registry
    print(f"Available tools: {len(TOOL_REGISTRY.list_tools())}")
    print(f"Tools: {', '.join(TOOL_REGISTRY.list_tools())}")
