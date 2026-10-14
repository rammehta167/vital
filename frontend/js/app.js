// Main Application Controller
let activeWarningTimer = null;
let warningCountdownVal = 15;
let currentCandidateId = null;
let currentRole = "patient";

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Initialize Theme & Language
  initTheme();
  applyTranslations();

  // 2. Setup Navigation Tabs
  setupNavigation();

  // 3. Initialize Demo Login Session (Respects selected role or defaults to patient)
  const savedRole = localStorage.getItem("current_role") || "patient";
  try {
    const userRes = await API.getMe();
    if (userRes && userRes.role) {
      updateUserBadge(userRes);
      localStorage.setItem("current_role", userRes.role);
    } else {
      const loginRes = await API.demoLogin(savedRole);
      updateUserBadge(loginRes.user);
    }
  } catch (err) {
    const loginRes = await API.demoLogin(savedRole);
    updateUserBadge(loginRes.user);
  }

  // 4. Initialize Charts
  const vitalCanvas = document.getElementById("liveVitalChart");
  if (vitalCanvas) ChartsManager.initLiveVitalChart(vitalCanvas);

  const ecgCanvas = document.getElementById("liveECGChart");
  if (ecgCanvas) ChartsManager.initLiveECGChart(ecgCanvas);

  // 5. Connect Real-time Stream
  StreamManager.init({
    onReading: handleLiveReading,
    onAlert: handleAlertCreated,
    onAutoWarning: handleAutoWarningCandidate,
    onAutoWarningCancelled: handleAutoWarningCancelled
  });

  // 6. Initial Data Load for Views
  refreshDashboard();
  setupEventListeners();
  checkSystemStatus();
});

