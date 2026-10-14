"""
Deterministic, versioned clinical triage rules engine.
Rules version: triage_rules_v1.0.0
Educational prototype - Not a clinical diagnosis device.
"""
import re
from typing import List, Dict, Any, Tuple

RULES_VERSION = "triage_rules_v1.0.0"

# Strict red-flag keyword triggers (multilingual: English, Hindi, Hinglish)
RED_FLAG_PATTERNS = [
    # Chest & Cardiac
    (r"\b(chest\s+pain|chest\s+tightness|chest\s+pressure|heart\s+attack|sine\s+me\s+dard|seene\s+mein\s+dard|chhati\s+me\s+dard)\b", "Severe chest pain / pressure (cardiac risk)"),
    # Respiratory
    (r"\b(breathlessness|shortness\s+of\s+breath|difficulty\s+breathing|can'?t\s+breathe|gasping|saans\s+phoolna|saans\s+lene\s+me\s+takleef|blue\s+lips|cyanosis)\b", "Respiratory distress / breathlessness"),
    # Neurological & Stroke
    (r"\b(faint(ed|ing)?|loss\s+of\s+consciousness|unconscious|behosh|chakkar\s+aake\s+gir\s+gaye)\b", "Syncope / loss of consciousness"),
    (r"\b(face\s+droop|facial\s+droop|arm\s+weakness|slurred\s+speech|stroke|paralysis|ek\s+taraf\s+kamzori)\b", "Potential acute stroke symptoms (FAST signs)"),
    (r"\b(confusion|disoriented|not\s+recognizing|hallucinat(ion|ing)|unresponsive)\b", "Acute confusion / altered mental status"),
    (r"\b(thunderclap|worst\s+headache\s+of\s+life|sudden\s+severe\s+headache)\b", "Sudden severe thunderclap headache"),
    (r"(stiff\s+neck.*fever|fever.*stiff\s+neck|gardan\s+jakadna|nuchal\s+rigidity)", "Meningismus / fever with neck stiffness"),
    # Bleeding & Trauma
    (r"\b(severe\s+bleeding|heavy\s+bleeding|uncontrolled\s+bleeding|khoon\s+behna|khun\s+nikal\s+raha)\b", "Severe or uncontrolled hemorrhage"),
    (r"\b(coughing\s+(up\s+)?blood|hemoptysis|khoon\s+ki\s+ulti|vomiting\s+blood|hematemesis)\b", "Internal bleeding / hemoptysis / hematemesis"),
    # Allergic & Anaphylaxis
    (r"\b(anaphylaxis|swollen\s+tongue|throat\s+closing|gala\s+band\s+hona|severe\s+allergic\s+reaction)\b", "Anaphylaxis / airway obstruction"),
    # Extreme Pain / Abdomen
    (r"\b(severe\s+abdominal\s+pain|rigid\s+abdomen|pet\s+me\s+tez\s+dard)\b", "Acute acute abdomen / severe abdominal pain"),
    # Extreme Vitals
    (r"\b(fever\s+above\s+104|temp\s+>40|temperature\s+40|hyperpyrexia)\b", "Hyperpyrexia (fever >= 40°C / 104°F)"),
    (r"\b(seizure|convulsion|daura\s+padna|fits)\b", "Acute seizure / convulsion"),
    (r"\b(suicid(al|e)|kill\s+myself|self\s+harm)\b", "Psychiatric emergency / crisis"),
    (r"\b(snake\s+bite|poison(ing)?|zehar)\b", "Toxic ingestion / envenomation")
]

# Mild / Routine condition keywords
PROMPT_CARE_PATTERNS = [
    (r"\b(high\s+fever|fever\s+(for\s+)?(3|4|5|several)\s+days|vomiting\s+repeatedly|persistent\s+vomiting)\b", "Persistent fever or intractable vomiting"),
    (r"\b(deep\s+cut|burn|fracture\s+suspected|unable\s+to\s+walk)\b", "Significant trauma requiring prompt clinical care"),
    (r"\b(urinary\s+pain|blood\s+in\s+urine|kidney\s+pain)\b", "Acute urinary complaint"),
    (r"\b(rash\s+spreading|severe\s+ear\s+pain)\b", "Spreading rash or acute otalgia")
]

