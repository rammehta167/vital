// Chart.js Visualizations tailored for Stitch Clinical Pulse Telemetry
let vitalHistoryChart = null;
let liveECGChart = null;
let trendHistoryChart = null;

const ChartsManager = {
  // 1. Live Pulse & SpO2 Chart (15 latest samples)
  initLiveVitalChart(ctx) {
    if (vitalHistoryChart) {
      vitalHistoryChart.destroy();
    }

    vitalHistoryChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Pulse Rate (BPM)",
            borderColor: "#62df7d",
            backgroundColor: "rgba(98, 223, 125, 0.12)",
            borderWidth: 2.2,
            tension: 0.35,
            fill: true,
            pointRadius: 2,
            pointBackgroundColor: "#62df7d",
            data: [],
            yAxisID: "yBPM"
          },
          {
            label: "Blood Oxygen SpO2 (%)",
            borderColor: "#bec6e0",
            backgroundColor: "transparent",
            borderWidth: 2,
            borderDash: [5, 4],
            tension: 0.2,
            pointRadius: 2,
            pointBackgroundColor: "#bec6e0",
            data: [],
            yAxisID: "ySpO2"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: "#eaf1ff",
              font: { family: "'JetBrains Mono', monospace", size: 11, weight: '600' }
            }
          },
          tooltip: {
            mode: "index",
            intersect: false,
            backgroundColor: "rgba(11, 28, 48, 0.9)",
            titleFont: { family: "'JetBrains Mono', monospace" },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.08)" },
            ticks: { color: "#bec6e0", font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          yBPM: {
            type: "linear",
            position: "left",
            min: 40,
            max: 160,
            grid: { color: "rgba(255, 255, 255, 0.08)" },
            ticks: { color: "#62df7d", font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          ySpO2: {
            type: "linear",
            position: "right",
            min: 75,
            max: 100,
            grid: { drawOnChartArea: false },
            ticks: { color: "#bec6e0", font: { family: "'JetBrains Mono', monospace", size: 10 } }
          }
        }
      }
    });
  },

  updateLiveVitalChart(reading) {
    if (!vitalHistoryChart) return;
    const timeLabel = new Date(reading.measured_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    const maxPoints = 20;
    const labels = vitalHistoryChart.data.labels;
    const bpmData = vitalHistoryChart.data.datasets[0].data;
    const spo2Data = vitalHistoryChart.data.datasets[1].data;

    labels.push(timeLabel);
    bpmData.push(reading.bpm !== null ? reading.bpm : null);
    spo2Data.push(reading.spo2 !== null ? reading.spo2 : null);

    if (labels.length > maxPoints) {
      labels.shift();
      bpmData.shift();
      spo2Data.shift();
    }

    vitalHistoryChart.update("none");
  },

  // 2. Simulated ECG Waveform Strip
  initLiveECGChart(ctx) {
    if (liveECGChart) {
      liveECGChart.destroy();
    }

    // Initialize with 40 baseline points
    const initPoints = Array.from({ length: 40 }, () => 0);
    const initLabels = Array.from({ length: 40 }, (_, i) => i);

    liveECGChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: initLabels,
        datasets: [{
          label: "Simulated Pulse Rhythm Trace (mV)",
          borderColor: "#62df7d",
          backgroundColor: "rgba(98, 223, 125, 0.08)",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          fill: true,
          data: initPoints
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { display: false },
          y: {
            min: -1.2,
            max: 2.5,
            grid: { color: "rgba(98, 223, 125, 0.15)" },
            ticks: { color: "#62df7d", font: { family: "'JetBrains Mono', monospace", size: 9 } }
          }
        }
      }
    });
  },

  updateLiveECG(sampleSlice) {
    if (!liveECGChart || !sampleSlice || sampleSlice.length === 0) return;
    const data = liveECGChart.data.datasets[0].data;

    sampleSlice.forEach(pt => {
      data.push(pt);
      if (data.length > 50) {
        data.shift();
      }
    });

    liveECGChart.update("none");
  },

  // 3. Historical Trend Chart
  initTrendChart(ctx, readings) {
    if (trendHistoryChart) {
      trendHistoryChart.destroy();
    }

    const labels = readings.map(r => new Date(r.measured_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    const bpms = readings.map(r => r.bpm);
    const spo2s = readings.map(r => r.spo2);
    const temps = readings.map(r => r.temp_c);

    trendHistoryChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Pulse (BPM)",
            borderColor: "#006b2c",
            backgroundColor: "rgba(0, 107, 44, 0.08)",
            data: bpms,
            tension: 0.3,
            fill: true,
            yAxisID: "y1"
          },
          {
            label: "SpO2 (%)",
            borderColor: "#565e74",
            data: spo2s,
            borderDash: [4, 4],
            tension: 0.3,
            yAxisID: "y2"
          },
          {
            label: "Temp (°C)",
            borderColor: "#d97706",
            data: temps,
            tension: 0.3,
            yAxisID: "y3"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: "#565e74",
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' }
            }
          }
        },
        scales: {
          x: { ticks: { color: "#6e7b6c", font: { family: "'JetBrains Mono', monospace", size: 10 } } },
          y1: { type: "linear", position: "left", min: 40, max: 150, ticks: { color: "#006b2c" } },
          y2: { type: "linear", position: "right", min: 70, max: 100, ticks: { color: "#565e74" }, grid: { drawOnChartArea: false } },
          y3: { type: "linear", position: "right", min: 35, max: 41, ticks: { color: "#d97706" }, grid: { drawOnChartArea: false } }
        }
      }
    });
  }
};
