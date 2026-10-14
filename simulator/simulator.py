"""
IoT Hardware Simulator for AI Healthcare Companion.
Simulates an ESP32 microcontroller with MAX30102 pulse oximeter + temperature sensor + GPS + SOS button.
Sends HTTP POST payloads identical to future firmware.
"""
import os
import time
import math
import random
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

# Defaults
DEFAULT_TARGET_URL = os.getenv("SIMULATOR_TARGET_URL", "http://localhost:8000/api/v1/readings")
DEFAULT_SOS_URL = DEFAULT_TARGET_URL.replace("/readings", "/sos")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "ESP32-VITAL-01")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "demo-device-key-change-me")

# Base coordinates: Jabalpur, Madhya Pradesh, India
BASE_LAT = 23.1815
BASE_LNG = 79.9864


class VitalSimulator:
    def __init__(
        self,
        target_url: str = DEFAULT_TARGET_URL,
        device_id: str = DEFAULT_DEVICE_ID,
        device_key: str = DEVICE_API_KEY
    ):
        self.target_url = target_url
        self.sos_url = target_url.replace("/readings", "/sos")
        self.bulk_url = target_url.replace("/readings", "/readings/bulk")
        self.device_id = device_id
        self.device_key = device_key

        self.scenario = "normal_rest"
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # State tracking
        self.current_bpm = 72.0
        self.current_spo2 = 98.0
        self.current_temp = 36.7
        self.lat = BASE_LAT
        self.lng = BASE_LNG
        self.step = 0
        self.sustained_high_pulse_timer = 0

        # Buffer for simulated network failures
        self.buffered_readings: List[Dict[str, Any]] = []
        self.network_failing = False
        self.last_sent_at: Optional[datetime] = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[SIMULATOR] Started for device {self.device_id} in scenario: {self.scenario}")

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        print(f"[SIMULATOR] Stopped.")

    def set_scenario(self, scenario: str):
        valid = [
            "normal_rest", "exercise", "fever", "low_oxygen", "high_pulse",
            "no_finger", "poor_signal", "offline", "network_fail", "sos_press", "fall_detected"
        ]
        if scenario not in valid:
            raise ValueError(f"Unknown scenario '{scenario}'. Valid: {valid}")

        prev = self.scenario
        self.scenario = scenario
        self.sustained_high_pulse_timer = 0
        print(f"[SIMULATOR] Switched scenario from '{prev}' to '{self.scenario}'")

        # If switching away from network_fail, flush buffered readings
        if prev == "network_fail" and scenario != "network_fail":
            self.flush_buffer()

    def flush_buffer(self):
        if not self.buffered_readings:
            return
        to_send = list(self.buffered_readings)
        self.buffered_readings.clear()
        print(f"[SIMULATOR] Network recovered! Flushing {len(to_send)} buffered readings to bulk upload...")
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    self.bulk_url,
                    headers={"X-Device-Key": self.device_key},
                    json={"device_id": self.device_id, "readings": to_send}
                )
                print(f"[SIMULATOR] Bulk flush response: {resp.status_code}")
        except Exception as e:
            print(f"[SIMULATOR] Bulk flush error: {e}")

    def trigger_sos(self, details: str = "Hardware SOS Panic Button Pressed"):
        print(f"[SIMULATOR] Triggering SOS for {self.device_id}...")
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    self.sos_url,
                    headers={"X-Device-Key": self.device_key},
                    json={
                        "device_id": self.device_id,
                        "lat": self.lat,
                        "lng": self.lng,
                        "details": details
                    }
                )
                print(f"[SIMULATOR] SOS dispatched: {resp.status_code}")
                return resp.json()
        except Exception as e:
            print(f"[SIMULATOR] SOS trigger failed: {e}")
            return None

    def trigger_fall(self):
        print(f"[SIMULATOR] Simulated Fall Detected (triaxial accelerometer impact > 3.5g)...")
        return self.trigger_sos(details="Fall Detected: Triaxial accelerometer spike followed by inactivity")

    def _generate_ecg_sample(self) -> List[float]:
        # Generate 16 sample points representing a simulated P-Q-R-S-T wave slice
        sample = []
        phase = (self.step % 10) / 10.0 * 2 * math.pi
        for i in range(16):
            t = phase + (i * 0.2)
            # Baseline sine + sharp QRS peak
            val = 0.2 * math.sin(t)
            if 1.4 < (t % (2 * math.pi)) < 1.7:
                val += 1.8  # R peak
            elif 1.2 < (t % (2 * math.pi)) <= 1.4:
                val -= 0.4  # Q dip
            elif 1.7 <= (t % (2 * math.pi)) < 1.9:
                val -= 0.6  # S dip
            sample.append(round(val + random.uniform(-0.05, 0.05), 3))
        return sample

    def _generate_reading(self) -> Optional[Dict[str, Any]]:
        self.step += 1

        # GPS slow random drift (around Jabalpur, India)
        # Occasionally 5% chance of "no fix" (null lat/lng)
        has_gps_fix = random.random() > 0.05
        if has_gps_fix:
            self.lat += random.uniform(-0.0001, 0.0001)
            self.lng += random.uniform(-0.0001, 0.0001)
            cur_lat = round(self.lat, 6)
            cur_lng = round(self.lng, 6)
        else:
            cur_lat = None
            cur_lng = None

        now_iso = datetime.now(timezone.utc).isoformat()
        ecg = self._generate_ecg_sample()

        scenario = self.scenario

        # Scenario 8: Device offline
        if scenario == "offline":
            return None  # Stops sending completely

        # Scenario 10: SOS button press
        if scenario == "sos_press":
            self.trigger_sos()
            self.scenario = "normal_rest"  # Return to normal after press

        # Scenario 11: Fall detected
        if scenario == "fall_detected":
            self.trigger_fall()
            self.scenario = "normal_rest"

        # Scenario 6: No finger on sensor
        if scenario == "no_finger":
            return {
                "device_id": self.device_id,
                "bpm": None,
                "spo2": None,
                "temp_c": round(36.5 + random.uniform(-0.1, 0.1), 1),
                "ecg_sample": None,
                "lat": cur_lat,
                "lng": cur_lng,
                "signal_quality": "no_finger",
                "ts": now_iso
            }

        # Scenario 7: Poor signal / noisy
        if scenario == "poor_signal":
            return {
                "device_id": self.device_id,
                "bpm": round(random.uniform(40, 160), 1),
                "spo2": round(random.uniform(75, 100), 1),
                "temp_c": round(random.uniform(35.0, 39.0), 1),
                "ecg_sample": ecg,
                "lat": cur_lat,
                "lng": cur_lng,
                "signal_quality": random.choice(["noisy", "poor"]),
                "ts": now_iso
            }

        # Scenario 2: Exercise
        if scenario == "exercise":
            target_bpm = 125.0
            target_spo2 = 97.0
            target_temp = 37.2
            noise_bpm = 3.0
        # Scenario 3: Fever
        elif scenario == "fever":
            target_bpm = 98.0
            target_spo2 = 96.0
            target_temp = 38.8
            noise_bpm = 2.0
        # Scenario 4: Low oxygen
        elif scenario == "low_oxygen":
            target_bpm = 88.0
            target_spo2 = 89.0  # Hypoxia
            target_temp = 36.6
            noise_bpm = 2.0
        # Scenario 5: High pulse sustained (>130 BPM for >= 30s)
        elif scenario == "high_pulse":
            target_bpm = 138.0
            target_spo2 = 97.0
            target_temp = 37.1
            noise_bpm = 2.0
            self.sustained_high_pulse_timer += 1
        # Scenario 1: Normal rest (default)
        else:
            target_bpm = 72.0
            target_spo2 = 98.0
            target_temp = 36.7
            noise_bpm = 1.5

        # Random-walk smoothing towards target
        self.current_bpm += 0.2 * (target_bpm - self.current_bpm) + random.uniform(-noise_bpm, noise_bpm)
        self.current_spo2 += 0.2 * (target_spo2 - self.current_spo2) + random.uniform(-0.3, 0.3)
        self.current_temp += 0.1 * (target_temp - self.current_temp) + random.uniform(-0.05, 0.05)

        # Clamping
        self.current_spo2 = max(70.0, min(100.0, self.current_spo2))

        return {
            "device_id": self.device_id,
            "bpm": round(self.current_bpm, 1),
            "spo2": round(self.current_spo2, 1),
            "temp_c": round(self.current_temp, 1),
            "ecg_sample": ecg,
            "lat": cur_lat,
            "lng": cur_lng,
            "signal_quality": "good",
            "ts": now_iso
        }

    def _run_loop(self):
        while not self._stop_event.is_set():
            reading = self._generate_reading()

            if reading:
                # Scenario 9: Network failure - buffer locally!
                if self.scenario == "network_fail":
                    self.buffered_readings.append(reading)
                    print(f"[SIMULATOR] Network drop: buffered sample #{len(self.buffered_readings)}")
                else:
                    try:
                        with httpx.Client(timeout=2.0) as client:
                            resp = client.post(
                                self.target_url,
                                headers={"X-Device-Key": self.device_key},
                                json=reading
                            )
                            self.last_sent_at = datetime.now(timezone.utc)
                    except Exception as exc:
                        # Auto-buffer on real connection failure
                        self.buffered_readings.append(reading)

            time.sleep(1.0)


# Global singleton simulator instance for backend control
global_simulator = VitalSimulator()


if __name__ == "__main__":
    print("=== Launching Standalone IoT Vital Tracker Simulator ===")
    global_simulator.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        global_simulator.stop()
        print("Simulator stopped.")
