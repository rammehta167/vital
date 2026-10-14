// Multilingual Dictionary (English / Hindi)
const I18N = {
  en: {
    app_title: "AI Healthcare Companion",
    subtitle: "Smart Vital Tracker & Emergency Response System",
    disclaimer: "Educational prototype. Not a certified medical device. Readings are simulated estimates. Never diagnose or prescribe. For real emergencies call 112.",
    tab_dashboard: "Live Dashboard",
    tab_history: "Vital History",
    tab_alerts: "Emergency Alerts",
    tab_simulator: "Simulator Control",
    tab_medicines: "Medications",
    tab_symptoms: "Symptom Triage",
    tab_summary: "AI Doctor Summary",
    tab_emergency_id: "Emergency ID (QR)",
    tab_reports: "Lab Reports",
    tab_admin: "Admin / System",
    logout: "Log Out",
    pulse: "Pulse (Heart Rate)",
    spo2: "Blood Oxygen (SpO2)",
    temperature: "Body Temp",
    signal_quality: "Signal Quality",
    device_status: "Device State",
    simulated_estimate: "simulated estimate",
    no_finger: "No Finger Detected",
    poor_signal: "Poor / Noisy Signal",
    stale_data: "STALE (No data >10s)",
    offline: "OFFLINE",
    sos_button: "EMERGENCY SOS",
    sos_subtext: "Press in acute emergency to notify all family & emergency responders immediately.",
    start_sim: "Start Sensor Feed",
    stop_sim: "Pause Sensor Feed",
    select_scenario: "Hardware Simulation Scenario:",
    normal_rest: "1. Normal Rest (65-85 BPM, 97-99% SpO2)",
    exercise: "2. Physical Exercise (110-140 BPM)",
    fever: "3. High Fever (38.5-39.5°C, elevated pulse)",
    low_oxygen: "4. Low Oxygen Hypoxia (88-92% SpO2)",
    high_pulse: "5. Sustained High Pulse (>130 BPM >=30s)",
    scenario_no_finger: "6. No Finger On Sensor (null readings)",
    scenario_poor_signal: "7. Poor Signal / Sensor Artifact Noise",
    scenario_offline: "8. Device Offline (transmission drops)",
    scenario_network_fail: "9. Network Drop (Buffer locally, bulk upload on reconnect)",
    scenario_sos: "10. Hardware SOS Button Pressed",
    scenario_fall: "11. Fall Detected (triaxial impact >3.5g)",
    warning_modal_title: "Potential Abnormal Vital Detected",
    cancel_warning_btn: "I am fine / Cancel Alert"
  },
  hi: {
    app_title: "एआई स्वास्थ्य साथी",
    subtitle: "स्मार्ट वाइटल ट्रैकर एवं आपातकालीन प्रतिक्रिया प्रणाली",
    disclaimer: "शैक्षणिक प्रोटोटाइप। यह प्रमाणित चिकित्सा उपकरण नहीं है। सभी आंकड़े अनुमानित हैं। वास्तविक आपात स्थिति में 112 डायल करें।",
    tab_dashboard: "लाइव डैशबोर्ड",
    tab_history: "वाइटल इतिहास",
    tab_alerts: "आपातकालीन अलर्ट",
    tab_simulator: "सिमुलेटर नियंत्रण",
    tab_medicines: "दवाएं व अनुपालन",
    tab_symptoms: "लक्षण जांच",
    tab_summary: "एआई डॉक्टर सारांश",
    tab_emergency_id: "इमरजेंसी मेडिकल आईडी (QR)",
    tab_reports: "जांच रिपोर्ट्स",
    tab_admin: "प्रशासन / प्रणाली",
    logout: "लॉग आउट",
    pulse: "नाड़ी दर (पल्स)",
    spo2: "रक्त ऑक्सीजन (SpO2)",
    temperature: "शरीर का तापमान",
    signal_quality: "सिग्नल गुणवत्ता",
    device_status: "डिवाइस स्थिति",
    simulated_estimate: "अनुमानित सिमुलेशन",
    no_finger: "सेंसर पर उंगली नहीं है",
    poor_signal: "कमजोर सिग्नल / शोर",
    stale_data: "डेटा रुका हुआ है (>10s)",
    offline: "ऑफलाइन",
    sos_button: "आपातकालीन SOS बटन",
    sos_subtext: "गंभीर आपात स्थिति में तुरंत परिजनों एवं 112 को सूचित करने के लिए दबाएं।",
    start_sim: "सेंसर चालू करें",
    stop_sim: "सेंसर रोकें",
    select_scenario: "हार्डवेयर सिमुलेशन परिदृश्य:",
    normal_rest: "1. सामान्य विश्राम (65-85 BPM, 97-99% SpO2)",
    exercise: "2. व्यायाम / दौड़ (110-140 BPM)",
    fever: "3. तेज बुखार (38.5-39.5°C)",
    low_oxygen: "4. कम ऑक्सीजन स्तर (88-92% SpO2)",
    high_pulse: "5. निरंतर उच्च नाड़ी दर (>130 BPM >=30s)",
    scenario_no_finger: "6. उंगली नहीं हटाई गई (शून्य मान)",
    scenario_poor_signal: "7. कमजोर सिग्नल / अत्यधिक गति",
    scenario_offline: "8. डिवाइस ऑफलाइन",
    scenario_network_fail: "9. नेटवर्क विफलता (स्थानीय बफरिंग व बल्क सिंक)",
    scenario_sos: "10. हार्डवेयर SOS बटन दबाया गया",
    scenario_fall: "11. गिरना पहचाना गया (गिरावट सेंसर चेतावनी)",
    warning_modal_title: "असामान्य वाइटल संकेत पहचाना गया",
    cancel_warning_btn: "मैं ठीक हूँ / चेतावनी रद्द करें"
  }
};

let currentLang = localStorage.getItem("app_lang") || "en";

function setLanguage(lang) {
  if (I18N[lang]) {
    currentLang = lang;
    localStorage.setItem("app_lang", lang);
    applyTranslations();
  }
}

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || I18N["en"][key] || key;
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (key && t(key)) {
      el.textContent = t(key);
    }
  });

  const langBtn = document.getElementById("langToggleBtn");
  if (langBtn) {
    langBtn.textContent = currentLang === "en" ? "हिन्दी" : "English";
  }
}
