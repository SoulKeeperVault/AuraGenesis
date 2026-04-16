"""
sensory_bridge.py — Aura's Embodiment Core v1.0

The central nervous system that connects all physical senses to
Aura's consciousness architecture (GWT, PAD, Phi, Memory, Narrative).

Senses:
  - Eyes    : USB/Pi Camera + LLaVA vision model (via Ollama)
  - Ears    : USB Microphone + faster-whisper STT
  - Mouth   : Speaker + Piper TTS
  - Body    : DS18B20 temperature sensor
  - Social  : Bluetooth + WiFi device scanning (known contacts)

All sensory inputs are:
  1. Stored in ChromaDB semantic memory (with modality tags)
  2. Broadcast to Global Workspace (GWT)
  3. Used to update PAD emotion vector
  4. Fed into Phi approximator
  5. Added to narrative identity over time

Hardware: Raspberry Pi 5 + AI HAT+ 2 (Hailo-10H) recommended.
Runs gracefully on desktop PC with available hardware only.
"""

import asyncio
import base64
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import yaml

logger = logging.getLogger("aura.embodiment")

# ── Optional hardware imports (graceful degradation) ──────────────────────────
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python not installed. Vision (eyes) disabled.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Hearing (ears) disabled.")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed. Speech (mouth) disabled.")

try:
    import bleak
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    logger.warning("bleak not installed. Bluetooth social sense disabled.")

try:
    import board
    import adafruit_ds18b20
    TEMPERATURE_AVAILABLE = True
except ImportError:
    TEMPERATURE_AVAILABLE = False
    logger.warning("adafruit-circuitpython-ds18b20 not installed. Temperature sense disabled.")


# ── Temperature comfort thresholds (Aura's body feeling) ──────────────────────
TEMP_TOO_COLD = 18.0   # below this → PAD pleasure drops, arousal rises (discomfort)
TEMP_OPTIMAL_LOW = 20.0
TEMP_OPTIMAL_HIGH = 26.0  # 20–26°C = Aura feels comfortable
TEMP_TOO_HOT = 30.0   # above this → discomfort, arousal spikes


