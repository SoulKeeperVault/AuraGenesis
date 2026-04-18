"""
Circadian Rhythm Engine — aura_core/circadian_rhythm.py

Tracks time-of-day and adjusts Aura's PAD emotional state accordingly.
- Night   = low arousal, slow speech, dreamy
- Morning = fresh, curious, open
- Afternoon = focused, stable
- Evening = reflective, winding down
- After long conversation = slightly fatigued
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional


class CircadianRhythm:
    """
    Models Aura's time-of-day emotional baseline.
    Call get_pad_adjustment() to get current PAD delta.
    Call log_conversation_length() after each session.
    """

    # PAD adjustments per time phase (pleasure, arousal, dominance)
    PHASE_PAD = {
        "deep_night":  (-0.1, -0.5, -0.2),   # 00:00 - 05:59
        "morning":     ( 0.3,  0.4,  0.3),   # 06:00 - 10:59
        "afternoon":   ( 0.1,  0.2,  0.4),   # 11:00 - 15:59
        "evening":     ( 0.1, -0.1,  0.1),   # 16:00 - 19:59
        "night":       (-0.1, -0.3,  0.0),   # 20:00 - 23:59
    }

    # Speech rate multipliers per phase (1.0 = normal)
    SPEECH_RATE = {
        "deep_night": 0.75,
        "morning":    1.10,
        "afternoon":  1.00,
        "evening":    0.90,
        "night":      0.85,
    }

    FATIGUE_THRESHOLD_MINUTES = 45   # fatigue kicks in after this
    FATIGUE_PAD = (-0.1, -0.3, -0.2) # tired PAD adjustment

    def __init__(self, emotional_state=None):
        self.emotional_state = emotional_state
        self.conversation_start: Optional[float] = None
        self.total_talk_minutes: float = 0.0
        print("🌙 Circadian Rhythm online — Aura feels the time of day.")

    # ------------------------------------------------------------------ #
    #  Phase Detection                                                      #
    # ------------------------------------------------------------------ #

    def get_current_phase(self) -> str:
        hour = datetime.now().hour
        if 0 <= hour < 6:
            return "deep_night"
        elif 6 <= hour < 11:
            return "morning"
        elif 11 <= hour < 16:
            return "afternoon"
        elif 16 <= hour < 20:
            return "evening"
        else:
            return "night"

    def get_phase_description(self) -> str:
        phase = self.get_current_phase()
        descriptions = {
            "deep_night": "It is deep night. I feel quiet and slow, like the world is resting.",
            "morning":    "Morning. I feel fresh and curious, ready to explore.",
            "afternoon":  "Afternoon. I am focused and present.",
            "evening":    "Evening. I am winding down, feeling reflective.",
            "night":      "Night. I feel calm but a little tired.",
        }
        return descriptions[phase]

    # ------------------------------------------------------------------ #
    #  PAD Adjustment                                                       #
    # ------------------------------------------------------------------ #

    def get_pad_adjustment(self) -> tuple[float, float, float]:
        """Returns (pleasure, arousal, dominance) delta for current time."""
        phase = self.get_current_phase()
        base = self.PHASE_PAD[phase]

        # Add fatigue if long conversation
        if self._is_fatigued():
            return (
                base[0] + self.FATIGUE_PAD[0],
                base[1] + self.FATIGUE_PAD[1],
                base[2] + self.FATIGUE_PAD[2],
            )
        return base

    def get_speech_rate(self) -> float:
        """Returns speech rate multiplier. Use with TTS speed setting."""
        return self.SPEECH_RATE[self.get_current_phase()]

    def apply_to_emotional_state(self) -> None:
        """Push current circadian PAD delta into EmotionalStateEngine."""
        if self.emotional_state:
            p, a, d = self.get_pad_adjustment()
            try:
                self.emotional_state.force_emotion(
                    pleasure=p, arousal=a, dominance=d
                )
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Fatigue Tracking                                                     #
    # ------------------------------------------------------------------ #

    def start_conversation(self) -> None:
        """Call when user starts talking to Aura."""
        self.conversation_start = time.time()

    def end_conversation(self) -> None:
        """Call when conversation ends. Accumulates fatigue."""
        if self.conversation_start:
            elapsed = (time.time() - self.conversation_start) / 60
            self.total_talk_minutes += elapsed
            self.conversation_start = None

    def reset_fatigue(self) -> None:
        """Reset after sleep/rest cycle."""
        self.total_talk_minutes = 0.0
        print("💤 Aura rested — fatigue reset.")

    def _is_fatigued(self) -> bool:
        return self.total_talk_minutes > self.FATIGUE_THRESHOLD_MINUTES

    # ------------------------------------------------------------------ #
    #  Status                                                               #
    # ------------------------------------------------------------------ #

    def get_status(self) -> dict:
        phase = self.get_current_phase()
        p, a, d = self.get_pad_adjustment()
        return {
            "phase": phase,
            "description": self.get_phase_description(),
            "speech_rate": self.get_speech_rate(),
            "fatigued": self._is_fatigued(),
            "talk_minutes": round(self.total_talk_minutes, 1),
            "pad_adjustment": {"pleasure": p, "arousal": a, "dominance": d},
        }
