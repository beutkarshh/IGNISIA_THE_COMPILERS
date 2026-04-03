"""
Agent Reasoning Module

Provides reasoning capabilities for agents:
- Chain-of-thought prompting templates
- Self-critique and reflection patterns
- Validation and verification functions
- Structured reasoning frameworks
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except:
    genai = None
    GENAI_AVAILABLE = False


# ============================================================================
# CHAIN-OF-THOUGHT PROMPTING
# ============================================================================

class ChainOfThought:
    """
    Structured chain-of-thought reasoning for agents.
    Breaks down complex reasoning into explicit steps.
    """
    
    @staticmethod
    def medical_analysis_template(question: str, context: Dict) -> str:
        """
        Template for medical analysis with step-by-step reasoning.
        
        Args:
            question: The question to answer
            context: Patient data and findings
            
        Returns:
            Structured prompt for LLM
        """
        return f"""You are a medical AI assistant. Use step-by-step reasoning to analyze this case.

QUESTION: {question}

PATIENT CONTEXT:
{json.dumps(context, indent=2)}

Please think through this step-by-step:

STEP 1: OBSERVE
- What are the key clinical findings?
- What measurements or values are abnormal?
- What patterns do you notice?

STEP 2: INTERPRET
- What could explain these findings?
- What clinical conditions are suggested?
- Are there any inconsistencies?

STEP 3: CORRELATE
- How do the different findings relate to each other?
- Do vitals support the lab findings?
- Do symptoms match the objective data?

STEP 4: CONCLUDE
- What is the most likely explanation?
- What is your confidence level (0-1)?
- What alternative explanations exist?

STEP 5: RECOMMEND
- What should be done next?
- What additional information is needed?
- What should be validated?

Format your response as JSON:
{{
  "observation": "...",
  "interpretation": "...",
  "correlation": "...",
  "conclusion": "...",
  "confidence": 0.0-1.0,
  "alternatives": [...],
  "recommendations": [...]
}}"""
    
    @staticmethod
    def trend_analysis_template(parameter: str, values: List[float], 
                                timestamps: List[str]) -> str:
        """Template for analyzing trends with reasoning."""
        return f"""Analyze this clinical parameter trend using step-by-step reasoning.

PARAMETER: {parameter}
VALUES: {values}
TIMEPOINTS: {timestamps}

Think step-by-step:

STEP 1: PATTERN IDENTIFICATION
- What is the overall direction (rising/falling/stable)?
- How rapid is the change?
- Are there any sudden jumps or drops?

STEP 2: CLINICAL SIGNIFICANCE
- Is this parameter critical?
- What does this trend suggest clinically?
- Should this trigger concern?

STEP 3: UNDERLYING CAUSES
- What could cause this trend?
- What physiological processes are involved?
- Are there multiple possible causes?

STEP 4: VALIDATION
- Does this trend make physiological sense?
- Could this be measurement error?
- What would confirm this is real?

Respond in JSON:
{{
  "pattern": "...",
  "clinical_significance": "...",
  "possible_causes": [...],
  "confidence": 0.0-1.0,
  "validation_needed": true/false,
  "reasoning": "..."
}}"""
    
    @staticmethod
    def conflict_resolution_template(finding1: Dict, finding2: Dict) -> str:
        """Template for resolving conflicting findings."""
        return f"""Two agents have conflicting findings. Use reasoning to resolve this.

FINDING 1:
{json.dumps(finding1, indent=2)}

FINDING 2:
{json.dumps(finding2, indent=2)}

Reason through this systematically:

STEP 1: IDENTIFY THE CONFLICT
- What exactly contradicts?
- Is this a direct contradiction or just different perspectives?

STEP 2: EVALUATE EVIDENCE
- What evidence supports Finding 1?
- What evidence supports Finding 2?
- Which has stronger clinical basis?

STEP 3: CONSIDER ALTERNATIVES
- Could both be partially correct?
- Is there a third explanation that reconciles both?

STEP 4: RESOLVE
- Which finding is more likely correct?
- Can they be reconciled?
- What additional data would resolve this?