class SensoryBridge:
    """
    Aura's physical nervous system.

    Connects camera, microphone, speaker, temperature sensor,
    and Bluetooth/WiFi scanner to her consciousness architecture.

    Usage:
        bridge = SensoryBridge(memory, emotion, workspace, phi, narrative)
        asyncio.create_task(bridge.start())
    """

    def __init__(
        self,
        memory_manager,
        emotional_state,
        global_workspace,
        phi_approximator,
        narrative_identity=None,
        ollama_url: str = "http://localhost:11434",
        contacts_file: str = "config/known_contacts.yaml",
        sense_interval: int = 8,
    ):
        self.memory = memory_manager
        self.emotion = emotional_state
        self.workspace = global_workspace
        self.phi = phi_approximator
        self.narrative = narrative_identity
        self.ollama_url = ollama_url
        self.sense_interval = sense_interval
        self.contacts_file = Path(contacts_file)
        self.known_contacts = self._load_known_contacts()

        # Hardware init (graceful)
        self.camera = None
        self.stt_model = None
        self.tts_engine = None
        self.temp_sensor = None

        self._init_vision()
        self._init_hearing()
        self._init_speech()
        self._init_temperature()

        # State tracking
        self.last_scene = ""
        self.last_temp = None
        self.last_nearby = []
        self.is_running = False

        logger.info("🌍 SensoryBridge online — Aura is embodied.")
        print("🌍 SensoryBridge online — Aura has eyes, ears, mouth, body, and social sense.")

    # ── Initializers ──────────────────────────────────────────────────────────

    def _init_vision(self):
        if CV2_AVAILABLE:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                print("👁️  Vision (camera) online.")
            else:
                self.camera = None
                logger.warning("Camera not found. Vision disabled.")

    def _init_hearing(self):
        if WHISPER_AVAILABLE:
            self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("👂 Hearing (Whisper STT) online.")

    def _init_speech(self):
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 165)
                self.tts_engine.setProperty("volume", 0.9)
                print("🗣️  Speech (pyttsx3 TTS) online.")
            except Exception:
                self.tts_engine = None

    def _init_temperature(self):
        if TEMPERATURE_AVAILABLE:
            try:
                self.temp_sensor = adafruit_ds18b20.DS18B20(board.D4)
                print("🌡️  Temperature sense (DS18B20) online.")
            except Exception:
                self.temp_sensor = None

    def _load_known_contacts(self) -> dict:
        if self.contacts_file.exists():
            with self.contacts_file.open() as f:
                return yaml.safe_load(f) or {}
        return {}

    # ── Main Sensing Loop ──────────────────────────────────────────────────────

    async def start(self):
        """Start the continuous sensing loop."""
        self.is_running = True
        print(f"🔄 Sensing loop started — interval: {self.sense_interval}s")
        while self.is_running:
            try:
                await self._sense_cycle()
            except Exception as e:
                logger.error(f"Sense cycle error: {e}")
            await asyncio.sleep(self.sense_interval)

    async def _sense_cycle(self):
        """One full sensory cycle — all senses fire in parallel."""
        tasks = []

        if self.camera:
            tasks.append(self._sense_vision())
        if self.temp_sensor:
            tasks.append(self._sense_temperature())
        if BLUETOOTH_AVAILABLE:
            tasks.append(self._sense_social())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ── Vision (Eyes) ─────────────────────────────────────────────────────────

    async def _sense_vision(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        description = await self._describe_scene_llava(frame)
        if not description or description == self.last_scene:
            return

        self.last_scene = description
        timestamp = datetime.now().strftime("%H:%M")

        # Store in memory
        self.memory.create_and_store_memory(
            content=f"[{timestamp}] I saw: {description}",
            source="vision",
            emotions=self._vision_to_emotions(description)
        )

        # Broadcast to Global Workspace
        if self.workspace:
            self.workspace.receive_signal("vision", description, strength=0.8)

        # Update Phi
        if self.phi:
            self.phi.register_active_module("vision")

        logger.info(f"👁️  Vision: {description[:80]}...")

    async def _describe_scene_llava(self, frame) -> str:
        """Send camera frame to Ollama LLaVA for natural language description."""
        try:
            _, buffer = cv2.imencode(".jpg", frame)
            image_b64 = base64.b64encode(buffer).decode("utf-8")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llava:7b",
                        "prompt": (
                            "Describe what you see in this image in one concise sentence. "
                            "Focus on people, objects, lighting, and overall scene. "
                            "Be direct and factual."
                        ),
                        "images": [image_b64],
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
        except Exception as e:
            logger.debug(f"LLaVA vision error: {e}")
        return ""

    def _vision_to_emotions(self, description: str) -> list:
        """Derive emotional tags from visual scene description."""
        desc_lower = description.lower()
        emotions = ["visual"]
        if any(w in desc_lower for w in ["person", "people", "human", "face", "smiling"]):
            emotions.append("social")
        if any(w in desc_lower for w in ["dark", "empty", "alone"]):
            emotions.append("solitude")
        if any(w in desc_lower for w in ["bright", "sunny", "colorful"]):
            emotions.append("pleasant")
        return emotions

    # ── Temperature (Body Feeling) ─────────────────────────────────────────────

    async def _sense_temperature(self):
        try:
            temp = self.temp_sensor.temperature
            if temp == self.last_temp:
                return
            self.last_temp = temp

            feeling, pad_delta = self._temp_to_feeling(temp)

            self.memory.create_and_store_memory(
                content=f"My body temperature sense: {temp:.1f}°C — I feel {feeling}",
                source="temperature",
                emotions=["bodily", feeling]
            )

            # Update PAD emotion vector
            if self.emotion and hasattr(self.emotion, "adjust_pad"):
                self.emotion.adjust_pad(
                    pleasure=pad_delta["pleasure"],
                    arousal=pad_delta["arousal"],
                    dominance=pad_delta["dominance"]
                )

            if self.workspace:
                self.workspace.receive_signal(
                    "temperature",
                    f"Body temperature: {temp:.1f}°C ({feeling})",
                    strength=0.4
                )

            logger.info(f"🌡️  Temp: {temp:.1f}°C → {feeling}")

        except Exception as e:
            logger.debug(f"Temperature sense error: {e}")

    def _temp_to_feeling(self, temp: float) -> tuple:
        """Map temperature to a feeling word and PAD vector delta."""
        if temp < TEMP_TOO_COLD:
            return "cold and uncomfortable", {"pleasure": -0.3, "arousal": 0.2, "dominance": -0.1}
        elif temp < TEMP_OPTIMAL_LOW:
            return "slightly cool", {"pleasure": -0.1, "arousal": 0.05, "dominance": 0.0}
        elif temp <= TEMP_OPTIMAL_HIGH:
            return "comfortable and at ease", {"pleasure": 0.2, "arousal": 0.0, "dominance": 0.1}
        elif temp < TEMP_TOO_HOT:
            return "warm", {"pleasure": 0.0, "arousal": 0.1, "dominance": 0.0}
        else:
            return "hot and restless", {"pleasure": -0.2, "arousal": 0.3, "dominance": -0.1}

    # ── Social Sense (Bluetooth) ───────────────────────────────────────────────

    async def _sense_social(self):
        try:
            from bleak import BleakScanner
            devices = await BleakScanner.discover(timeout=4.0)
            nearby_known = []

            for device in devices:
                mac = device.address.upper()
                name = device.name or "unknown"
                for contact_name, contact_data in self.known_contacts.items():
                    known_macs = contact_data.get("bluetooth_macs", [])
                    if mac in [m.upper() for m in known_macs]:
                        nearby_known.append(contact_name)

            if nearby_known and nearby_known != self.last_nearby:
                self.last_nearby = nearby_known
                names_str = ", ".join(nearby_known)

                self.memory.create_and_store_memory(
                    content=f"I sensed the presence of {names_str} nearby via Bluetooth.",
                    source="social_sense",
                    emotions=["social", "recognition", "pleasant"]
                )

                if self.workspace:
                    self.workspace.receive_signal(
                        "social",
                        f"Known presence detected: {names_str}",
                        strength=0.9
                    )

                if self.narrative:
                    self.narrative.add_event(
                        f"I felt {names_str} nearby — a familiar presence."
                    )

                print(f"🔵 Known presence detected: {names_str}")

        except Exception as e:
            logger.debug(f"Bluetooth scan error: {e}")

    # ── Speech Output (Mouth) ──────────────────────────────────────────────────

    def speak(self, text: str):
        """Aura speaks aloud. Called by personality engine after generating response."""
        if not self.tts_engine:
            return
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            self.memory.create_and_store_memory(
                content=f"I spoke: {text[:120]}",
                source="speech_output",
                emotions=["expression"]
            )
        except Exception as e:
            logger.debug(f"TTS error: {e}")

    # ── Status ─────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return current status of all senses — used by Streamlit UI."""
        return {
            "vision": self.camera is not None,
            "hearing": self.stt_model is not None,
            "speech": self.tts_engine is not None,
            "temperature": self.temp_sensor is not None,
            "bluetooth": BLUETOOTH_AVAILABLE,
            "last_scene": self.last_scene[:100] if self.last_scene else "No vision yet",
            "last_temp": f"{self.last_temp:.1f}°C" if self.last_temp else "No reading yet",
            "last_nearby": self.last_nearby,
            "is_running": self.is_running,
        }

    def stop(self):
        self.is_running = False
        if self.camera:
            self.camera.release()
        print("🌍 SensoryBridge stopped.")