ROUTINE_CONSULT_PATTERNS = [
    (r"\b(mild\s+fever|fever\s+since\s+yesterday|bukhar|body\s+ache|badan\s+dard)\b", "Mild fever / body ache"),
    (r"\b(cough|cold|runny\s+nose|sore\s+throat|gala\s+kharash|khasi|zukam)\b", "Upper respiratory symptoms / common cold"),
    (r"\b(headache|mild\s+headache|sir\s+dard|sar\s+dard)\b", "Mild or episodic headache"),
    (r"\b(acidity|heartburn|gas|indigestion|pet\s+kharab|kabz|loose\s+motion)\b", "Gastrointestinal discomfort / dyspepsia / mild diarrhea")
]


def evaluate_symptoms(text: str) -> Dict[str, Any]:
    """
    Deterministic triage algorithm.
    Returns:
    - outcome: emergency | prompt_care | routine_consult | self_care_info
    - red_flags: List of detected flags
    - guidance: Clinical safety guidance
    - follow_up_questions: List of deterministic follow-up inquiries
    - rules_version: string version
    """
    cleaned = text.lower().strip()
    detected_red_flags: List[str] = []

    # 1. Check Red Flags First
    for pattern, label in RED_FLAG_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            detected_red_flags.append(label)

    if detected_red_flags:
        return {
            "outcome": "emergency",
            "red_flags": detected_red_flags,
            "guidance": (
                "🚨 CRITICAL WARNING: Potential emergency indicators detected. "
                "Do NOT wait. Call 112 immediately or proceed to the nearest emergency department. "
                "Keep the patient resting and do not offer oral food or heavy medication pending emergency evaluation."
            ),
            "follow_up_questions": [
                "Is the patient conscious, breathing and able to respond?",
                "Has an emergency ambulance (112) or responder been dispatched?",
                "Are emergency contacts alerted?"
            ],
            "rules_version": RULES_VERSION
        }

    # 2. Check Prompt Care
    prompt_triggers: List[str] = []
    for pattern, label in PROMPT_CARE_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            prompt_triggers.append(label)

    if prompt_triggers:
        return {
            "outcome": "prompt_care",
            "red_flags": [],
            "guidance": (
                "Prompt clinical attention recommended within 6 to 12 hours. "
                "Visit a clinic or primary healthcare centre for clinical examination. "
                "If any red-flag symptoms develop (such as shortness of breath, chest pain, or fainting), seek immediate emergency care."
            ),
            "follow_up_questions": [
                "How many days have these symptoms been present?",
                "Is the patient able to retain oral fluids?",
                "Has the temperature or pain intensity increased over the past 6 hours?"
            ],
            "rules_version": RULES_VERSION
        }

    # 3. Check Routine Consult
    routine_triggers: List[str] = []
    for pattern, label in ROUTINE_CONSULT_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            routine_triggers.append(label)

    if routine_triggers:
        return {
            "outcome": "routine_consult",
            "red_flags": [],
            "guidance": (
                "Schedule a routine consultation with a registered medical practitioner. "
                "Stay well hydrated, rest adequately, and monitor temperature and vitals. "
                "Never hesitate to consult a doctor if symptoms worsen or do not improve within 48 hours."
            ),
            "follow_up_questions": [
                "Have you taken any over-the-counter paracetamol or antacids?",
                "Are you experiencing any other symptoms like chills or nausea?",
                "Do you have pre-existing conditions like diabetes or hypertension?"
            ],
            "rules_version": RULES_VERSION
        }

    # 4. Unknown / Missing / Mild
    # Conservative fallback: If input is vague or unknown, recommend consultation
    return {
        "outcome": "self_care_info",
        "red_flags": [],
        "guidance": (
            "Mild symptoms reported. Maintain oral hydration, rest, and observe symptoms. "
            "Please consult a certified healthcare professional if symptoms persist or cause discomfort. "
            "If any warning signs such as chest pain or breathing difficulty arise, call 112 immediately."
        ),
        "follow_up_questions": [
            "Can you describe when these symptoms started and how severe they are?",
            "Are there any specific activities or foods that aggravate the feeling?",
            "Are there any other sensations like dizziness, sweating, or pain?"
        ],
        "rules_version": RULES_VERSION
    }