Respond in JSON:
{{
  "conflict_type": "...",
  "resolution": "finding1" | "finding2" | "both_partial" | "neither",
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "recommended_action": "..."
}}"""


# ============================================================================
# SELF-CRITIQUE PATTERNS
# ============================================================================

class SelfCritique:
    """
    Self-critique patterns for agents to validate their own reasoning.
    """
    
    @staticmethod
    def critique_extraction(extracted_data: Dict, source_text: str) -> str:
        """Critique extraction results."""
        return f"""Review your extraction and check for errors.

SOURCE TEXT:
{source_text}

YOUR EXTRACTION:
{json.dumps(extracted_data, indent=2)}

SELF-CRITIQUE CHECKLIST:

1. COMPLETENESS
   - Did I extract all relevant information?
   - Did I miss anything important?
   - Are there mentions I overlooked?

2. ACCURACY
   - Are the values correct?
   - Did I misinterpret anything?
   - Are severities appropriately assigned?

3. CONSISTENCY
   - Do the extracted items make sense together?
   - Are there contradictions?
   - Does this match clinical reality?

4. SPECIFICITY
   - Are terms specific enough?
   - Should I use more precise medical terminology?
   - Are time references clear?

Respond in JSON:
{{
  "completeness_score": 0.0-1.0,
  "accuracy_score": 0.0-1.0,
  "consistency_score": 0.0-1.0,
  "issues_found": [...],
  "suggested_corrections": [...],
  "confidence_in_extraction": 0.0-1.0
}}"""
    
    @staticmethod
    def critique_analysis(analysis: Dict, supporting_data: Dict) -> str:
        """Critique an analysis."""
        return f"""Critically evaluate your analysis.

YOUR ANALYSIS:
{json.dumps(analysis, indent=2)}

SUPPORTING DATA:
{json.dumps(supporting_data, indent=2)}

CRITICAL EVALUATION:

1. LOGIC
   - Is my reasoning sound?
   - Did I make logical leaps?
   - Are my conclusions supported?

2. BIAS
   - Am I favoring certain interpretations?
   - Did I consider alternatives equally?
   - Am I overconfident?

3. EVIDENCE
   - Is there sufficient evidence?
   - Did I ignore contrary evidence?
   - What evidence would change my conclusion?

4. CLINICAL PLAUSIBILITY
   - Does this make medical sense?
   - Have I seen this pattern before?
   - Are there red flags?

Respond in JSON:
{{
  "logic_score": 0.0-1.0,
  "bias_detected": true/false,
  "evidence_strength": "weak" | "moderate" | "strong",
  "concerns": [...],
  "confidence_after_critique": 0.0-1.0,
  "should_revise": true/false
}}"""
    
    @staticmethod
    def validate_reasoning_chain(reasoning_steps: List[str], 
                                conclusion: str) -> str:
        """Validate a reasoning chain leads to the conclusion."""
        return f"""Validate that this reasoning chain properly supports the conclusion.

REASONING STEPS:
{json.dumps(reasoning_steps, indent=2)}

CONCLUSION:
{conclusion}

VALIDATION CHECKS:

1. LOGICAL FLOW
   - Does each step follow from the previous?
   - Are there gaps in reasoning?
   - Are assumptions stated clearly?

2. SUFFICIENCY
   - Do the steps adequately support the conclusion?
   - Is the conclusion the only possibility?
   - What other conclusions could this support?

3. NECESSITY
   - Are all steps necessary?
   - Are any steps redundant?
   - Is each step justified?

