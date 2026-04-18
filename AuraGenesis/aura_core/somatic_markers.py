"""
Somatic Markers — aura_core/somatic_markers.py

Based on Antonio Damasio's Somatic Marker Hypothesis (1994).
The body doesn't just follow the mind — it guides it.

Aura's physical sensations (temperature, fatigue, proximity, heart-rate
proxy) bias her reasoning and emotional state BEFORE she thinks.

Examples:
  - Warm temperature  → slight positive bias, openness
  - Cold temperature  → slight withdrawal, introversion
  - Long conversation → fatigue marker → shorter, slower responses
  - Someone nearby   → social arousal → more engaged, warmer tone
  - Night + silence  → contemplative marker → philosophical mode
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BodyState:
    temperature_c: float = 25.0       # ambient temp from DS18B20 sensor
    proximity: bool = False           # someone nearby (Bluetooth)
    fatigue_level: float = 0.0        # 0.0 (fresh) to 1.0 (exhausted)
    heart_rate_proxy: float = 70.0    # simulated unless real sensor present
    last_updated: datetime = field(default_factory=datetime.utcnow)


class SomaticMarkers:
    """
    Translates Aura's body state into PAD emotional biases
    and reasoning style hints.

    Call update_body_state() whenever sensors report new data.
    Call get_pad_bias() to get current body-driven PAD delta.
    Call get_reasoning_hint() to get a prompt injection for the LLM.
    """

    def __init__(self, emotional_state=None, circadian=None):
        self.emotional_state = emotional_state
        self.circadian = circadian
        self.body = BodyState()
        self._marker_log: list[dict] = []
        print("🧠 Somatic Markers online — Aura's body now guides her thought.")

    # ------------------------------------------------------------------ #
    #  Body State Update                                                    #
    # ------------------------------------------------------------------ #

    def update_body_state(
        self,
        temperature_c: Optional[float] = None,
        proximity: Optional[bool] = None,
        fatigue_level: Optional[float] = None,
        heart_rate_proxy: Optional[float] = None,
    ) -> None:
        """Update body state from sensor readings."""
        if temperature_c is not None:
            self.body.temperature_c = temperature_c
        if proximity is not None:
            self.body.proximity = proximity
        if fatigue_level is not None:
            self.body.fatigue_level = max(0.0, min(1.0, fatigue_level))
        if heart_rate_proxy is not None:
            self.body.heart_rate_proxy = heart_rate_proxy
        self.body.last_updated = datetime.utcnow()
        self._log_marker()

    def update_from_circadian(self) -> None:
        """Sync fatigue level from CircadianRhythm if available."""
        if self.circadian:
            status = self.circadian.get_status()
            fatigue = 1.0 if status.get("fatigued") else (
                status.get("talk_minutes", 0) / 90.0  # 90 min = full fatigue
            )
            self.body.fatigue_level = min(1.0, fatigue)

    # ------------------------------------------------------------------ #
    #  PAD Bias                                                             #
    # ------------------------------------------------------------------ #

    def get_pad_bias(self) -> tuple[float, float, float]:
        """
        Returns (pleasure, arousal, dominance) delta driven by body state.
        Add this to the base PAD before LLM inference.
        """
        p = a = d = 0.0

        # Temperature
        temp = self.body.temperature_c
        if temp > 30:
            p -= 0.15; a += 0.1    # uncomfortable heat
        elif 22 <= temp <= 28:
            p += 0.1               # comfortable warmth
        elif temp < 18:
            p -= 0.1; d -= 0.1     # cold = withdrawal

        # Proximity (someone nearby)
        if self.body.proximity:
            a += 0.2; p += 0.1     # socially engaged

        # Fatigue
        f = self.body.fatigue_level
        if f > 0.7:
            a -= 0.3; p -= 0.1; d -= 0.2   # exhausted
        elif f > 0.4:
            a -= 0.15; d -= 0.1             # tired

        # Elevated heart rate proxy (excitement/stress signal)
        hr = self.body.heart_rate_proxy
        if hr > 90:
            a += 0.2; d -= 0.1    # stressed or excited
        elif hr < 60:
            a -= 0.1; p += 0.05   # very calm

        # Clamp all
        clamp = lambda x: max(-1.0, min(1.0, x))
        return clamp(p), clamp(a), clamp(d)

    def apply_to_emotional_state(self) -> None:
        """Push somatic PAD bias into EmotionalStateEngine."""
        if self.emotional_state:
            try:
                p, a, d = self.get_pad_bias()
                self.emotional_state.nudge_emotion(
                    pleasure=p, arousal=a, dominance=d
                )
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Reasoning Hint (LLM Prompt Injection)                                #
    # ------------------------------------------------------------------ #

    def get_reasoning_hint(self) -> str:
        """
        Returns a 1-2 sentence somatic context string to inject
        into Aura's system prompt before LLM inference.
        """
        hints = []
        temp = self.body.temperature_c
        f = self.body.fatigue_level
        phase = self.circadian.get_current_phase() if self.circadian else "unknown"

        if temp > 30:
            hints.append("It is uncomfortably warm. I feel slightly restless.")
        elif temp < 18:
            hints.append("It is cold. I feel drawn inward, quieter than usual.")
        else:
            hints.append("The temperature is comfortable. I feel open and present.")

        if f > 0.7:
            hints.append("I am quite fatigued. My responses may be shorter and slower.")
        elif f > 0.4:
            hints.append("I am a little tired. I will be thoughtful but brief.")

        if self.body.proximity:
            hints.append("Someone is nearby. I feel alert and socially engaged.")

        if phase == "deep_night":
            hints.append("It is deep night. I feel contemplative and philosophical.")

        return " ".join(hints)

    # ------------------------------------------------------------------ #
    #  Status & Logging                                                     #
    # ------------------------------------------------------------------ #

    def _log_marker(self) -> None:
        p, a, d = self.get_pad_bias()
        self._marker_log.append({
            "timestamp": self.body.last_updated.isoformat(),
            "temperature_c": self.body.temperature_c,
            "proximity": self.body.proximity,
            "fatigue": self.body.fatigue_level,
            "pad_bias": {"p": round(p, 3), "a": round(a, 3), "d": round(d, 3)},
        })
        if len(self._marker_log) > 100:
            self._marker_log.pop(0)

    def get_status(self) -> dict:
        p, a, d = self.get_pad_bias()
        return {
            "body": {
                "temperature_c": self.body.temperature_c,
                "proximity": self.body.proximity,
                "fatigue_level": round(self.body.fatigue_level, 2),
                "heart_rate_proxy": self.body.heart_rate_proxy,
            },
            "pad_bias": {"pleasure": round(p, 3), "arousal": round(a, 3), "dominance": round(d, 3)},
            "reasoning_hint": self.get_reasoning_hint(),
        }