// Theme Management
// Theme Management
function initTheme() {
  const saved = localStorage.getItem("app_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  document.documentElement.classList.toggle("dark", saved === "dark");
  const themeBtn = document.getElementById("themeToggleBtn");
  if (themeBtn) {
    themeBtn.textContent = saved === "dark" ? "☀️" : "🌙";
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  document.documentElement.classList.toggle("dark", next === "dark");
  localStorage.setItem("app_theme", next);
  const themeBtn = document.getElementById("themeToggleBtn");
  if (themeBtn) themeBtn.textContent = next === "dark" ? "☀️" : "🌙";
}

// Monitored Patient Global State (Always Ramesh Sharma for demo & viva)
const MONITORED_PATIENT = {
  name: "Ramesh Sharma",
  age: 68,
  gender: "Male",
  blood_group: "B+",
  allergies: "Penicillin",
  chronic_conditions: "Hypertension, Mild Type-2 Diabetes",
  caregiver: "Priya Sharma (+91 94250 98765)",
  physician: "Dr. Alok Mehta, MD",
  id: "#PT-2026-RS"
};

// User Profile & Role Badge
function updateUserBadge(user) {
  currentRole = user.role;
  applyRolePermissions(user.role);
}

// Role-Based Screen Adaptations & Data Minimization
function applyRolePermissions(role) {
  currentRole = role;

  const roleMeta = {
    patient: {
      userName: "Ramesh Sharma",
      roleLabel: "Patient",
      roleContext: "Patient Self-Care Mode",
      avatarText: "RS",
      patientCardContext: "Self-Care Vital Telemetry • Monitored by Caregiver Priya & Dr. Mehta",
      statusPill: "🟢 PATIENT SELF-CARE",
      statusClass: "bg-emerald-100 text-emerald-800",
      reassuranceNote: "Ramesh's heart rate, blood oxygen, and body temperature are within normal resting ranges.",
      bannerClass: "w-full p-4 rounded-2xl bg-emerald-50 text-emerald-950 border border-emerald-200 flex flex-wrap items-center justify-between gap-3 shadow-sm transition-all duration-300",
      bannerIcon: "self_improvement",
      bannerIconClass: "material-symbols-outlined text-emerald-600 text-[26px]",
      bannerTitle: "Personal Telemetry & Self-Care Dashboard",
      bannerSubtitle: "Your wearable is transmitting live pulse, blood oxygen, and body temperature. Monitored by Priya Sharma & Dr. Mehta.",
      bannerBadge: "PATIENT ACTIVE",
      bannerBadgeClass: "px-3 py-1 rounded-full bg-emerald-200 text-emerald-900 font-bold text-xs uppercase tracking-wide",
      heroName: "Ramesh V. (You)",
      avatarInitials: "RV",
      avatarGradient: "w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white flex items-center justify-center font-headline-md text-headline-md font-extrabold shadow-[0_12px_30px_-6px_rgba(16,185,129,0.4)]",
      demographicsLine: `<span><strong>Age:</strong> 68 Yrs (Male)</span> <span class="text-surface-dim">•</span> <span><strong>Blood Group:</strong> <span class="text-primary font-bold">B+ Positive</span></span> <span class="text-surface-dim">•</span> <span><strong>Caregiver:</strong> Priya Sharma (Daughter)</span> <span class="text-surface-dim">•</span> <span><strong>Attending MD:</strong> Dr. Alok Mehta, MD</span>`,
      sosHeader: `<span class="material-symbols-outlined text-[15px]">fmd_bad</span> INSTANT SOS RELAY`,
      sosButtonText: "Hold 2s for 112 SOS",
      sosSubtitle: "Protected against accidental single taps (Hold 2s to confirm dispatch)"
    },
    caregiver: {
      userName: "Priya Sharma",
      roleLabel: "Caregiver",
      roleContext: "Caregiver Ward & Home Watchline",
      avatarText: "PS",
      patientCardContext: "Monitoring Father: Ramesh V. (68 Yrs) • Safe Perimeter & Fall Sense Active",
      statusPill: "🟣 CAREGIVER SUPERVISION",
      statusClass: "bg-purple-100 text-purple-900 font-bold",
      reassuranceNote: "Geofence perimeter armed (0.4 mi radius). Fall sense IMU normal (0.02G).",
      bannerClass: "w-full p-4 rounded-2xl bg-purple-50 text-purple-950 border border-purple-200 flex flex-wrap items-center justify-between gap-3 shadow-sm transition-all duration-300",
      bannerIcon: "family_restroom",
      bannerIconClass: "material-symbols-outlined text-purple-600 text-[26px]",
      bannerTitle: "Caregiver Ward & Home Watchline — Monitoring Father Ramesh V.",
      bannerSubtitle: "Continuous perimeter and fall sensing active. Medication adherence tracked with family diary.",
      bannerBadge: "CAREGIVER SUPERVISION",
      bannerBadgeClass: "px-3 py-1 rounded-full bg-purple-200 text-purple-900 font-bold text-xs uppercase tracking-wide",
      heroName: "Ramesh Sharma (Father)",
      avatarInitials: "RS",
      avatarGradient: "w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white flex items-center justify-center font-headline-md text-headline-md font-extrabold shadow-[0_12px_30px_-6px_rgba(147,51,234,0.4)]",
      demographicsLine: `<span><strong>Relationship:</strong> Father (Caregiver: Priya)</span> <span class="text-surface-dim">•</span> <span><strong>Age:</strong> 68 Yrs</span> <span class="text-surface-dim">•</span> <span><strong>Perimeter:</strong> Inside Safe Zone</span> <span class="text-surface-dim">•</span> <span><strong>Fall Sensor:</strong> 0.02G (Normal)</span>`,
      sosHeader: `<span class="material-symbols-outlined text-[15px]">emergency</span> CAREGIVER EMERGENCY RELAY`,
      sosButtonText: "Hold 2s: Call 112 Ambulance",
      sosSubtitle: "Dispatches Jabalpur 112 emergency services and notifies Dr. Mehta"
    },
    doctor: {
      userName: "Dr. Alok Mehta, MD",
      roleLabel: "Attending Physician",
      roleContext: "Attending Cardiologist Dossier",
      avatarText: "AM",
      patientCardContext: "Clinical Telemetry Dossier • Attending: Dr. Alok Mehta, MD (Cardiology)",
      statusPill: "🔵 PHYSICIAN MONITORED",
      statusClass: "bg-blue-100 text-blue-900 font-bold",
      reassuranceNote: "Dual-wavelength SpO2 and ECG telemetry active. PI 4.2% nominal.",
      bannerClass: "w-full p-4 rounded-2xl bg-blue-50 text-blue-950 border border-blue-200 flex flex-wrap items-center justify-between gap-3 shadow-sm transition-all duration-300",
      bannerIcon: "stethoscope",
      bannerIconClass: "material-symbols-outlined text-blue-600 text-[26px]",
      bannerTitle: "Attending Physician Console — Dr. Alok Mehta, MD (Cardiology)",
      bannerSubtitle: "Continuous Lead II ECG, dual-band plethysmography, and Rx titration monitoring.",
      bannerBadge: "CLINICAL DOSSIER",
      bannerBadgeClass: "px-3 py-1 rounded-full bg-blue-200 text-blue-900 font-bold text-xs uppercase tracking-wide",
      heroName: "Ramesh Sharma (#PT-2026-RS)",
      avatarInitials: "RS",
      avatarGradient: "w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-700 text-white flex items-center justify-center font-headline-md text-headline-md font-extrabold shadow-[0_12px_30px_-6px_rgba(37,99,235,0.4)]",
      demographicsLine: `<span><strong>Diagnosis:</strong> Stage 1 HTN, Mild T2D</span> <span class="text-surface-dim">•</span> <span><strong>Rx:</strong> Telmisartan 40mg PO</span> <span class="text-surface-dim">•</span> <span><strong>Allergy:</strong> <strong class="text-error">Penicillin (Severe)</strong></span> <span class="text-surface-dim">•</span> <span><strong>Attending:</strong> Dr. Mehta</span>`,
      sosHeader: `<span class="material-symbols-outlined text-[15px]">medical_services</span> CLINICAL CODE ESCALATION`,
      sosButtonText: "Hold 2s: Code Escalation",
      sosSubtitle: "Triggers priority hospital transport and routes telemetry to CCU"
    },
    responder: {
      userName: "Asha",
      roleLabel: "EMT Jabalpur / Responder",
      roleContext: "Emergency Field Responder Mode",
      avatarText: "A",
      patientCardContext: "Field Emergency Triage • Monitored Patient: Ramesh V. (Ward 4)",
      statusPill: "🔴 FIELD RESPONDER ACTIVE",
      statusClass: "bg-error-container text-on-error-container font-extrabold",
      reassuranceNote: "Priority Incident Channel: High-contrast triage active. Private home diaries filtered for privacy.",
      bannerClass: "w-full p-4 rounded-2xl bg-rose-50 text-rose-950 border-2 border-rose-400 flex flex-wrap items-center justify-between gap-3 shadow-md transition-all duration-300",
      bannerIcon: "emergency",
      bannerIconClass: "material-symbols-outlined text-rose-600 text-[26px] animate-pulse",
      bannerTitle: "Emergency Field Responder Triage — Asha (EMT Lead)",
      bannerSubtitle: "Priority Incident Channel active. Non-emergency private diaries filtered for data minimization.",
      bannerBadge: "CODE AMBER TRIAGE",
      bannerBadgeClass: "px-3 py-1 rounded-full bg-rose-600 text-white font-extrabold text-xs uppercase tracking-wide",
      heroName: "Ramesh Sharma (Incident Patient)",
      avatarInitials: "EM",
      avatarGradient: "w-20 h-20 rounded-2xl bg-gradient-to-br from-rose-600 to-red-700 text-white flex items-center justify-center font-headline-md text-headline-md font-extrabold shadow-[0_12px_30px_-6px_rgba(225,29,72,0.4)]",
      demographicsLine: `<span><strong>TRIAGE:</strong> <strong class="text-rose-700">CODE AMBER</strong></span> <span class="text-surface-dim">•</span> <span><strong>CRITICAL ALLERGY:</strong> <strong class="text-error">PENICILLIN (ANAPHYLAXIS)</strong></span> <span class="text-surface-dim">•</span> <span><strong>Blood:</strong> B+</span> <span class="text-surface-dim">•</span> <span><strong>Scene:</strong> Jabalpur Ward 4</span>`,
      sosHeader: `<span class="material-symbols-outlined text-[15px]">local_shipping</span> ON-SCENE DISPATCH ACKNOWLEDGE`,
      sosButtonText: "Hold 2s: Mark Scene Arrival",
      sosSubtitle: "Transmits verified on-scene timestamp to central 112 dispatch server"
    },
    admin: {
      userName: "System Administrator",
      roleLabel: "System Admin",
      roleContext: "Telemetry Infrastructure & Audit Control",
      avatarText: "SA",
      patientCardContext: "Station Node 04-B • BLE Mesh Core Diagnostics",
      statusPill: "⚙️ MESH ADMIN ACTIVE",
      statusClass: "bg-surface-container-high text-on-surface font-bold",
      reassuranceNote: "BLE Mesh online (4 nodes connected). Sampling frequency locked at 250 Hz.",
      bannerClass: "w-full p-4 rounded-2xl bg-slate-100 text-slate-900 border border-slate-300 flex flex-wrap items-center justify-between gap-3 shadow-sm transition-all duration-300",
      bannerIcon: "settings_suggest",
      bannerIconClass: "material-symbols-outlined text-slate-700 text-[26px]",
      bannerTitle: "Telemetry Infrastructure & BLE Mesh Diagnostics Console",
      bannerSubtitle: "4 nodes connected. Sampling locked at 250 Hz. Continuous audit logger and simulator controls active.",
      bannerBadge: "ADMINISTRATOR",
      bannerBadgeClass: "px-3 py-1 rounded-full bg-slate-300 text-slate-900 font-bold text-xs uppercase tracking-wide",
      heroName: "Telemetry Node 04-B (Subject: Ramesh Sharma)",
      avatarInitials: "SA",
      avatarGradient: "w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-700 to-zinc-900 text-white flex items-center justify-center font-headline-md text-headline-md font-extrabold shadow-[0_12px_30px_-6px_rgba(51,65,85,0.4)]",
      demographicsLine: `<span><strong>Firmware:</strong> ESP32 v2.4.1</span> <span class="text-surface-dim">•</span> <span><strong>Sensor Lead:</strong> MAX30102 Optical</span> <span class="text-surface-dim">•</span> <span><strong>Sample Rate:</strong> 250 Hz Continuous</span> <span class="text-surface-dim">•</span> <span><strong>RSSI:</strong> -58 dBm</span>`,
      sosHeader: `<span class="material-symbols-outlined text-[15px]">terminal</span> DIAGNOSTIC TEST DISPATCH`,
      sosButtonText: "Hold 2s: Trigger Pipeline Test",
      sosSubtitle: "Simulates full 5-stage dispatch state machine loop with audit timestamping"
    }
  };

  const meta = roleMeta[role] || roleMeta.patient;

  // 1. Update Header Badges & Pill
  const badge = document.getElementById("currentUserBadge");
  if (badge) badge.textContent = `${meta.userName} (${meta.roleLabel.toUpperCase()})`;

  const avatar = document.getElementById("currentUserAvatarText");
  if (avatar) avatar.textContent = meta.avatarText;

  const roleContextPill = document.getElementById("roleContextTag");
  if (roleContextPill) roleContextPill.textContent = meta.roleContext;

  const statusPillEl = document.getElementById("roleStatusPill");
  if (statusPillEl) {
    statusPillEl.textContent = meta.statusPill;
    statusPillEl.className = `px-3 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1.5 ${meta.statusClass}`;
  }

  const patientContextEl = document.getElementById("patientCardContext");
  if (patientContextEl) patientContextEl.textContent = meta.patientCardContext;

  const reassuranceEl = document.getElementById("calmHeroSubtitle");
  if (reassuranceEl) reassuranceEl.textContent = meta.reassuranceNote;

  // 2. Update Dynamic Role Alert Banner
  const alertBanner = document.getElementById("roleAlertBanner");
  if (alertBanner && meta.bannerClass) alertBanner.className = meta.bannerClass;

  const bannerIcon = document.getElementById("roleBannerIcon");
  if (bannerIcon) {
    bannerIcon.textContent = meta.bannerIcon;
    bannerIcon.className = meta.bannerIconClass;
  }

  const bannerTitle = document.getElementById("roleBannerTitle");
  if (bannerTitle) bannerTitle.textContent = meta.bannerTitle;

  const bannerSubtitle = document.getElementById("roleBannerSubtitle");
  if (bannerSubtitle) bannerSubtitle.textContent = meta.bannerSubtitle;

  const bannerBadge = document.getElementById("roleBannerBadge");
  if (bannerBadge) {
    bannerBadge.textContent = meta.bannerBadge;
    bannerBadge.className = meta.bannerBadgeClass;
  }

  // 3. Update Patient Hero Card
  const heroNameEl = document.getElementById("patientHeaderName");
  if (heroNameEl) heroNameEl.textContent = meta.heroName;

  const avatarBoxEl = document.getElementById("patientAvatarBox");
  if (avatarBoxEl && meta.avatarGradient) avatarBoxEl.className = meta.avatarGradient;

  const avatarInitialsEl = document.getElementById("patientAvatarInitials");
  if (avatarInitialsEl) avatarInitialsEl.textContent = meta.avatarInitials;

  const demoLineEl = document.getElementById("patientDemographicsLine");
  if (demoLineEl && meta.demographicsLine) demoLineEl.innerHTML = meta.demographicsLine;

  const sosHeaderEl = document.getElementById("sosActionHeader");
  if (sosHeaderEl && meta.sosHeader) sosHeaderEl.innerHTML = meta.sosHeader;

  const sosBtnTextEl = document.getElementById("sosButtonText");
  if (sosBtnTextEl && meta.sosButtonText) sosBtnTextEl.textContent = meta.sosButtonText;

  const sosBtnSubtitleEl = document.getElementById("sosButtonSubtitle");
  if (sosBtnSubtitleEl && meta.sosSubtitle) sosBtnSubtitleEl.textContent = meta.sosSubtitle;

  // 4. Adjust Sidebar Tabs based on Role (Data Minimization for Responder)
  const restrictedTabs = ["tab-medicines", "tab-summary", "tab-reports", "tab-admin"];
  const sidebarNav = document.getElementById("sidebarNavigation");

  if (sidebarNav) {
    sidebarNav.querySelectorAll(".tab-btn").forEach(btn => {
      const tab = btn.getAttribute("data-tab");
      if (role === "responder" && restrictedTabs.includes(tab)) {
        btn.style.display = "none";
      } else {
        btn.style.display = "flex";
      }
    });
  }

  // If responder is active and current active tab is restricted, bounce to dashboard
  const activeTabContent = document.querySelector(".tab-content.active");
  if (role === "responder" && activeTabContent && restrictedTabs.includes(activeTabContent.id)) {
    switchTab("tab-dashboard");
  }

  // 5. Adjust Section 5 Operations Panel for Role
  document.querySelectorAll("[data-role-panel]").forEach(el => {
    const targetRoles = (el.getAttribute("data-role-panel") || "").split(" ");
    if (targetRoles.includes(role)) {
      el.style.display = "grid";
    } else {
      el.style.display = "none";
    }
  });

  // 6. Role-specific Toast Reassurance
  if (role === "responder") {
    showToast("Responder Mode: Emergency Triage active. Private clinical notes filtered for privacy.", "info");
  }

  // 7. Sync role dropdown
  const selector = document.getElementById("roleSelector");
  if (selector && selector.value !== role) {
    selector.value = role;
  }
}

// Navigation & Tab Switching
function setupNavigation() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Check URL hash or path for direct routing (e.g. /emergency/{token})
  const path = window.location.pathname;
  if (path.startsWith("/emergency/")) {
    const token = path.split("/emergency/")[1];
    switchTab("tab-responder-view");
    loadPublicEmergencyCard(token);
  } else if (path.startsWith("/ack/")) {
    const token = path.split("/ack/")[1];
    acknowledgeEventByUrl(token);
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  const targetContent = document.getElementById(tabId);

  if (targetBtn) targetBtn.classList.add("active");
  if (targetContent) targetContent.classList.add("active");

  // Load specific tab data
  if (tabId === "tab-history") loadHistoryData();
  if (tabId === "tab-alerts") loadAlertsData();
  if (tabId === "tab-simulator") loadSimulatorData();
  if (tabId === "tab-medicines") loadMedicinesData();
  if (tabId === "tab-summary") loadDoctorSummary();
  if (tabId === "tab-emergency-id") loadEmergencyID();
  if (tabId === "tab-reports") loadReportsData();
  if (tabId === "tab-contacts") loadContactsData();
  if (tabId === "tab-admin") loadAdminData();
}

// Live Reading Handler
function handleLiveReading(reading) {
  // Update Live Vitals Cards
  const pulseVal = document.getElementById("vitalPulseVal");
  const pulseLive = document.getElementById("pulse-live");
  const spo2Val = document.getElementById("vitalSpO2Val");
  const spo2Live = document.getElementById("spo2-live");
  const tempVal = document.getElementById("vitalTempVal");
  const tempLive = document.getElementById("temp-live");
  const tempFLive = document.getElementById("temp-f-live");
  const pulseInterval = document.getElementById("pulse-interval-live");
  const sigVal = document.getElementById("vitalSignalVal");
  const sigText = document.getElementById("signal-quality-text");
  const syncLabel = document.getElementById("sync-live-label");
  const lastUpdated = document.getElementById("lastUpdatedText");
  const devBadge = document.getElementById("deviceStatusBadge");

  const bpmText = reading.bpm !== null ? reading.bpm : "--";
  if (pulseVal) pulseVal.textContent = bpmText;
  if (pulseLive) pulseLive.textContent = bpmText;
  const metricHr = document.getElementById("metric-heart-rate");
  if (metricHr) metricHr.textContent = bpmText;

  if (reading.bpm !== null && pulseInterval) {
    const rr = Math.round(60000 / reading.bpm);
    pulseInterval.textContent = `Interval: ${rr} ms`;
  }

  const spo2Text = reading.spo2 !== null ? `${reading.spo2}` : "--";
  if (spo2Val) spo2Val.textContent = reading.spo2 !== null ? `${reading.spo2}%` : "--";
  if (spo2Live) spo2Live.textContent = spo2Text;
  const metricSpo2 = document.getElementById("metric-spo2");
  if (metricSpo2) metricSpo2.textContent = spo2Text;

  const tempText = reading.temp_c !== null ? `${reading.temp_c}` : "--";
  if (tempVal) tempVal.textContent = reading.temp_c !== null ? `${reading.temp_c}°C` : "--";
  if (tempLive) tempLive.textContent = tempText;
  const metricTemp = document.getElementById("metric-temperature");
  if (metricTemp) metricTemp.textContent = tempText;
  if (tempFLive && reading.temp_c !== null) {
    tempFLive.textContent = `${(reading.temp_c * 9/5 + 32).toFixed(1)} °F`;
  }

  // 1. Vital Status Pills (Clean, compact, non-wrapping badges)
  const pulseStatus = document.getElementById("vitalPulseStatus");
  if (pulseStatus) {
    if (reading.bpm === null) {
      pulseStatus.textContent = "Sensor Off";
      pulseStatus.className = "px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else if (reading.bpm < 55 || reading.bpm > 115) {
      pulseStatus.textContent = reading.bpm > 115 ? "Elevated (Check)" : "Low (Check)";
      pulseStatus.className = "px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else {
      pulseStatus.textContent = "Within example range";
      pulseStatus.className = "px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200/60 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    }
  }

  const spo2Status = document.getElementById("vitalSpO2Status");
  if (spo2Status) {
    if (reading.spo2 === null) {
      spo2Status.textContent = "Sensor Off";
      spo2Status.className = "px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else if (reading.spo2 < 93) {
      spo2Status.textContent = "Low (Check O2)";
      spo2Status.className = "px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else {
      spo2Status.textContent = "Within example range";
      spo2Status.className = "px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200/60 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    }
  }

  const tempStatus = document.getElementById("vitalTempStatus");
  if (tempStatus) {
    if (reading.temp_c === null) {
      tempStatus.textContent = "Sensor Off";
      tempStatus.className = "px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else if (reading.temp_c > 38.0 || reading.temp_c < 36.0) {
      tempStatus.textContent = reading.temp_c > 38.0 ? "Elevated Temp" : "Low Temp";
      tempStatus.className = "px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    } else {
      tempStatus.textContent = "Within example range";
      tempStatus.className = "px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200/60 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
    }
  }

  // 2. Signal Quality display & badges (MAX30102 PPG)
  const sigQ = (reading.signal_quality || "good").toLowerCase();
  const snrVal = document.getElementById("signalQualityPercent");
  if (sigVal) {
    if (sigQ === "no_finger") {
      sigVal.textContent = "No Finger Detected";
      sigVal.className = "px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
      if (snrVal) snrVal.textContent = "0%";
    } else if (sigQ === "poor" || sigQ === "noisy") {
      sigVal.textContent = "Motion Artifact";
      sigVal.className = "px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
      if (snrVal) snrVal.textContent = "54%";
    } else {
      sigVal.textContent = "Within example range";
      sigVal.className = "px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200/60 text-[11px] rounded-lg font-bold whitespace-nowrap shrink-0 shadow-xs";
      if (snrVal) snrVal.textContent = "98%";
    }
  }

  if (sigText) {
    if (sigQ === "no_finger") {
      sigText.textContent = "WEARABLE: NO FINGER";
    } else if (sigQ === "poor") {
      sigText.textContent = "WEARABLE: NOISY SIGNAL";
    } else {
      sigText.textContent = "HOME WIFI: 98%";
    }
  }

  if (syncLabel) {
    syncLabel.textContent = "LIVE FEED: ACTIVE";
  }

  if (lastUpdated) {
    lastUpdated.textContent = `Last reading: ${new Date(reading.measured_at).toLocaleTimeString()}`;
  }

  if (devBadge) {
    devBadge.textContent = "ONLINE (ESP32)";
    devBadge.className = "badge badge-device-online";
  }

  // 3. Update Calm Care Hero Line & Health Score Ring
  updateCalmHeroStatus(reading);
  updateHealthScore(reading);

  // 4. Push to Real-time Charts
  ChartsManager.updateLiveVitalChart(reading);

  if (reading.ecg_sample) {
    try {
      const slice = typeof reading.ecg_sample === "string" ? JSON.parse(reading.ecg_sample) : reading.ecg_sample;
      ChartsManager.updateLiveECG(slice);
    } catch(e) {}
  }
}

// Update Calm Care Hero Status Line
function updateCalmHeroStatus(reading) {
  const card = document.getElementById("calmHeroStatusCard");
  const icon = document.getElementById("calmHeroIcon");
  const title = document.getElementById("calmHeroTitle");
  const subtitle = document.getElementById("calmHeroSubtitle");
  if (!card || !title || !subtitle) return;

  const isBpmAbnormal = reading.bpm !== null && (reading.bpm < 55 || reading.bpm > 115);
  const isSpo2Abnormal = reading.spo2 !== null && reading.spo2 < 93;
  const isTempAbnormal = reading.temp_c !== null && (reading.temp_c > 38.0 || reading.temp_c < 36.0);

  if (isBpmAbnormal || isSpo2Abnormal || isTempAbnormal) {
    card.classList.add("abnormal");
    if (icon) {
      icon.textContent = "warning";
      icon.className = "material-symbols-outlined text-[28px] text-amber-600 dark:text-amber-400";
    }
    title.textContent = isSpo2Abnormal ? "Check pulse & oxygen level" : "Check vital stability";
    subtitle.textContent = "Abnormal reading detected outside target baseline. Continuous observation in progress.";
  } else {
    card.classList.remove("abnormal");
    if (icon) {
      icon.textContent = "check_circle";
      icon.className = "material-symbols-outlined text-[28px] text-emerald-600 dark:text-emerald-400";
    }
    title.textContent = "All vitals look normal";
    subtitle.textContent = "Ramesh's heart rate, blood oxygen, and body temperature are within expected resting ranges.";
  }
}

// Update Health Score Ring (0-100 Example Score)
function updateHealthScore(reading) {
  const valEl = document.getElementById("healthScoreValue");
  const circle = document.getElementById("healthScoreCircle");
  if (!valEl || !circle) return;

  let score = 96;
  if (reading.bpm !== null) {
    if (reading.bpm < 60 || reading.bpm > 100) {
      score -= Math.min(25, Math.abs(reading.bpm - 75) * 0.5);
    }
  }
  if (reading.spo2 !== null && reading.spo2 < 95) {
    score -= (95 - reading.spo2) * 5;
  }
  if (reading.temp_c !== null && (reading.temp_c > 37.3 || reading.temp_c < 36.5)) {
    score -= Math.abs(reading.temp_c - 36.8) * 12;
  }

  score = Math.max(20, Math.min(99, Math.round(score)));
  valEl.textContent = score;

  // Circumference = 2 * PI * 40 = 251.2
  const offset = 251.2 - (score / 100) * 251.2;
  circle.style.strokeDashoffset = offset;
  circle.style.stroke = score > 85 ? "var(--primary)" : (score > 65 ? "#f59e0b" : "var(--error)");
}

// Automatic Warning 15-second Grace Countdown Modal
function handleAutoWarningCandidate(candidate) {
  currentCandidateId = candidate.candidate_id;
  warningCountdownVal = candidate.countdown_seconds || 15;

  const modal = document.getElementById("autoWarningModal");
  const timerDisplay = document.getElementById("warningCountdownNumber");
  const reasonDisplay = document.getElementById("warningReasonText");

  if (reasonDisplay) {
    reasonDisplay.textContent = `Sustained abnormal vital signs detected for ${candidate.duration_secs}s: ${candidate.reason}`;
  }

  if (timerDisplay) timerDisplay.textContent = warningCountdownVal;
  if (modal) modal.classList.add("open");

  if (activeWarningTimer) clearInterval(activeWarningTimer);
  activeWarningTimer = setInterval(() => {
    warningCountdownVal -= 1;
    if (timerDisplay) timerDisplay.textContent = warningCountdownVal;

    if (warningCountdownVal <= 0) {
      clearInterval(activeWarningTimer);
      activeWarningTimer = null;
      if (modal) modal.classList.remove("open");
    }
  }, 1000);
}

function handleAutoWarningCancelled(data) {
  if (activeWarningTimer) {
    clearInterval(activeWarningTimer);
    activeWarningTimer = null;
  }
  const modal = document.getElementById("autoWarningModal");
  if (modal) modal.classList.remove("open");
  showToast("Automatic warning dismissed. You indicated you are okay.", "info");
}

async function cancelActiveWarning() {
  if (currentCandidateId) {
    await API.cancelWarning(currentCandidateId);
    handleAutoWarningCancelled();
  }
}

// Alerts & Events Handlers
function handleAlertCreated(event) {
  showToast(`🚨 ${event.title}`, "danger");
  // If alerts tab open, reload
  loadAlertsData();
}

async function acknowledgeEventByUrl(token) {
  try {
    const res = await fetch(`/api/v1/events/ack/${token}`).then(r => r.json());
    showToast(`Alert #${res.event_id} acknowledged: ${res.message}`, "success");
    switchTab("tab-alerts");
  } catch(e) {
    showToast("Failed to acknowledge alert via token", "danger");
  }
}

// Dashboard Refresh
async function refreshDashboard() {
  try {
    const latest = await API.getLatestReading();
    if (latest.reading) {
      handleLiveReading(latest.reading);
    } else {
      const devBadge = document.getElementById("deviceStatusBadge");
      if (devBadge) {
        devBadge.textContent = latest.device_status.toUpperCase();
        devBadge.className = "badge badge-device-offline";
      }
    }

    // Load next medication reminder
    const meds = await API.getMedications();
    const reminderBox = document.getElementById("nextMedicationCard");
    if (reminderBox && meds.length > 0) {
      const nextMed = meds[0];
      reminderBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="font-size:1.1rem; color:var(--text-primary);">${nextMed.name} (${nextMed.strength || ""})</strong>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">
              Scheduled: 08:30 AM &bull; ${nextMed.instructions}
            </div>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn btn-success" onclick="logMedAdherence(${nextMed.id}, 'taken')">✔ Taken</button>
            <button class="btn btn-outline" onclick="logMedAdherence(${nextMed.id}, 'snoozed')">⏰ Snooze</button>
            <button class="btn btn-danger" onclick="logMedAdherence(${nextMed.id}, 'skipped')">✖ Skip</button>
          </div>
        </div>
      `;
    }
  } catch (err) {
    console.warn("Dashboard refresh error:", err);
  }
}

// Vital History View
async function loadHistoryData(range = "day") {
  const container = document.getElementById("historyTableBody");
  const statsBox = document.getElementById("historyStatsGrid");
  try {
    const data = await API.getReadingsHistory(range);
    const stats = data.stats;

    if (statsBox) {
      statsBox.innerHTML = `
        <div class="vital-card">
          <div class="vital-title">Pulse (BPM)</div>
          <div class="vital-value" style="font-size:1.8rem;">${stats.avg_bpm || "--"} <span class="vital-unit">AVG</span></div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Min: ${stats.min_bpm || "--"} | Max: ${stats.max_bpm || "--"}</div>
        </div>
        <div class="vital-card">
          <div class="vital-title">SpO2 Oxygen (%)</div>
          <div class="vital-value" style="font-size:1.8rem;">${stats.avg_spo2 || "--"}% <span class="vital-unit">AVG</span></div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Min: ${stats.min_spo2 || "--"}% | Max: ${stats.max_spo2 || "--"}%</div>
        </div>
        <div class="vital-card">
          <div class="vital-title">Body Temp (°C)</div>
          <div class="vital-value" style="font-size:1.8rem;">${stats.avg_temp || "--"}°C <span class="vital-unit">AVG</span></div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Min: ${stats.min_temp || "--"} | Max: ${stats.max_temp || "--"}</div>
        </div>
        <div class="vital-card">
          <div class="vital-title">Total Samples</div>
          <div class="vital-value" style="font-size:1.8rem;">${stats.total_samples}</div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Window: ${data.range_label}</div>
        </div>
      `;
    }

    // Trend chart
    const trendCanvas = document.getElementById("historyTrendChart");
    if (trendCanvas) ChartsManager.initTrendChart(trendCanvas, data.readings);

    if (container) {
      container.innerHTML = data.readings.slice(-30).reverse().map(r => `
        <tr>
          <td>${new Date(r.measured_at).toLocaleString()}</td>
          <td><strong>${r.bpm !== null ? r.bpm : "--"}</strong> BPM</td>
          <td>${r.spo2 !== null ? r.spo2 + "%" : "--"}</td>
          <td>${r.temp_c !== null ? r.temp_c + "°C" : "--"}</td>
          <td><span class="vital-status-pill ${r.signal_quality === 'good' ? 'vital-status-normal' : 'vital-status-warning'}">${r.signal_quality}</span></td>
          <td><span class="vital-estimate-tag">simulated</span></td>
        </tr>
      `).join("");
    }
  } catch (err) {
    showToast("Error loading history: " + err.message, "danger");
  }
}

// Build a clean status stepper for an event: Created -> Sent -> Delivered -> Acknowledged
function buildAlertStepperHtml(status, logs = []) {
  const steps = ["created", "sent", "delivered", "acknowledged"];
  const labels = {
    created: "1. Created",
    sent: "2. Dispatched",
    delivered: "3. Delivered",
    acknowledged: "4. Acknowledged"
  };

  const statusOrder = { created: 0, sent: 1, delivered: 2, acknowledged: 3, resolved: 4, failed: 1 };
  const currentLevel = statusOrder[status] !== undefined ? statusOrder[status] : 0;
  const isFailed = status === "failed" || logs.some(l => l.status === "failed");

  return `
    <div class="alert-stepper my-3">
      ${steps.map((st, idx) => {
        let nodeClass = "step-node";
        let icon = idx + 1;
        if (status === "resolved") {
          nodeClass += " completed";
          icon = "✔";
        } else if (isFailed && idx === currentLevel) {
          nodeClass += " failed";
          icon = "✖";
        } else if (idx < currentLevel || (idx === currentLevel && status === st)) {
          nodeClass += (idx === currentLevel ? " active" : " completed");
          if (idx < currentLevel) icon = "✔";
        }
        return `
          <div class="${nodeClass}">
            <div class="step-dot">${icon}</div>
            <span class="step-label">${labels[st]}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function formatDispatchSummary(logs = []) {
  if (!logs || logs.length === 0) {
    return {
      contacts: [{ name: "Primary Care Network", role: "Kin & Attending Staff", type: "In-App Telemetry" }],
      resolvedDetail: null
    };
  }

  const contacts = [];
  logs.forEach(l => {
    const d = l.detail || "";
    if (d.includes("Priya")) contacts.push({ name: "Priya Sharma", role: "Caregiver", type: "SMS & Email" });
    else if (d.includes("Mehta")) contacts.push({ name: "Dr. Alok Mehta", role: "Attending MD", type: "SMS & Email" });
    else if (d.includes("Asha") || d.includes("112")) contacts.push({ name: "112 Ambulance", role: "EMT Lead (Asha)", type: "SMS Dispatch" });
    else if (d.includes("santosh") || d.includes("Santosh")) contacts.push({ name: "Santosh", role: "Emergency Kin", type: "SMS Dispatch" });
  });

  const uniqueContacts = [];
  const seen = new Set();
  contacts.forEach(c => {
    if (!seen.has(c.name)) {
      seen.add(c.name);
      uniqueContacts.push(c);
    }
  });

  if (uniqueContacts.length === 0) {
    uniqueContacts.push({ name: "Primary Care Network", role: "Kin & Attending Staff", type: "Multi-Channel" });
  }

  const resolvedLog = logs.find(l => l.status === "resolved");

  return {
    contacts: uniqueContacts,
    resolvedDetail: resolvedLog ? resolvedLog.detail : null
  };
}

// Alerts View
async function loadAlertsData() {
  const container = document.getElementById("alertsListContainer");
  if (!container) return;
  try {
    const events = await API.getEvents();
    if (events.length === 0) {
      container.innerHTML = `<div class="bg-surface-container-lowest p-8 rounded-2xl border border-outline-variant/30 text-center text-on-surface-variant font-medium">No active emergency alarms or alerts recorded.</div>`;
      return;
    }

    container.innerHTML = events.map(ev => {
      const isCritical = ev.severity === "critical";
      const summary = formatDispatchSummary(ev.logs);

      return `
        <div class="bg-surface-container-lowest p-5 rounded-2xl border border-outline-variant/30 shadow-xs mb-4" style="border-left: 5px solid ${isCritical ? 'var(--primary)' : '#d97706'};">
          <!-- Card Header -->
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="material-symbols-outlined text-[20px] ${isCritical ? 'text-primary' : 'text-amber-600'}">
                  ${isCritical ? 'e911_emergency' : 'warning'}
                </span>
                <h3 class="text-base font-bold text-on-surface tracking-tight">${ev.title}</h3>
              </div>
              <div class="text-xs text-on-surface-variant flex items-center gap-2">
                <span>${new Date(ev.created_at).toLocaleString([], { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}</span>
                <span>•</span>
                <span class="font-mono">ID: #${ev.id}</span>
              </div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wide ${
              ev.status === 'resolved' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' :
              ev.status === 'acknowledged' ? 'bg-blue-50 text-blue-800 border border-blue-200' :
              'bg-amber-50 text-amber-800 border border-amber-200'
            }">
              STATUS: ${ev.status.toUpperCase()}
            </span>
          </div>

          <p class="text-xs text-on-surface mb-3">${ev.description || "Emergency threshold breached on telemetry monitor."}</p>
          
          <!-- Visual Alert Stepper Pipeline -->
          ${buildAlertStepperHtml(ev.status, ev.logs)}

          <!-- Clean Verified Alert Recipients Summary -->
          <div class="bg-surface-container-low/70 rounded-xl p-3.5 border border-outline-variant/30 my-3">
            <div class="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-2.5 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px] text-emerald-600">verified</span>
              Emergency Dispatch Confirmed (${summary.contacts.length} Contacts Notified)
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              ${summary.contacts.map(c => `
                <div class="bg-surface-container-lowest p-2.5 rounded-lg border border-outline-variant/20 flex flex-col justify-between shadow-2xs">
                  <div class="flex items-center justify-between gap-1">
                    <span class="text-xs font-bold text-on-surface truncate">${c.name}</span>
                    <span class="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200/50">Delivered</span>
                  </div>
                  <div class="text-[10px] text-on-surface-variant mt-1">${c.role} • ${c.type}</div>
                </div>
              `).join('')}
            </div>

            ${summary.resolvedDetail ? `
              <div class="mt-2.5 pt-2 border-t border-outline-variant/20 text-xs text-emerald-800 flex items-center gap-1.5 font-medium">
                <span class="material-symbols-outlined text-[15px] text-emerald-600">done_all</span>
                <span>${summary.resolvedDetail}</span>
              </div>
            ` : ''}

            <!-- Collapsible Technical Carrier & Audit Trail (Accessible for Viva, Clean by Default) -->
            <details class="mt-2.5 pt-2 border-t border-outline-variant/20 text-on-surface-variant">
              <summary class="cursor-pointer text-[11px] font-semibold text-primary hover:underline flex items-center gap-1 select-none">
                <span>View Technical Audit Trail (${ev.logs.length} carrier events)</span>
              </summary>
              <div class="mt-2 p-2.5 bg-surface-container-lowest rounded-lg font-mono text-[10px] space-y-1 max-h-36 overflow-y-auto border border-outline-variant/20 text-on-surface-variant">
                ${ev.logs.map(l => `<div><strong class="text-on-surface">${l.channel.toUpperCase()}</strong> [${l.status.toUpperCase()}]: ${l.detail}</div>`).join('')}
              </div>
            </details>
          </div>

          <!-- Actions Bar -->
          <div class="flex items-center justify-between flex-wrap gap-2 pt-1">
            <div class="flex items-center gap-2">
              ${ev.map_url ? `
                <a href="${ev.map_url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-container-low hover:bg-surface-container border border-outline-variant/30 text-on-surface text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs">
                  <span class="material-symbols-outlined text-[15px] text-primary">location_on</span>
                  GPS Location
                </a>
              ` : ''}
              ${ev.ack_token && ev.status !== 'resolved' && ev.status !== 'acknowledged' ? `
                <a href="/ack/${ev.ack_token}" target="_blank" class="px-3 py-1.5 rounded-lg bg-surface-container-low hover:bg-surface-container border border-outline-variant/30 text-on-surface text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs">
                  <span class="material-symbols-outlined text-[15px] text-secondary">check</span>
                  Acknowledge
                </a>
              ` : ''}
            </div>

            <div>
              ${ev.status !== 'resolved' ? `
                <button class="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs transition-colors cursor-pointer flex items-center gap-1.5" onclick="resolveAlertPrompt(${ev.id})">
                  <span class="material-symbols-outlined text-[15px]">done_all</span>
                  Mark as Resolved
                </button>
              ` : `
                <span class="text-xs text-emerald-700 font-bold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                  <span class="material-symbols-outlined text-[15px]">check_circle</span>
                  Resolved by ${ev.resolved_by || 'Staff'}
                </span>
              `}
            </div>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    showToast("Error loading alerts: " + err.message, "danger");
  }
}

async function resolveAlertPrompt(id) {
  const notes = prompt("Enter resolution notes (e.g. Paramedic attended patient / Patient false alarm):", "Patient resting and stable");
  if (notes !== null) {
    await API.resolveEvent(id, notes);
    showToast(`Event #${id} marked as resolved.`, "success");
    loadAlertsData();
  }
}

// Simulator Control Panel
async function loadSimulatorData() {
  try {
    const status = await API.getSimulatorStatus();
    const select = document.getElementById("simulatorScenarioSelect");
    const toggleBtn = document.getElementById("simToggleBtn");
    const bufferDisplay = document.getElementById("simBufferDisplay");
    const notifToggle = document.getElementById("simNotifFailToggle");

    if (select) select.value = status.current_scenario;
    if (toggleBtn) {
      toggleBtn.textContent = status.is_running ? t("stop_sim") : t("start_sim");
      toggleBtn.className = status.is_running ? "btn btn-danger" : "btn btn-success";
    }
    if (bufferDisplay) {
      bufferDisplay.textContent = `${status.buffered_count} readings buffered in local memory`;
    }

    // Notification Failure Toggle Status
    const notifRes = await API.getNotificationFailureToggle();
    if (notifToggle) notifToggle.checked = notifRes.simulate_failure;
  } catch(e) {
    console.warn("Simulator status error:", e);
  }
}

async function switchSimulatorScenario(scenario) {
  try {
    const res = await API.controlSimulator("switch_scenario", scenario);
    showToast(`Switched simulator scenario to: ${res.current_scenario}`, "info");
    loadSimulatorData();
  } catch(e) {
    showToast("Error switching scenario: " + e.message, "danger");
  }
}

async function toggleSimulatorRunning() {
  const status = await API.getSimulatorStatus();
  const nextAction = status.is_running ? "stop" : "start";
  await API.controlSimulator(nextAction);
  loadSimulatorData();
  showToast(`Simulator feed ${nextAction === 'start' ? 'STARTED' : 'PAUSED'}`, "info");
}

async function triggerManualSOS() {
  const btn = document.getElementById("bigSosBtn");
  if (btn) btn.style.transform = "scale(0.95)";

  try {
    const res = await API.triggerSOS("Manual SOS Panic Button Activated from Home Dashboard");
    showToast("🚨 EMERGENCY SOS ACTIVATED! Family and emergency responders alerted.", "danger");
    refreshDashboard();
  } catch(e) {
    showToast("Failed to trigger SOS: " + e.message, "danger");
  } finally {
    if (btn) btn.style.transform = "";
  }
}

// Medications View
async function loadMedicinesData() {
  const listContainer = document.getElementById("medicinesListContainer");
  const adherenceBar = document.getElementById("adherenceProgressBar");
  const adherenceText = document.getElementById("adherencePercentageText");

  try {
    const [meds, adhSummary] = await Promise.all([
      API.getMedications(),
      API.getAdherenceSummary()
    ]);

    if (adherenceBar && adherenceText) {
      adherenceBar.style.width = `${adhSummary.adherence_percentage}%`;
      adherenceText.textContent = `${adhSummary.adherence_percentage}% (${adhSummary.taken} of ${adhSummary.total_scheduled} doses taken)`;
    }

    if (listContainer) {
      if (meds.length === 0) {
        listContainer.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted);">No medications registered yet.</div>`;
        return;
      }

      listContainer.innerHTML = meds.map(m => `
        <div class="card" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <strong style="font-size:1.1rem; color:var(--text-primary);">${m.name}</strong>
              <span class="badge" style="background:rgba(59,130,246,0.15); color:#60a5fa;">${m.strength || m.form}</span>
              ${!m.is_verified ? `<span class="badge" style="background:rgba(239,68,68,0.15); color:#f87171;">Unverified Scan</span>` : ""}
            </div>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">
              Instructions: ${m.instructions} &bull; Schedule: ${JSON.parse(m.schedule_times).join(", ")}
            </div>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn btn-outline" style="font-size:0.8rem;" onclick="logMedAdherence(${m.id}, 'taken')">✔ Take</button>
            <button class="btn btn-outline" style="font-size:0.8rem;" onclick="logMedAdherence(${m.id}, 'snoozed')">⏰ Snooze</button>
          </div>
        </div>
      `).join("");
    }
  } catch(e) {
    showToast("Error loading medications: " + e.message, "danger");
  }
}

async function handleScanStripUpload(input) {
  const file = input.files[0];
  if (!file) return;

  showToast("Scanning strip packaging using AI vision OCR...", "info");
  try {
    const res = await API.scanMedicineStrip(file);
    // Populate modal fields for mandatory user verification
    document.getElementById("medModalName").value = res.name;
    document.getElementById("medModalStrength").value = res.strength || "";
    document.getElementById("medModalForm").value = res.form || "Tablet";
    document.getElementById("medModalInstructions").value = res.suggested_instructions || "After meals";
    document.getElementById("medModalConfidence").textContent = `Extraction Confidence: ${(res.confidence * 100).toFixed(0)}%`;

    document.getElementById("addMedicineModal").classList.add("open");
  } catch (err) {
    showToast("OCR Scan error: " + err.message, "danger");
  }
}

async function saveConfirmedMedicine() {
  const name = document.getElementById("medModalName").value.trim();
  const strength = document.getElementById("medModalStrength").value.trim();
  const form = document.getElementById("medModalForm").value;
  const times = parseInt(document.getElementById("medModalTimes").value) || 1;
  const instructions = document.getElementById("medModalInstructions").value.trim();

  if (!name) {
    alert("Medicine name is required.");
    return;
  }

  await API.addMedication({
    name,
    strength,
    form,
    times_per_day: times,
    schedule_times: ["08:00"],
    duration_days: 30,
    instructions,
    is_verified: true
  });

  document.getElementById("addMedicineModal").classList.remove("open");
  showToast(`Medicine '${name}' saved and schedule active.`, "success");
  loadMedicinesData();
}

async function logMedAdherence(medId, action) {
  await API.logAdherence(medId, action);
  showToast(`Recorded medication ${action.toUpperCase()}`, "success");
  refreshDashboard();
  loadMedicinesData();
}

// Symptom Triage View with Speech-to-Text
let speechRecognition = null;
function toggleSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech-to-text recognition is not supported in this browser. Please type your symptoms.");
    return;
  }

  const micBtn = document.getElementById("micRecordBtn");
  if (!speechRecognition) {
    speechRecognition = new SpeechRecognition();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = true;
    speechRecognition.lang = currentLang === "hi" ? "hi-IN" : "en-IN";

    speechRecognition.onstart = () => {
      if (micBtn) {
        micBtn.textContent = "🔴 Listening... Speak clearly";
        micBtn.classList.add("btn-danger");
      }
    };

    speechRecognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      const input = document.getElementById("symptomInputText");
      if (input) input.value = transcript;
    };

    speechRecognition.onerror = (e) => {
      console.warn("Speech error:", e);
      if (micBtn) {
        micBtn.textContent = "🎤 Voice Input";
        micBtn.classList.remove("btn-danger");
      }
      speechRecognition = null;
    };

    speechRecognition.onend = () => {
      if (micBtn) {
        micBtn.textContent = "🎤 Voice Input";
        micBtn.classList.remove("btn-danger");
      }
      speechRecognition = null;
    };

    speechRecognition.start();
  } else {
    speechRecognition.stop();
    speechRecognition = null;
  }
}

async function runSymptomTriage() {
  const input = document.getElementById("symptomInputText");
  const resultBox = document.getElementById("triageResultBox");
  const text = input ? input.value.trim() : "";

  if (!text) {
    alert("Please enter or dictate symptoms.");
    return;
  }

  resultBox.innerHTML = `<div style="text-align:center; padding:20px;">Analyzing clinical triage rules (Versioned Engine)...</div>`;

  try {
    const res = await API.evaluateSymptoms(text, currentLang);
    const isEmerg = res.outcome === "emergency";

    resultBox.innerHTML = `
      <div class="card" style="border: 2px solid ${isEmerg ? 'var(--danger)' : 'var(--primary)'}; background: ${isEmerg ? 'rgba(239,68,68,0.1)' : 'var(--bg-card)'};">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h3 style="color:${isEmerg ? '#f87171' : 'var(--primary)'}; font-size:1.25rem;">
            ${isEmerg ? '🚨 CRITICAL EMERGENCY GUIDANCE' : 'Clinical Triage Evaluation'}
          </h3>
          <span class="badge ${isEmerg ? 'badge-device-offline' : 'badge-ai-live'}">
            OUTCOME: ${res.outcome.toUpperCase()}
          </span>
        </div>
        <p style="font-size:1.05rem; line-height:1.6; margin-bottom:14px; font-weight:500;">
          ${res.guidance}
        </p>
        ${res.red_flags_detected.length > 0 ? `
          <div style="background:rgba(239,68,68,0.2); padding:10px 14px; border-radius:var(--radius-sm); margin-bottom:14px;">
            <strong>Detected Red-Flag Signs:</strong>
            <ul style="margin-left:20px; margin-top:4px;">
              ${res.red_flags_detected.map(f => `<li>${f}</li>`).join("")}
            </ul>
          </div>
        ` : ""}
        ${res.ai_explanation ? `
          <div style="background:rgba(148,163,184,0.08); padding:12px 14px; border-radius:var(--radius-sm); margin-bottom:14px;">
            <strong>Plain-Language Explanation:</strong>
            <p style="margin-top:4px; font-size:0.9rem; color:var(--text-secondary);">${res.ai_explanation}</p>
          </div>
        ` : ""}
        <div>
          <strong>Suggested Follow-Up Inquiries for Physician Visit:</strong>
          <ul style="margin-left:20px; margin-top:6px; font-size:0.9rem; color:var(--text-secondary);">
            ${res.follow_up_questions.map(q => `<li>${q}</li>`).join("")}
          </ul>
        </div>
        <div style="margin-top:14px; font-size:0.75rem; color:var(--text-muted); border-top:1px solid var(--border-color); padding-top:8px;">
          Engine: ${res.rules_version} &bull; Never diagnose or prescribe. If emergency, dial 112 immediately.
        </div>
      </div>
    `;
  } catch(e) {
    showToast("Triage error: " + e.message, "danger");
  }
}

// AI Doctor Clinical Summary
async function loadDoctorSummary() {
  const container = document.getElementById("doctorSummaryContainer");
  if (!container) return;
  try {
    const res = await API.getLatestSummary();
    const c = res.structured_content;

    container.innerHTML = `
      <div class="card doctor-summary-sheet" style="padding:28px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px; border-bottom:2px solid var(--border-color); padding-bottom:16px;">
          <div>
            <h2 style="font-size:1.6rem; margin-bottom:4px;">${res.title}</h2>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              Generated: ${new Date(res.created_at).toLocaleString()} &bull; Doctor Share Link Token: <code>${res.share_token || 'N/A'}</code>
            </div>
          </div>
          <div class="no-print" style="display:flex; gap:10px;">
            <button class="btn btn-outline" onclick="copyDoctorShareLink('${res.share_token}')">🔗 Copy Doctor Link</button>
            <button class="btn btn-primary" onclick="window.print()">🖨️ Print / Save PDF</button>
          </div>
        </div>

        <!-- 1. Patient Overview -->
        <div style="margin-bottom:20px;">
          <h3 style="font-size:1.15rem; margin-bottom:8px;">1. Patient Overview <span class="provenance-tag prov-patient">[patient-reported]</span></h3>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; font-size:0.9rem;">
            <div><strong>Name:</strong> ${c.patient_overview.name}</div>
            <div><strong>Age / Gender:</strong> ${c.patient_overview.age} / ${c.patient_overview.gender}</div>
            <div><strong>Blood Group:</strong> ${c.patient_overview.blood_group}</div>
            <div><strong>Allergies:</strong> <span style="color:var(--danger);">${c.patient_overview.allergies}</span></div>
            <div><strong>Chronic Conditions:</strong> ${c.patient_overview.chronic_conditions}</div>
          </div>
        </div>

        <!-- 2. Chief Complaints & Red Flags -->
        <div style="margin-bottom:20px;">
          <h3 style="font-size:1.15rem; margin-bottom:8px;">2. Complaints & Red-Flag Screening <span class="provenance-tag prov-ai">[AI-generated]</span></h3>
          <div style="background:rgba(148,163,184,0.06); padding:12px; border-radius:var(--radius-sm); font-size:0.9rem;">
            <div><strong>Red Flag Screen:</strong> ${c.red_flag_screen.status}</div>
            <div style="margin-top:6px;"><strong>Recorded Complaints:</strong> ${c.chief_complaints.map(x => x.complaint).join(", ")}</div>
          </div>
        </div>

        <!-- 3. Current Medications -->
        <div style="margin-bottom:20px;">
          <h3 style="font-size:1.15rem; margin-bottom:8px;">3. Active Medications <span class="provenance-tag prov-patient">[patient-reported]</span></h3>
          <ul style="margin-left:20px; font-size:0.9rem;">
            ${c.current_medications.map(m => `<li><strong>${m.name} ${m.strength || ''}</strong> (${m.form}) &bull; Verification Status: <em>${m.verification_status}</em></li>`).join("")}
          </ul>
        </div>

        <!-- 4. Recent Vital Signs -->
        <div style="margin-bottom:20px;">
          <h3 style="font-size:1.15rem; margin-bottom:8px;">4. Recent Vital Signs <span class="provenance-tag prov-device">[device-simulated]</span></h3>
          <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:6px;">Educational prototype readings &bull; Status: ${c.recent_vitals.status_label}</div>
          <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; font-size:0.9rem;">
            <div style="background:rgba(59,130,246,0.08); padding:10px; border-radius:var(--radius-sm);">
              <strong>Pulse (BPM)</strong><br>Min: ${c.recent_vitals.bpm.min || '--'} | Avg: ${c.recent_vitals.bpm.avg || '--'} | Max: ${c.recent_vitals.bpm.max || '--'}
            </div>
            <div style="background:rgba(16,185,129,0.08); padding:10px; border-radius:var(--radius-sm);">
              <strong>SpO2 Oxygen</strong><br>Min: ${c.recent_vitals.spo2.min || '--'}% | Avg: ${c.recent_vitals.spo2.avg || '--'}% | Max: ${c.recent_vitals.spo2.max || '--'}%
            </div>
            <div style="background:rgba(245,158,11,0.08); padding:10px; border-radius:var(--radius-sm);">
              <strong>Temperature</strong><br>Min: ${c.recent_vitals.temp_c.min || '--'}°C | Avg: ${c.recent_vitals.temp_c.avg || '--'}°C | Max: ${c.recent_vitals.temp_c.max || '--'}°C
            </div>
          </div>
        </div>

        <!-- 5. Information Gaps -->
        <div style="margin-bottom:20px; border-top:1px solid var(--border-color); padding-top:12px;">
          <h3 style="font-size:1.15rem; color:#f59e0b; margin-bottom:6px;">5. Clinical Information Gaps Identified</h3>
          <ul style="margin-left:20px; font-size:0.85rem; color:var(--text-secondary);">
            ${c.information_gaps.length > 0 ? c.information_gaps.map(g => `<li>${g}</li>`).join("") : "<li>No major information gaps flagged.</li>"}
          </ul>
        </div>

        <div style="font-size:0.75rem; color:var(--text-muted); text-align:center; margin-top:20px;">
          ${c.disclaimer}
        </div>
      </div>
    `;
  } catch(e) {
    showToast("Error loading summary: " + e.message, "danger");
  }
}

function copyDoctorShareLink(token) {
  const url = `${window.location.origin}/api/v1/summary/share/${token}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast("72-hour Doctor Summary Link copied to clipboard!", "success");
  });
}

// Emergency Medical ID QR View
async function loadEmergencyID() {
  const qrImg = document.getElementById("emergencyQRImg");
  const linkText = document.getElementById("emergencyPublicUrlText");
  const logsBody = document.getElementById("emergencyAccessLogsBody");

  try {
    let active = await API.getActiveEmergencyQR();
    if (!active) {
      active = await API.generateEmergencyQR();
    }

    if (qrImg) qrImg.src = active.qr_code_base64;
    if (linkText) {
      linkText.href = active.public_url;
      linkText.textContent = active.public_url;
    }

    // Load logs
    const logs = await API.getEmergencyAccessLogs();
    if (logsBody) {
      logsBody.innerHTML = logs.map(l => `
        <tr>
          <td>${new Date(l.accessed_at).toLocaleString()}</td>
          <td>${l.ip_address}</td>
          <td style="font-size:0.75rem; color:var(--text-muted);">${l.user_agent.substring(0, 45)}...</td>
        </tr>
      `).join("");
    }
  } catch(e) {
    showToast("Error loading Emergency QR: " + e.message, "danger");
  }
}

async function regenerateEmergencyQR() {
  await API.generateEmergencyQR();
  showToast("Generated new Emergency Medical ID QR code.", "success");
  loadEmergencyID();
}

async function revokeEmergencyQR() {
  if (confirm("Revoke active Emergency Medical ID QR? Responders will no longer be able to scan.")) {
    await API.revokeEmergencyQR();
    showToast("Emergency Medical ID revoked.", "info");
    loadEmergencyID();
  }
}

async function loadPublicEmergencyCard(token) {
  const container = document.getElementById("publicEmergencyCardContainer");
  if (!container) return;
  try {
    const card = await API.getPublicEmergencyCard(token);
    container.innerHTML = `
      <div class="card" style="border: 2px solid var(--danger); max-width:650px; margin:0 auto; padding:28px;">
        <div style="background:var(--danger); color:#fff; padding:6px 14px; border-radius:var(--radius-sm); font-weight:800; font-size:0.85rem; text-align:center; margin-bottom:18px;">
          🚨 AUTHORISED FIRST RESPONDER MEDICAL IDENTIFICATION
        </div>
        <h2 style="font-size:1.8rem; margin-bottom:6px;">${card.patient_name}</h2>
        <div style="font-size:0.95rem; color:var(--text-secondary); margin-bottom:16px;">
          Age: ${card.age || 'N/A'} &bull; Gender: ${card.gender || 'N/A'}
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px;">
          <div style="background:rgba(239,68,68,0.1); padding:14px; border-radius:var(--radius-sm);">
            <strong>Blood Group:</strong>
            <div style="font-size:1.6rem; font-weight:800; color:var(--danger);">${card.blood_group || 'Unknown'}</div>
          </div>
          <div style="background:rgba(245,158,11,0.1); padding:14px; border-radius:var(--radius-sm);">
            <strong>Severe Allergies:</strong>
            <div style="font-size:1.2rem; font-weight:700; color:var(--warning);">${card.allergies || 'None reported'}</div>
          </div>
        </div>

        <div style="margin-bottom:16px;">
          <strong>Chronic Conditions:</strong>
          <p style="margin-top:4px;">${card.chronic_conditions || 'None recorded'}</p>
        </div>

        <div style="margin-bottom:16px;">
          <strong>Emergency Contacts:</strong>
          <ul style="margin-left:20px; margin-top:6px;">
            ${card.emergency_contacts.map(c => `<li><strong>${c.name}</strong> (${c.relationship}): <a href="tel:${c.phone}" style="color:var(--primary);">${c.phone}</a></li>`).join("")}
          </ul>
        </div>

        <div style="font-size:0.75rem; color:var(--text-muted); border-top:1px solid var(--border-color); padding-top:10px; text-align:center;">
          ${card.disclaimer} &bull; Token Expires: ${new Date(card.expires_at).toLocaleTimeString()}
        </div>
      </div>
    `;
  } catch(e) {
    container.innerHTML = `<div class="card" style="text-align:center; color:var(--danger); padding:30px;">This emergency token is invalid, expired, or has been revoked by the patient.</div>`;
  }
}

// AI Health Chat Assistant
function toggleChatPanel() {
  const panel = document.getElementById("chatSidePanel");
  if (panel) panel.classList.toggle("open");
}

async function sendChatMessage() {
  const input = document.getElementById("chatInputField");
  const msgs = document.getElementById("chatMessagesContainer");
  const text = input ? input.value.trim() : "";
  if (!text) return;

  input.value = "";

  // Append user bubble
  const userEl = document.createElement("div");
  userEl.className = "chat-bubble chat-user";
  userEl.textContent = text;
  msgs.appendChild(userEl);
  msgs.scrollTop = msgs.scrollHeight;

  // Append loading bot bubble
  const botEl = document.createElement("div");
  botEl.className = "chat-bubble chat-bot";
  botEl.textContent = "...";
  msgs.appendChild(botEl);
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res = await API.sendChatMessage(text);
    botEl.innerHTML = `
      <div>${res.reply}</div>
      <div style="font-size:0.72rem; color:var(--text-muted); margin-top:6px; border-top:1px solid var(--border-color); padding-top:4px;">
        ⚠️ ${res.disclaimer}
      </div>
    `;
    if (res.is_emergency) {
      botEl.style.borderColor = "var(--danger)";
    }
  } catch(e) {
    botEl.textContent = "AI Assistant temporarily unavailable.";
  }
  msgs.scrollTop = msgs.scrollHeight;
}

// Lab Reports View
async function loadReportsData() {
  const container = document.getElementById("reportsListContainer");
  if (!container) return;
  try {
    const reports = await API.getReports();
    if (reports.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted);">No reports uploaded yet.</div>`;
      return;
    }

    container.innerHTML = reports.map(r => {
      const data = JSON.parse(r.extracted_data || "[]");
      return `
        <div class="card" style="margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div>
              <strong>${r.filename}</strong>
              <div style="font-size:0.8rem; color:var(--text-secondary);">${new Date(r.uploaded_at).toLocaleDateString()}</div>
            </div>
            <span class="badge badge-ai-live">${data.length} Extracted Markers</span>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Test Parameter</th>
                <th>Measured Value</th>
                <th>Reference Range</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${data.map(d => `
                <tr>
                  <td>${d.test_name}</td>
                  <td><strong>${d.value}</strong> ${d.unit}</td>
                  <td>${d.reference_range}</td>
                  <td><span class="badge ${d.status === 'verified' ? 'badge-device-online' : 'badge-ai-mock'}">${d.status}</span></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }).join("");
  } catch(e) {
    showToast("Error loading reports: " + e.message, "danger");
  }
}

async function handleReportUpload(input) {
  const file = input.files[0];
  if (!file) return;
  showToast(`Uploading and extracting report: ${file.name}...`, "info");
  try {
    await API.uploadReport(file);
    showToast("Diagnostic report uploaded and markers extracted.", "success");
    loadReportsData();
  } catch(e) {
    showToast("Upload error: " + e.message, "danger");
  }
}

// Contacts View
async function loadContactsData() {
  const container = document.getElementById("contactsListContainer");
  if (!container) return;
  try {
    const contacts = await API.getContacts();
    container.innerHTML = contacts.map(c => `
      <div class="card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div>
          <strong>${c.name}</strong> <span class="badge" style="background:rgba(59,130,246,0.1); color:var(--primary);">${c.relationship_type}</span>
          <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">
            📞 ${c.phone} ${c.email ? `&bull; ✉️ ${c.email}` : ''}
          </div>
        </div>
        <button class="btn btn-danger" style="font-size:0.75rem;" onclick="deleteContactPrompt(${c.id})">Delete</button>
      </div>
    `).join("");
  } catch(e) {
    showToast("Error loading contacts: " + e.message, "danger");
  }
}

async function deleteContactPrompt(id) {
  if (confirm("Remove contact?")) {
    await API.deleteContact(id);
    showToast("Contact removed.", "info");
    loadContactsData();
  }
}

async function addContactPrompt() {
  const name = prompt("Contact Full Name:", "Priya Sharma");
  const phone = prompt("Phone Number (with country code):", "+91 94250 98765");
  const rel = prompt("Relationship (Family / Doctor / Neighbor):", "Family");
  if (name && phone) {
    await API.addContact({ name, phone, relationship_type: rel || "Family" });
    showToast("Contact added.", "success");
    loadContactsData();
  }
}

// Admin View
async function loadAdminData() {
  try {
    const [health, auditLogs] = await Promise.all([
      API.getSystemHealth(),
      API.getAuditLogs()
    ]);

    const healthBox = document.getElementById("systemHealthGrid");
    if (healthBox) {
      healthBox.innerHTML = `
        <div class="vital-card">
          <div class="vital-title">System Status</div>
          <div class="vital-value" style="font-size:1.6rem; color:var(--success);">${health.status.toUpperCase()}</div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Version: ${health.version}</div>
        </div>
        <div class="vital-card">
          <div class="vital-title">AI Provider Mode</div>
          <div class="vital-value" style="font-size:1.6rem;">${health.ai_status.toUpperCase()}</div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Provider: ${health.ai_provider}</div>
        </div>
        <div class="vital-card">
          <div class="vital-title">IoT Simulator</div>
          <div class="vital-value" style="font-size:1.6rem;">${health.simulator_active ? 'ACTIVE' : 'IDLE'}</div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Hardware: ESP32 Emulated</div>
        </div>
      `;
    }

    const auditBody = document.getElementById("adminAuditLogsBody");
    if (auditBody) {
      auditBody.innerHTML = auditLogs.slice(0, 30).map(l => `
        <tr>
          <td>${new Date(l.created_at).toLocaleTimeString()}</td>
          <td><strong>${l.action}</strong></td>
          <td>${l.resource}</td>
          <td>${l.actor_role || 'System'}</td>
          <td style="font-size:0.8rem; color:var(--text-secondary);">${l.details || ''}</td>
        </tr>
      `).join("");
    }
  } catch(e) {
    console.warn("Admin data load error:", e);
  }
}

async function triggerResetDemoData() {
  if (confirm("Reset database to original demo state (Ramesh Sharma, 7-day readings, past alerts)?")) {
    try {
      await API.resetDemoData();
      showToast("Demo dataset successfully reset.", "success");
      setTimeout(() => location.reload(), 600);
    } catch(e) {
      showToast("Demo reset failed: " + e.message, "error");
    }
  }
}

async function resetDatabaseConfirm() {
  await triggerResetDemoData();
}

// Immediate Synchronous Role Switching with Background Auth Session Sync
async function switchDemoRole(role) {
  // 1. Immediately apply visual and functional role changes to DOM
  localStorage.setItem("current_role", role);
  applyRolePermissions(role);

  // 2. Sync selector value
  const selector = document.getElementById("roleSelector");
  if (selector && selector.value !== role) {
    selector.value = role;
  }

  // 3. Switch to dashboard tab to show the role-tailored view
  switchTab("tab-dashboard");

  // 4. Synchronize auth session with backend asynchronously in background
  try {
    const loginRes = await API.demoLogin(role);
    const me = await API.getMe();
    if (me) {
      showToast(`Switched active session to: ${me.full_name} (${role.toUpperCase()})`, "info");
      const badge = document.getElementById("currentUserBadge");
      if (badge && !badge.textContent.includes(me.full_name)) {
        badge.textContent = `${me.full_name} (${role.toUpperCase()})`;
      }
    }
  } catch (err) {
    console.warn("Background demo login warning:", err);
  }
}

// Button Helpers for Interactive Dashboard Sections
function handleSosButtonClick() {
  showToast("Press and hold for 2 seconds to confirm SOS dispatch.", "info");
}

function markDoseGiven(btn) {
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Given ✓";
    btn.className = "px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-800 font-label-sm font-bold text-xs cursor-default";
  }
  showToast("Dose logged as administered by Priya Sharma", "success");
}

function saveCaregiverDiaryNote() {
  const input = document.getElementById("caregiver-diary-input");
  if (!input || !input.value.trim()) {
    showToast("Please enter a diary note first", "warning");
    return;
  }
  const note = input.value.trim();
  showToast(`Care note saved: "${note}"`, "success");
  input.value = "";
}

function signDoctorProgressNote() {
  const input = document.getElementById("doctor-soap-input");
  if (input && input.value.trim()) {
    const note = input.value.trim();
    showToast(`Signed clinical note: "${note}"`, "success");
    input.value = "";
  } else {
    showToast("Clinical progress note signed and filed to EMR", "success");
  }
}

function relayResponderFieldNote() {
  const input = document.getElementById("responder-note-input");
  if (input && input.value.trim()) {
    const note = input.value.trim();
    showToast(`Field note relayed to 112 dispatch: "${note}"`, "success");
    input.value = "";
  } else {
    showToast("Field note relayed to 112 dispatch server", "success");
  }
}

// Global System Health Badge
async function checkSystemStatus() {
  try {
    const health = await API.getSystemHealth();
    const aiBadge = document.getElementById("aiModeBadge");
    if (aiBadge) {
      aiBadge.textContent = `AI: ${health.ai_status.toUpperCase()} (${health.ai_provider})`;
      aiBadge.className = health.ai_status === "live" ? "badge badge-ai-live" : "badge badge-ai-mock";
    }
  } catch(e) {}
}

// Notification Failure Toggle Handler
async function handleNotifFailToggle(checkbox) {
  await API.setNotificationFailureToggle(checkbox.checked);
  showToast(`Simulated Notification Failure: ${checkbox.checked ? 'ENABLED' : 'DISABLED'}`, "info");
}

// Toast Alert Messages (High-contrast, modern floating notifications)
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");

  const config = {
    danger: {
      bg: "bg-red-600 text-white border-red-700/50",
      icon: "e911_emergency",
      shadow: "shadow-[0_12px_28px_rgba(220,38,38,0.45)]"
    },
    error: {
      bg: "bg-red-600 text-white border-red-700/50",
      icon: "error",
      shadow: "shadow-[0_12px_28px_rgba(220,38,38,0.45)]"
    },
    warning: {
      bg: "bg-amber-600 text-white border-amber-700/50",
      icon: "warning",
      shadow: "shadow-[0_12px_28px_rgba(217,119,6,0.4)]"
    },
    success: {
      bg: "bg-emerald-600 text-white border-emerald-700/50",
      icon: "check_circle",
      shadow: "shadow-[0_12px_28px_rgba(5,150,105,0.4)]"
    },
    info: {
      bg: "bg-slate-900 text-white border-slate-700",
      icon: "info",
      shadow: "shadow-[0_12px_28px_rgba(15,23,42,0.45)]"
    }
  }[type] || {
    bg: "bg-slate-900 text-white border-slate-700",
    icon: "info",
    shadow: "shadow-[0_12px_28px_rgba(15,23,42,0.45)]"
  };

  toast.className = `flex items-center gap-2.5 px-4 py-3 rounded-xl border text-xs font-bold ${config.bg} ${config.shadow} transition-all duration-300 ease-out mb-2 backdrop-blur-md pointer-events-auto transform translate-y-0 opacity-100`;

  toast.innerHTML = `
    <span class="material-symbols-outlined text-[18px] shrink-0">${config.icon}</span>
    <span class="leading-snug flex-1">${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-6px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function setupEventListeners() {
  // Chat enter key
  const chatInput = document.getElementById("chatInputField");
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendChatMessage();
    });
  }

  // Initialize Hold-to-Confirm 2s SOS Action
  initHoldToConfirmSos();
}

// ----------------------------------------------------
// HOLD-TO-CONFIRM SOS ACTION & 5s CANCEL GRACE PERIOD
// ----------------------------------------------------
let holdTimer = null;
let sosGraceInterval = null;
let sosGraceSeconds = 5;

function initHoldToConfirmSos() {
  const btn = document.getElementById("holdSosBtn") || document.getElementById("sos-button");
  const fill = document.getElementById("holdSosProgress") || document.getElementById("sos-progress");
  const hint = document.getElementById("holdSosTimerHint") || document.getElementById("sos-timer-label");
  if (!btn) return;

  let animFrame = null;
  let startTime = 0;
  const holdDuration = 2000;

  const startHold = (e) => {
    if (e.type === "touchstart") e.preventDefault();
    btn.classList.add("holding");
    btn.classList.add("scale-[0.98]");
    startTime = Date.now();
    playChime("tick");

    function updateProgress() {
      const elapsed = Date.now() - startTime;
      const pct = Math.min((elapsed / holdDuration) * 100, 100);
      if (fill) fill.style.width = pct + "%";

      const remaining = Math.max(0, ((holdDuration - elapsed) / 1000).toFixed(1));
      if (hint) hint.textContent = `Holding... ${remaining}s`;

      if (elapsed >= holdDuration) {
        cancelHold();
        if (hint) hint.textContent = "Confirmed!";
        triggerSosWithGracePeriod();
      } else {
        animFrame = requestAnimationFrame(updateProgress);
      }
    }
    animFrame = requestAnimationFrame(updateProgress);
  };

  const cancelHold = () => {
    if (animFrame) {
      cancelAnimationFrame(animFrame);
      animFrame = null;
    }
    btn.classList.remove("holding");
    btn.classList.remove("scale-[0.98]");
    if (fill) fill.style.width = "0%";
    if (hint) hint.textContent = "Hold 2s";
  };

  btn.addEventListener("mousedown", startHold);
  btn.addEventListener("touchstart", startHold, { passive: false });
  window.addEventListener("mouseup", cancelHold);
  window.addEventListener("touchend", cancelHold);
}

function triggerSosWithGracePeriod() {
  const modal = document.getElementById("sosGraceModal");
  const countEl = document.getElementById("sosGraceCountdown");
  const barEl = document.getElementById("sosGraceProgressBar");
  if (!modal) return;

  sosGraceSeconds = 5;
  if (countEl) countEl.textContent = sosGraceSeconds;
  if (barEl) barEl.style.width = "100%";
  modal.classList.remove("hidden");
  playChime("alert");

  if (sosGraceInterval) clearInterval(sosGraceInterval);

  sosGraceInterval = setInterval(async () => {
    sosGraceSeconds -= 1;
    if (countEl) countEl.textContent = sosGraceSeconds;
    if (barEl) barEl.style.width = `${(sosGraceSeconds / 5) * 100}%`;
    playChime("tick");

    if (sosGraceSeconds <= 0) {
      clearInterval(sosGraceInterval);
      sosGraceInterval = null;
      modal.classList.add("hidden");
      
      // Dispatch SOS to backend
      try {
        const res = await API.triggerSOS("Confirmed Emergency SOS (Hold-to-confirm 2s validated)");
        showToast("🚨 EMERGENCY SOS DISPATCHED to Priya Sharma & 112 services!", "danger");
        playChime("alert");
        refreshDashboard();
        if (currentRole === "responder" || currentRole === "caregiver" || currentRole === "doctor") {
          loadAlertsData();
        }
      } catch (err) {
        showToast("Error dispatching SOS: " + err.message, "danger");
      }
    }
  }, 1000);
}

function cancelSosGracePeriod() {
  if (sosGraceInterval) {
    clearInterval(sosGraceInterval);
    sosGraceInterval = null;
  }
  const modal = document.getElementById("sosGraceModal");
  if (modal) modal.classList.add("hidden");
  playChime("cancel");
  showToast("Emergency SOS Cancelled: You indicated you are okay.", "info");
}

// ----------------------------------------------------
// GUIDED DEMO TOUR (VIVA MENTOR WALKTHROUGH MODE)
// ----------------------------------------------------
const demoTourSteps = [
  {
    badge: "STEP 1/6: NORMAL REST",
    text: "Normal resting vitals: Pulse ~74 BPM, SpO₂ ~98%, Temp ~36.8°C. Telemetry updates live via Server-Sent Events.",
    actionName: "Simulate Normal",
    action: async () => {
      await API.demoLogin("patient");
      const me = await API.getMe();
      updateUserBadge(me);
      await API.controlSimulator("start");
      await switchSimulatorScenario("normal_rest");
      switchTab("tab-dashboard");
      showToast("Tour Step 1: Simulator set to Normal Rest", "info");
    }
  },
  {
    badge: "STEP 2/6: LOW SPO2 HYPOXIA",
    text: "Simulates SpO₂ drop to 89%. Demonstrates rule engine tracking sustained abnormal readings for >=30 seconds.",
    actionName: "Simulate Hypoxia",
    action: async () => {
      await switchSimulatorScenario("low_oxygen");
      switchTab("tab-dashboard");
      showToast("Tour Step 2: SpO2 dropping below 90% (Hypoxia)", "warning");
    }
  },
  {
    badge: "STEP 3/6: 15s GRACE COUNTDOWN",
    text: "Automated triage safety engine fires 15s grace modal. Patient can cancel if false alarm, preventing unnecessary dispatches.",
    actionName: "Show 15s Grace",
    action: async () => {
      handleAutoWarningCandidate({
        candidate_id: 999,
        countdown_seconds: 15,
        duration_secs: 32,
        reason: "Low SpO2 (89% < 92% sustained >=30s)"
      });
      showToast("Tour Step 3: 15-second grace countdown active", "info");
    }
  },
  {
    badge: "STEP 4/6: HOLD-TO-CONFIRM SOS",
    text: "Single hold-to-confirm emergency button prevents accidental triggers, followed by a 5-second cancel window.",
    actionName: "Trigger SOS Grace",
    action: async () => {
      handleAutoWarningCancelled();
      triggerSosWithGracePeriod();
      showToast("Tour Step 4: 5-second cancellation grace window", "info");
    }
  },
  {
    badge: "STEP 5/6: RESPONDER PRIVACY (ASHA)",
    text: "Switch to Responder (Asha). Notice strict data minimization: only Emergency ID is shown; private meds are hidden.",
    actionName: "Switch to Asha",
    action: async () => {
      cancelSosGracePeriod();
      await switchDemoRole("responder");
      showToast("Tour Step 5: Responder mode active - data minimization enforced", "info");
    }
  },
  {
    badge: "STEP 6/6: ALERT STEPPER & RESOLVE",
    text: "Verified incident state machine: Created → Sent → Delivered → Acknowledged with exact failure and delivery states.",
    actionName: "View Alert Stepper",
    action: async () => {
      switchTab("tab-alerts");
      loadAlertsData();
      showToast("Tour Step 6: Viewing full alert dispatch chain & audit log", "info");
    }
  }
];

let currentTourIndex = 0;

function startGuidedDemoTour() {
  const bar = document.getElementById("demoTourBar");
  if (!bar) return;
  bar.classList.remove("hidden");
  currentTourIndex = 0;
  renderTourStep();
}

function stopGuidedDemoTour() {
  const bar = document.getElementById("demoTourBar");
  if (bar) bar.classList.add("hidden");
}

function renderTourStep() {
  const step = demoTourSteps[currentTourIndex];
  const badge = document.getElementById("tourStepBadge");
  const text = document.getElementById("tourStepText");
  const actionBtn = document.getElementById("tourActionBtn");
  const prevBtn = document.getElementById("tourPrevBtn");
  const nextBtn = document.getElementById("tourNextBtn");

  if (badge) badge.textContent = step.badge;
  if (text) text.textContent = step.text;
  if (actionBtn) actionBtn.textContent = step.actionName;
  if (prevBtn) prevBtn.disabled = currentTourIndex === 0;
  if (nextBtn) nextBtn.textContent = currentTourIndex === demoTourSteps.length - 1 ? "Finish" : "Next";
}

async function runTourCurrentAction() {
  const step = demoTourSteps[currentTourIndex];
  if (step && step.action) {
    await step.action();
  }
}

function nextTourStep() {
  if (currentTourIndex < demoTourSteps.length - 1) {
    currentTourIndex++;
    renderTourStep();
    runTourCurrentAction();
  } else {
    stopGuidedDemoTour();
    showToast("Demo tour completed! Good luck on your viva!", "success");
  }
}

function prevTourStep() {
  if (currentTourIndex > 0) {
    currentTourIndex--;
    renderTourStep();
    runTourCurrentAction();
  }
}

// ----------------------------------------------------
// ACCESSIBILITY & AUDIO UTILITIES
// ----------------------------------------------------
function toggleFontSize() {
  const isLarge = document.documentElement.classList.toggle("font-large");
  const btn = document.getElementById("fontSizeBtn");
  if (btn) btn.textContent = isLarge ? "A⁻" : "A⁺";
  showToast(`Accessibility Text Size: ${isLarge ? 'LARGE' : 'STANDARD'}`, "info");
}

let audioCtx = null;
function playChime(type = "tick") {
  if (audioMuted) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    const now = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === "tick") {
      osc.frequency.setValueAtTime(800, now);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === "alert") {
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(880, now + 0.1);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.36);
    } else if (type === "cancel") {
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.setValueAtTime(300, now + 0.1);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.26);
    }
  } catch (e) {
    // Audio context silently ignored if blocked by browser policy
  }
}

// Stitch Clinical Telemetry Interactivity Helpers
function triggerEmergencySOS() {
  triggerSosWithGracePeriod();
}

async function injectSimulation(type, btn) {
  if (btn) {
    btn.classList.add('ring-2', 'ring-primary', 'bg-surface-container-high');
    setTimeout(() => {
      btn.classList.remove('ring-2', 'ring-primary', 'bg-surface-container-high');
    }, 600);
  }
  const scenarioMap = {
    'bradycardia': 'high_pulse',
    'disconnect': 'no_finger',
    'lag': 'network_fail',
    'hypoxemia': 'low_oxygen',
    'sos': 'sos_press',
    'normal': 'normal_rest'
  };
  const targetScenario = scenarioMap[type] || 'normal_rest';
  await switchSimulatorScenario(targetScenario);
}

function setTimeframe(btn, tf) {
  document.querySelectorAll('.timeframe-pill').forEach(b => {
    b.className = 'timeframe-pill px-3 py-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container text-xs font-semibold transition-all cursor-pointer';
  });
  if (btn) {
    btn.className = 'timeframe-pill px-3 py-1.5 rounded-lg bg-surface-container-lowest text-primary text-xs font-bold shadow-xs border border-outline-variant/30 transition-all cursor-pointer';
  }
  const rangeMap = { 'live': 'dense', '1h': 'dense', '24h': 'day', '7d': 'week' };
  loadHistoryData(rangeMap[tf] || 'day');
}

let audioMuted = false;
function toggleAudioFx(btn) {
  audioMuted = !audioMuted;
  const icon = btn ? btn.querySelector('.material-symbols-outlined') : null;
  if (icon) {
    icon.textContent = audioMuted ? 'volume_off' : 'volume_up';
  }
  showToast(audioMuted ? 'Audible telemetry alert feedback muted.' : 'Audible telemetry alert feedback active.', 'info');
}

function logBedsideSymptom() {
  const input = document.getElementById('obs-input') || document.getElementById('symptom-input');
  if (!input) return;
  const val = input.value.trim();
  if (!val) {
    showToast('Please type an observation to log.', 'warning');
    return;
  }
  const list = document.getElementById('observations-list');
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (list) {
    const newCard = document.createElement('div');
    newCard.className = 'p-3 bg-surface-container-low rounded-2xl transition-colors hover:bg-surface-container border-l-4 border-primary';
    newCard.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-label-lg font-bold text-on-surface">${escapeHtml(val)}</span>
        <span class="font-label-sm font-mono text-primary font-bold">${timeStr}</span>
      </div>
      <p class="font-body-sm text-on-surface-variant mt-1">Bedside observation recorded into patient chart.</p>
    `;
    list.prepend(newCard);
  }
  input.value = '';
  showToast('Observation recorded in patient chart.', 'success');
}

function escapeHtml(text) {
  const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// User Logout Handler
function handleLogout() {
  if (confirm("Log out of the clinical dashboard and return to the landing page?")) {
    API.setToken(null);
    localStorage.removeItem("auth_token");
    sessionStorage.clear();
    showToast("Logged out successfully. Returning to landing page...", "info");
    setTimeout(() => {
      window.location.href = "/";
    }, 350);
  }
}


