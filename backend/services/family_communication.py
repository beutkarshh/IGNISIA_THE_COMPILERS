"""
Family Communication Service
Transforms clinical assessments into hopeful, compassionate summaries for patient families
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class ConfidenceLevel(Enum):
    HIGH = "high"        # 90%+
    MEDIUM = "medium"    # 70-89%
    OBSERVATION = "observation"  # <70%

class SupportedLanguage(Enum):
    ENGLISH = "en"
    HINDI = "hi"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"

@dataclass
class FamilyCommunication:
    patient_id: str
    timestamp: str
    diagnosis_summary: str
    confidence_level: ConfidenceLevel
    confidence_score: float
    hopeful_message: Dict[str, str]  # language -> message
    care_emphasis: Dict[str, str]
    next_steps: Dict[str, str]
    stability_status: str

class FamilyCommunicationAgent:
    """
    AI Agent specialized in creating hope-giving, family-friendly medical communications
    """
    
    def __init__(self):
        self.hope_phrases = self._load_hope_phrases()
        self.diagnosis_templates = self._load_diagnosis_templates()
    
    def generate_family_summary(
        self, 
        patient_data: Dict,
        assessment_result: Dict,
        target_languages: List[SupportedLanguage] = [SupportedLanguage.ENGLISH, SupportedLanguage.HINDI]
    ) -> FamilyCommunication:
        """
        Generate hopeful family communication from clinical assessment
        """
        # Extract key information
        confidence_score = assessment_result.get('risk_score', 50)
        diagnosis = assessment_result.get('primary_concern', 'monitoring')
        clinical_flags = assessment_result.get('clinical_flags', [])
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(confidence_score, clinical_flags)
        
        # Generate hopeful messages for each language
        hopeful_messages = {}
        care_emphasis = {}
        next_steps = {}
        
        for lang in target_languages:
            hopeful_messages[lang.value] = self._create_hopeful_message(
                diagnosis, confidence_level, confidence_score, lang
            )
            care_emphasis[lang.value] = self._create_care_emphasis(confidence_level, lang)
            next_steps[lang.value] = self._create_next_steps(diagnosis, confidence_level, lang)
        
        # Assess overall stability for families
        stability_status = self._assess_family_friendly_stability(patient_data, clinical_flags)
        
        return FamilyCommunication(
            patient_id=str(patient_data.get('subject_id', '')),
            timestamp=assessment_result.get('timestamp', ''),
            diagnosis_summary=self._simplify_diagnosis_for_family(diagnosis),
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            hopeful_message=hopeful_messages,
            care_emphasis=care_emphasis,
            next_steps=next_steps,
            stability_status=stability_status
        )
    
    def _determine_confidence_level(self, score: float, flags: List[str]) -> ConfidenceLevel:
        """Determine confidence level based on clinical assessment"""
        if score >= 90:
            return ConfidenceLevel.HIGH
        elif score >= 70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.OBSERVATION
    
    def _create_hopeful_message(
        self, 
        diagnosis: str, 
        confidence: ConfidenceLevel, 
        score: float,
        language: SupportedLanguage
    ) -> str:
        """Create hope-filled message explaining the condition"""
        
        # Get base template for diagnosis type
        if "sepsis" in diagnosis.lower():
            template_key = "sepsis"
        elif "cardiac" in diagnosis.lower() or "heart" in diagnosis.lower():
            template_key = "cardiac"
        elif "respiratory" in diagnosis.lower() or "lung" in diagnosis.lower():
            template_key = "respiratory"
        else:
            template_key = "general"
        
        # Get template for confidence level and language
        template = self.diagnosis_templates[template_key][confidence.value][language.value]
        hope_phrase = self.hope_phrases[confidence.value][language.value]
        
        return f"{template} {hope_phrase}"
    
    def _create_care_emphasis(self, confidence: ConfidenceLevel, language: SupportedLanguage) -> str:
        """Emphasize the quality of care being provided"""
        care_messages = {
            SupportedLanguage.ENGLISH: {
                ConfidenceLevel.HIGH: "Our experienced ICU team is providing 24/7 specialized care with the most advanced medical equipment.",
                ConfidenceLevel.MEDIUM: "Your loved one is receiving excellent care from our dedicated medical team around the clock.", 
                ConfidenceLevel.OBSERVATION: "Our medical team is carefully monitoring and providing the best supportive care while we gather information."
            },
            SupportedLanguage.HINDI: {
                ConfidenceLevel.HIGH: "हमारी अनुभवी ICU टीम अत्याधुनिक चिकित्सा उपकरणों के साथ 24/7 विशेषज्ञ देखभाल प्रदान कर रही है।",
                ConfidenceLevel.MEDIUM: "आपके प्रियजन को हमारी समर्पित चिकित्सा टीम से चौबीसों घंटे उत्कृष्ट देखभाल मिल रही है।",
                ConfidenceLevel.OBSERVATION: "हमारी चिकित्सा टीम सावधानीपूर्वक निगरानी कर रही है और जानकारी एकत्र करते समय बेहतरीन सहायक देखभाल प्रदान कर रही है।"
            }
        }
        
        return care_messages.get(language, care_messages[SupportedLanguage.ENGLISH])[confidence]
    
    def _create_next_steps(self, diagnosis: str, confidence: ConfidenceLevel, language: SupportedLanguage) -> str:
        """Explain next steps in hopeful terms"""
        if confidence == ConfidenceLevel.HIGH:
            if language == SupportedLanguage.HINDI:
                return "डॉक्टर निर्धारित उपचार योजना के अनुसार आगे बढ़ेंगे। हम नियमित रूप से आपको अपडेट देते रहेंगे।"
            else:
                return "The doctors will continue with the established treatment plan. We'll keep you updated on progress regularly."
        
        elif confidence == ConfidenceLevel.MEDIUM:
            if language == SupportedLanguage.HINDI:
                return "डॉक्टर कुछ और जांच करेंगे और फिर सबसे अच्छी उपचार योजना निर्धारित करेंगे।"
            else:
                return "The doctors will complete a few more tests and then establish the best treatment plan."
        
        else:  # OBSERVATION
            if language == SupportedLanguage.HINDI:
                return "डॉक्टर सावधानीपूर्वक जानकारी एकत्र कर रहे हैं ताकि सबसे सटीक उपचार दे सकें।"
            else:
                return "The doctors are carefully gathering information to provide the most precise treatment."
    
    def _assess_family_friendly_stability(self, patient_data: Dict, flags: List[str]) -> str:
        """Assess stability in family-friendly terms"""
        # Look for concerning flags
        concerning_flags = ["critical", "unstable", "deteriorating"]
        has_concerns = any(flag in ' '.join(flags).lower() for flag in concerning_flags)
        
        if not has_concerns:
            return "stable_comfortable"
        elif len(flags) <= 2:
            return "stable_monitored"
        else:
            return "receiving_intensive_care"
    
    def _simplify_diagnosis_for_family(self, diagnosis: str) -> str:
        """Convert medical diagnosis to family-friendly terms"""
        simplifications = {
            "sepsis": "infection that the body is fighting",
            "septic shock": "serious infection requiring intensive care",
            "cardiac event": "heart condition requiring monitoring", 
            "respiratory failure": "breathing support needed",
            "multi-organ": "condition affecting multiple systems"
        }
        
        for medical_term, family_term in simplifications.items():
            if medical_term in diagnosis.lower():
                return family_term
        
        return "condition requiring ICU monitoring"
    
    def _load_hope_phrases(self) -> Dict:
        """Load hope-giving phrases for different confidence levels"""
        return {
            "high": {
                "en": "Our medical team is very confident about the treatment plan and many patients recover excellently with this level of care.",
                "hi": "हमारी चिकित्सा टीम उपचार योजना के बारे में बहुत आश्वस्त है और कई मरीज़ इस स्तर की देखभाल से उत्कृष्ट रूप से ठीक हो जाते हैं।"
            },
            "medium": {
                "en": "The medical team is working with a clear direction and we're optimistic about the treatment approach.",
                "hi": "चिकित्सा टीम एक स्पष्ट दिशा में काम कर रही है और हम उपचार के दृष्टिकोण को लेकर आशावादी हैं।"
            },
            "observation": {
                "en": "Our experienced team is taking the most careful approach to ensure the best possible outcome.",
                "hi": "हमारी अनुभवी टीम सबसे अच्छे संभावित परिणाम को सुनिश्चित करने के लिए सबसे सावधान दृष्टिकोण अपना रही है।"
            }
        }
    
    def _load_diagnosis_templates(self) -> Dict:
        """Load diagnosis explanation templates"""
        return {
            "sepsis": {
                "high": {
                    "en": "The doctors have identified that your loved one is fighting an infection. The good news is that we caught this early and our medical team knows exactly how to treat this condition.",
                    "hi": "डॉक्टरों ने पहचाना है कि आपके प्रियजन के शरीर में संक्रमण से लड़ रहे हैं। अच्छी बात यह है कि हमने इसे जल्दी पकड़ लिया है और हमारी चिकित्सा टीम जानती है कि इसका इलाज कैसे करना है।"
                },
                "medium": {
                    "en": "Your loved one is receiving treatment for an infection. We are closely monitoring their progress and adjusting the treatment as needed.",
                    "hi": "आपके प्रियजन को संक्रमण के लिए उपचार मिल रहा है। हम उनकी प्रगति पर बारीकी से नज़र रख रहे हैं और आवश्यकतानुसार उपचार को समायोजित कर रहे हैं।"
                },
                "observation": {
                    "en": "The doctors are carefully monitoring some signs of infection and providing supportive care while determining the best treatment approach.",
                    "hi": "डॉक्टर संक्रमण के कुछ लक्षणों की सावधानीपूर्वक निगरानी कर रहे हैं और सबसे अच्छे उपचार का निर्धारण करते समय सहायक देखभाल प्रदान कर रहे हैं।"
                }
            },
            "cardiac": {
                "high": {
                    "en": "The doctors are treating your loved one's heart condition with proven medical approaches. Our cardiac team has extensive experience with these situations.",
                    "hi": "डॉक्टर आपके प्रियजन की हृदय की स्थिति का सिद्ध चिकित्सा दृष्टिकोण से इलाज कर रहे हैं। हमारी हृदय टीम के पास इन स्थितियों का व्यापक अनुभव है।"
                },
                "medium": {
                    "en": "The doctors are closely monitoring your loved one's heart and have several effective treatment options available.",
                    "hi": "डॉक्टर आपके प्रियजन के दिल पर बारीकी से नज़र रख रहे हैं और उनके पास कई प्रभावी उपचार विकल्प उपलब्ध हैं।"
                },
                "observation": {
                    "en": "The doctors are carefully observing your loved one's heart function and will determine the most appropriate care plan.",
                    "hi": "डॉक्टर आपके प्रियजन के हृदय के कार्य को सावधानीपूर्वक देख रहे हैं और सबसे उपयुक्त देखभाल योजना निर्धारित करेंगे।"
                }
            },
            "general": {
                "high": {
                    "en": "Your loved one is receiving excellent specialized care for their condition. The medical team is confident about the treatment approach.",
                    "hi": "आपके प्रियजन को उनकी स्थिति के लिए उत्कृष्ट विशेषज्ञ देखभाल मिल रही है। चिकित्सा टीम उपचार के दृष्टिकोण को लेकर आश्वस्त है।"
                },
                "medium": {
                    "en": "Your loved one is in good hands with our medical team. We are providing comprehensive care and monitoring their progress closely.",
                    "hi": "आपके प्रियजन हमारी चिकित्सा टीम के अच्छे हाथों में हैं। हम व्यापक देखभाल प्रदान कर रहे हैं और उनकी प्रगति पर बारीकी से नज़र रख रहे हैं।"
                },
                "observation": {
                    "en": "Our medical team is carefully observing your loved one and providing excellent supportive care while we gather information.",
                    "hi": "हमारी चिकित्सा टीम आपके प्रियजन को सावधानीपूर्वक देख रही है और जानकारी एकत्र करते समय उत्कृष्ट सहायक देखभाल प्रदान कर रही है।"
                }
            }
        }

# Example usage
if __name__ == "__main__":
    agent = FamilyCommunicationAgent()
    
    # Sample patient data and assessment
    patient_data = {"subject_id": 10006, "age": 65, "gender": "M"}
    assessment = {
        "risk_score": 85,
        "primary_concern": "sepsis",
        "clinical_flags": ["elevated_lactate", "tachycardia"],
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    family_comm = agent.generate_family_summary(patient_data, assessment)
    print("Family Communication Generated:")
    print(f"Confidence: {family_comm.confidence_level.value}")
    print(f"English: {family_comm.hopeful_message['en']}")
    print(f"Hindi: {family_comm.hopeful_message['hi']}")