Respond in JSON:
{{
  "chain_valid": true/false,
  "gaps_identified": [...],
  "alternative_conclusions": [...],
  "confidence_in_conclusion": 0.0-1.0,
  "reasoning_quality": "weak" | "moderate" | "strong"
}}"""


# ============================================================================
# VALIDATION FRAMEWORKS
# ============================================================================

def validate_clinical_plausibility(finding: Dict, context: Dict) -> Dict[str, Any]:
    """
    Validate if a finding is clinically plausible given context.
    
    Args:
        finding: The finding to validate
        context: Clinical context (vitals, labs, symptoms)
        
    Returns:
        Validation result
    """
    # This would typically use medical knowledge base
    # For now, implement basic heuristics
    
    plausibility_checks = []
    plausible = True
    
    # Example: If finding claims sepsis, check for supporting evidence
    if 'sepsis' in str(finding).lower():
        # Check for infection signals
        has_fever = context.get('vitals', {}).get('temperature', 37) > 38
        has_elevated_wbc = context.get('labs', {}).get('wbc', 7) > 12
        has_tachycardia = context.get('vitals', {}).get('heart_rate', 80) > 90
        
        if not (has_fever or has_elevated_wbc or has_tachycardia):
            plausible = False
            plausibility_checks.append({
                'check': 'sepsis_indicators',
                'passed': False,
                'reason': 'Sepsis claimed but no supporting vital/lab findings'
            })
    
    return {
        'plausible': plausible,
        'confidence': 0.8 if plausible else 0.3,
        'checks_performed': plausibility_checks,
        'recommendation': 'accept' if plausible else 'review'
    }


def cross_validate_findings(finding1: Dict, finding2: Dict) -> Dict[str, Any]:
    """
    Cross-validate two findings for consistency.
    
    Args:
        finding1: First finding
        finding2: Second finding
        
    Returns:
        Validation result
    """
    consistency_score = 1.0
    issues = []
    
    # Check for direct contradictions
    # This is simplified - would be more sophisticated in production
    if finding1.get('type') == finding2.get('type'):
        if finding1.get('data') != finding2.get('data'):
            consistency_score = 0.5
            issues.append('Same type but different data values')
    
    return {
        'consistent': consistency_score > 0.7,
        'consistency_score': consistency_score,
        'issues': issues,
        'recommendation': 'accept' if consistency_score > 0.7 else 'investigate'
    }


def validate_trend_direction(values: List[float], claimed_direction: str) -> bool:
    """
    Validate that a claimed trend direction matches the actual data.
    
    Args:
        values: List of values
        claimed_direction: The claimed direction ('rising', 'falling', 'stable')
        
    Returns:
        True if claim matches data
    """
    if len(values) < 2:
        return True  # Can't validate with insufficient data
    
    first = values[0]
    last = values[-1]
    
    if first == 0:
        return True
    
    change_pct = ((last - first) / first) * 100
    
    if claimed_direction in ['rising', 'rising_sharply']:
        return change_pct > 5
    elif claimed_direction in ['falling', 'falling_sharply']:
        return change_pct < -5
    elif claimed_direction == 'stable':
        return abs(change_pct) < 10
    
    return False


# ============================================================================
# REASONING HELPER FUNCTIONS
# ============================================================================

def generate_confidence_score(evidence_strength: str, consistency: float, 
                             validation_passed: bool) -> float:
    """
    Generate a confidence score based on multiple factors.
    
    Args:
        evidence_strength: 'weak', 'moderate', or 'strong'
        consistency: Consistency score 0-1
        validation_passed: Whether validation checks passed
        
    Returns:
        Confidence score 0-1
    """
    base_score = {
        'weak': 0.3,
        'moderate': 0.6,
        'strong': 0.9
    }.get(evidence_strength, 0.5)
    
    # Adjust for consistency
    base_score *= consistency
    
    # Penalize if validation failed
    if not validation_passed:
        base_score *= 0.5
    
    return min(max(base_score, 0.0), 1.0)


def identify_reasoning_gaps(steps: List[str], conclusion: str) -> List[str]:
    """
    Identify gaps in a reasoning chain.
    
    Args:
        steps: List of reasoning steps
        conclusion: The conclusion
        
    Returns:
        List of identified gaps
    """
    gaps = []
    
    # Check for sufficient steps
    if len(steps) < 2:
        gaps.append("Insufficient reasoning steps - need at least 2")
    
    # Check for logical connectors (simplified)
    connectors = ['therefore', 'thus', 'because', 'since', 'so', 'hence']
    has_connectors = any(any(c in step.lower() for c in connectors) for step in steps)
    
    if not has_connectors:
        gaps.append("No logical connectors found - reasoning may be disconnected")
    
    # Check if conclusion appears in steps
    conclusion_mentioned = any(conclusion.lower() in step.lower() for step in steps)
    if not conclusion_mentioned:
        gaps.append("Conclusion not mentioned in reasoning steps - may be leap")
    
    return gaps


def generate_alternative_hypotheses(findings: List[Dict], max_alternatives: int = 3) -> List[Dict]:
    """
    Generate alternative hypotheses based on findings.
    
    Args:
        findings: List of findings
        max_alternatives: Maximum number of alternatives to generate
        
    Returns:
        List of alternative hypotheses
    """
    # This would typically use medical knowledge base
    # Simplified version
    
    alternatives = []
    
    # Example: If high lactate, consider alternatives to sepsis
    has_high_lactate = any(
        f.get('data', {}).get('parameter') == 'lactate' and 
        f.get('data', {}).get('values', [0])[-1] > 2.0
        for f in findings
    )
    
    if has_high_lactate:
        alternatives.append({
            'hypothesis': 'Tissue hypoperfusion from cardiogenic shock',
            'supporting_evidence': ['Elevated lactate'],
            'would_support': ['Low cardiac output', 'Pulmonary edema']
        })
        
        alternatives.append({
            'hypothesis': 'Liver dysfunction affecting lactate clearance',
            'supporting_evidence': ['Elevated lactate'],
            'would_support': ['Elevated bilirubin', 'Coagulopathy']
        })
    
    return alternatives[:max_alternatives]


# ============================================================================
# REASONING EXECUTOR
# ============================================================================

class ReasoningEngine:
    """
    Main reasoning engine that agents can use.
    Coordinates chain-of-thought, critique, and validation.
    """
    
    def __init__(self, llm_model = None):
        self.model = llm_model
        self.cot = ChainOfThought()
        self.critique = SelfCritique()
    
    def reason_through_analysis(self, question: str, context: Dict) -> Dict[str, Any]:
        """
        Use chain-of-thought to reason through an analysis.
        
        Args:
            question: The question to reason through
            context: Context data
            
        Returns:
            Reasoning result with confidence
        """
        if not self.model:
            # Fallback without LLM
            return {
                'conclusion': 'LLM not available - using rule-based fallback',
                'confidence': 0.5,
                'reasoning_steps': []
            }
        
        # Generate CoT prompt
        prompt = self.cot.medical_analysis_template(question, context)
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Parse JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'conclusion': 'Reasoning failed',
                'confidence': 0.0
            }
    
    def critique_and_refine(self, initial_result: Dict, source_data: Dict) -> Dict[str, Any]:
        """
        Critique an initial result and optionally refine.
        
        Args:
            initial_result: The initial analysis result
            source_data: Source data used for analysis
            
        Returns:
            Critique result with refinement suggestions
        """
        if not self.model:
            return {'refined': initial_result, 'critique_score': 0.7}
        
        prompt = self.critique.critique_analysis(initial_result, source_data)
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            critique_result = json.loads(result_text)
            
            # If critique suggests revision, could trigger re-analysis here
            if critique_result.get('should_revise'):
                return {
                    'needs_revision': True,
                    'critique': critique_result,
                    'refined': initial_result  # Would re-analyze in full implementation
                }
            
            return {
                'needs_revision': False,
                'critique': critique_result,
                'refined': initial_result
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'refined': initial_result
            }


if __name__ == "__main__":
    # Test reasoning module
    print("=== Testing Reasoning Module ===\n")
    
    # Test CoT template generation
    cot = ChainOfThought()
    
    question = "Is this patient showing signs of septic shock?"
    context = {
        'vitals': {'temperature': 38.9, 'heart_rate': 115, 'systolic_bp': 88},
        'labs': {'lactate': 3.8, 'wbc': 16.2},
        'symptoms': ['fever', 'hypotension']
    }
    
    prompt = cot.medical_analysis_template(question, context)
    print("Chain-of-Thought Prompt Generated:")
    print(prompt[:300] + "...\n")
    
    # Test validation
    finding = {'type': 'sepsis', 'confidence': 0.9}
    validation = validate_clinical_plausibility(finding, context)
    print(f"Clinical Plausibility: {validation['plausible']}")
    print(f"Confidence: {validation['confidence']}\n")
    
    # Test confidence scoring
    confidence = generate_confidence_score('strong', 0.9, True)
    print(f"Generated Confidence Score: {confidence}")
