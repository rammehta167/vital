// Real-time Event Stream with Fallback Polling
const StreamManager = {
  eventSource: null,
  isSSEActive: false,
  pollingInterval: null,
  callbacks: {
    onReading: null,
    onAlert: null,
    onAutoWarning: null,
    onAutoWarningCancelled: null
  },

  init(callbacks = {}) {
    this.callbacks = { ...this.callbacks, ...callbacks };
    this.connectSSE();
  },

  connectSSE() {
    if (this.eventSource) {
      this.eventSource.close();
    }

    try {
      this.eventSource = new EventSource("/api/v1/stream");

      this.eventSource.onopen = () => {
        console.log("[SSE] Connected to real-time event stream.");
        this.isSSEActive = true;
        this.stopPollingFallback();
      };

      this.eventSource.addEventListener("reading_received", (e) => {
        try {
          const data = JSON.parse(e.data);
          if (this.callbacks.onReading) this.callbacks.onReading(data);
        } catch (err) { console.error("[SSE parse error]", err); }
      });

      this.eventSource.addEventListener("event_created", (e) => {
        try {
          const data = JSON.parse(e.data);
          if (this.callbacks.onAlert) this.callbacks.onAlert(data);
        } catch (err) { console.error("[SSE parse error]", err); }
      });

      this.eventSource.addEventListener("auto_warning_countdown", (e) => {
        try {
          const data = JSON.parse(e.data);
          if (this.callbacks.onAutoWarning) this.callbacks.onAutoWarning(data);
        } catch (err) { console.error("[SSE parse error]", err); }
      });

      this.eventSource.addEventListener("auto_warning_cancelled", (e) => {
        try {
          const data = JSON.parse(e.data);
          if (this.callbacks.onAutoWarningCancelled) this.callbacks.onAutoWarningCancelled(data);
        } catch (err) { console.error("[SSE parse error]", err); }
      });

      this.eventSource.onerror = (err) => {
        console.warn("[SSE] Disconnected or failed. Switching to 2-second polling fallback...", err);
        this.isSSEActive = false;
        this.startPollingFallback();
      };
    } catch (e) {
      console.warn("[SSE] EventSource unavailable. Starting polling fallback.", e);
      this.startPollingFallback();
    }
  },

  startPollingFallback() {
    if (this.pollingInterval) return;
    console.log("[Stream] Starting 2s polling fallback...");
    this.pollingInterval = setInterval(async () => {
      try {
        const latest = await API.getLatestReading();
        if (latest && latest.reading && this.callbacks.onReading) {
          this.callbacks.onReading(latest.reading);
        }
      } catch (err) {
        // Silently retry
      }
    }, 2000);
  },

  stopPollingFallback() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }
};
