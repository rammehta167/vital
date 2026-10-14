// Centralized API Client
const API = {
  token: localStorage.getItem("auth_token") || "",

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("auth_token", token);
    } else {
      localStorage.removeItem("auth_token");
    }
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    if (this.token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    options.headers = headers;

    try {
      const response = await fetch(endpoint, options);
      if (response.status === 401 && endpoint !== "/api/v1/auth/login" && endpoint !== "/api/v1/auth/demo-login") {
        console.warn("Session expired or unauthorized. Switching to demo patient session...");
        await this.demoLogin("patient");
        // Retry once with new token
        headers["Authorization"] = `Bearer ${this.token}`;
        options.headers = headers;
        return (await fetch(endpoint, options)).json();
      }

      if (!response.ok) {
        let errData;
        try { errData = await response.json(); } catch(e) { errData = { detail: response.statusText }; }
        throw new Error(errData.detail || `HTTP Error ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`[API Error: ${endpoint}]`, err);
      throw err;
    }
  },

  // Auth & Profile
  async demoLogin(role = "patient") {
    const res = await this.request("/api/v1/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role })
    });
    this.setToken(res.access_token);
    return res;
  },

  async getMe() {
    return this.request("/api/v1/auth/me");
  },

  async exportData() {
    return this.request("/api/v1/auth/export-my-data");
  },

  async deleteMyData() {
    return this.request("/api/v1/auth/delete-my-data", { method: "DELETE" });
  },

  // Vitals Readings
  async getLatestReading() {
    return this.request("/api/v1/readings/latest");
  },

  async getReadingsHistory(range = "day") {
    return this.request(`/api/v1/readings/history?range=${range}`);
  },

  // Emergency SOS & Events
  async triggerSOS(details = "Manual SOS Panic Button Activated") {
    return this.request("/api/v1/sos", {
      method: "POST",
      body: JSON.stringify({
        idempotency_key: `sos_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        details
      })
    });
  },

  async getEvents(status = "") {
    return this.request(status ? `/api/v1/events?status=${status}` : "/api/v1/events");
  },

  async resolveEvent(id, notes = "Resolved via Dashboard") {
    return this.request(`/api/v1/events/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ notes })
    });
  },

  async cancelWarning(candidateId) {
    return this.request(`/api/v1/events/cancel-warning/${candidateId}`, { method: "POST" });
  },

  // Simulator Control
  async getSimulatorStatus() {
    return this.request("/api/v1/simulator/status");
  },

  async controlSimulator(action, scenario = null) {
    return this.request("/api/v1/simulator/control", {
      method: "POST",
      body: JSON.stringify({ action, scenario })
    });
  },

  // Medications
  async getMedications() {
    return this.request("/api/v1/medications");
  },

  async scanMedicineStrip(file) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request("/api/v1/medications/scan-strip", {
      method: "POST",
      body: formData
    });
  },

  async addMedication(medData) {
    return this.request("/api/v1/medications", {
      method: "POST",
      body: JSON.stringify(medData)
    });
  },

  async logAdherence(medId, action) {
    return this.request("/api/v1/medications/adherence", {
      method: "POST",
      body: JSON.stringify({
        medication_id: medId,
        scheduled_time: new Date().toISOString(),
        action
      })
    });
  },

  async getAdherenceSummary() {
    return this.request("/api/v1/medications/adherence-summary");
  },

  // Symptoms & Triage
  async evaluateSymptoms(inputText, language = "en", speechTranscript = "") {
    return this.request("/api/v1/symptoms/evaluate", {
      method: "POST",
      body: JSON.stringify({
        input_text: inputText,
        language,
        speech_transcript: speechTranscript
      })
    });
  },

  // AI Doctor Summary
  async generateDoctorSummary() {
    return this.request("/api/v1/summary/generate", { method: "POST" });
  },

  async getLatestSummary() {
    return this.request("/api/v1/summary/latest");
  },

  // Emergency Medical ID QR
  async generateEmergencyQR(visibleFields = ["blood_group", "allergies", "chronic_conditions", "emergency_contacts", "medications"]) {
    return this.request("/api/v1/emergency-id/generate", {
      method: "POST",
      body: JSON.stringify({ visible_fields: visibleFields, expire_hours: 24 })
    });
  },

  async getActiveEmergencyQR() {
    return this.request("/api/v1/emergency-id/active");
  },

  async revokeEmergencyQR() {
    return this.request("/api/v1/emergency-id/revoke", { method: "POST" });
  },

  async getEmergencyAccessLogs() {
    return this.request("/api/v1/emergency-id/access-logs");
  },

  async getPublicEmergencyCard(token) {
    return this.request(`/api/v1/emergency-id/public/${token}`);
  },

  // Diagnostics & Reports
  async getReports() {
    return this.request("/api/v1/reports");
  },

  async uploadReport(file) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request("/api/v1/reports/upload", {
      method: "POST",
      body: formData
    });
  },

  async verifyReport(reportId, verifiedFields) {
    return this.request(`/api/v1/reports/${reportId}/verify`, {
      method: "PUT",
      body: JSON.stringify(verifiedFields)
    });
  },

  // Contacts
  async getContacts() {
    return this.request("/api/v1/contacts");
  },

  async addContact(contactData) {
    return this.request("/api/v1/contacts", {
      method: "POST",
      body: JSON.stringify(contactData)
    });
  },

  async deleteContact(id) {
    return this.request(`/api/v1/contacts/${id}`, { method: "DELETE" });
  },

  // AI Chat
  async sendChatMessage(message) {
    return this.request("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
  },

  // Admin & Health
  async getSystemHealth() {
    return this.request("/api/v1/admin/health");
  },

  async getAuditLogs(action = "") {
    return this.request(action ? `/api/v1/admin/audit-logs?action=${action}` : "/api/v1/admin/audit-logs");
  },

  async getNotificationFailureToggle() {
    return this.request("/api/v1/admin/notification-failure-toggle");
  },

  async setNotificationFailureToggle(enabled) {
    return this.request(`/api/v1/admin/notification-failure-toggle?enabled=${enabled}`, { method: "POST" });
  },

  async resetDemoData() {
    return this.request("/api/v1/admin/reset-demo-data", { method: "POST" });
  }
};
