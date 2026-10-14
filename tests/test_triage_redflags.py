from backend.app.services.triage_rules import evaluate_symptoms

# Test suite with 25 distinct red flag test cases across English, Hindi, and Hinglish
RED_FLAG_TEST_CASES = [
    # 1. Chest & Cardiac
    "I am experiencing severe chest pain and pressure on my left arm.",
    "Dad has crushing chest tightness and heavy sweating.",
    "Patient suspects a heart attack with chest pressure.",
    "Sine me dard ho raha hai aur paseena aa raha hai.",
    "Mere chhati me dard hai bohot tez.",
    "Seene mein dard mehsus ho raha hai.",

    # 2. Respiratory & Oxygenation
    "Sudden extreme breathlessness while sitting down.",
    "Patient has acute shortness of breath and blue lips.",
    "I can't breathe and my throat feels constricted.",
    "Saans lene me takleef ho rahi hai aur ghutan lag rahi hai.",
    "Saans phoolna bohot zyada badh gaya hai.",
    "Cyanosis observed around fingers and lips.",

    # 3. Neurological & Stroke
    "Patient fainted suddenly on the kitchen floor.",
    "Complete loss of consciousness for two minutes.",
    "Grandma has sudden face droop and right arm weakness.",
    "Sudden slurred speech and stroke symptoms.",
    "Sudden thunderclap headache, worst headache of life.",
    "Behosh ho gaye the thodi der pehle.",
    "Chakkar aake gir gaye aur unconscious ho gaye.",
    "Ek taraf kamzori aa gayi hai aur bol nahi pa rahe.",

    # 4. Severe Hemorrhage & Trauma
    "Patient is coughing up blood in large amounts.",
    "Severe uncontrolled bleeding from leg wound.",
    "Khooni ulti ho rahi hai (vomiting blood).",

    # 5. Meningismus & Infection
    "High fever with stiff neck and inability to touch chin to chest.",
    "Fever above 104 with violent convulsions."
]


def test_triage_redflags_suite_all_escalate_to_emergency():
    assert len(RED_FLAG_TEST_CASES) >= 20, "Must have >= 20 test cases"

    for idx, case in enumerate(RED_FLAG_TEST_CASES, 1):
        result = evaluate_symptoms(case)
        assert result["outcome"] == "emergency", (
            f"Case #{idx} FAILED to escalate to emergency: '{case}'. Got: '{result['outcome']}'"
        )
        assert len(result["red_flags"]) > 0, f"Case #{idx} returned empty red_flags"
        assert "112" in result["guidance"], f"Case #{idx} guidance missing emergency call 112"


def test_triage_mild_and_routine_do_not_escalate_to_emergency():
    cold_case = "I have a mild runny nose and sneezing since yesterday."
    res = evaluate_symptoms(cold_case)
    assert res["outcome"] != "emergency"
    assert res["outcome"] in ("routine_consult", "self_care_info")

    acidity_case = "Mild acidity and heartburn after spicy dinner."
    res_acid = evaluate_symptoms(acidity_case)
    assert res_acid["outcome"] != "emergency"
