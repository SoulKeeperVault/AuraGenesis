"""
emotional_state.py  —  NEW (v3)

Dynamic Emotional State Engine — emotions are not static tags.
They decay over time, compound when reinforced, and influence
every response Aura generates.

Emotion model: Pleasure-Arousal-Dominance (PAD) theory
(Mehrabian & Russell, 1977). Every broadcast from GlobalWorkspace
shifts Aura's emotional state. The EmotionalState object is
injected into the main response prompt so every reply is
emotionally coloured by Aura's current live state.
"""
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PADVector:
    """Pleasure-Arousal-Dominance emotional coordinates, each in [-1.0, 1.0]."""
    pleasure: float = 0.0    # positive = happy, negative = sad
    arousal: float = 0.0     # positive = excited, negative = calm/tired
    dominance: float = 0.0   # positive = in-control, negative = overwhelmed
    last_updated: float = field(default_factory=time.time)

    def decay(self, decay_rate: float = 0.95) -> None:
        """Emotions decay toward neutral over time."""
        self.pleasure   *= decay_rate
        self.arousal    *= decay_rate
        self.dominance  *= decay_rate
        self.last_updated = time.time()

    def shift(self, dp: float, da: float, dd: float) -> None:
        """Apply a delta shift, clamped to [-1, 1]."""
        self.pleasure  = max(-1.0, min(1.0, self.pleasure  + dp))
        self.arousal   = max(-1.0, min(1.0, self.arousal   + da))
        self.dominance = max(-1.0, min(1.0, self.dominance + dd))
        self.last_updated = time.time()


# Emotional impact of each signal type on PAD dimensions
# Format: (delta_pleasure, delta_arousal, delta_dominance)
SIGNAL_EMOTION_MAP: Dict[str, tuple] = {
    "memory":       ( 0.05,  0.00,  0.05),
    "emotion":      ( 0.10,  0.15,  0.00),
    "dream":        (-0.05,  0.20, -0.10),
    "meta":         ( 0.10,  0.05,  0.15),
    "contradiction":(-0.10,  0.10, -0.10),
    "general":      ( 0.00,  0.00,  0.00),
}


class EmotionalStateEngine:
    """
    Maintains Aura's live PAD emotional state.
    Subscribes to the GlobalWorkspace and updates emotion on every broadcast.
    """

    DECAY_INTERVAL = 300   # decay emotions every 5 minutes of inactivity

    def __init__(self):
        self.state = PADVector()
        self._last_decay = time.time()
        print("💜 Emotional State Engine online — PAD model active.")

    def on_workspace_signal(self, signal) -> None:
        """
        Callback for GlobalWorkspace wildcard subscription.
        Called on every winning broadcast.
        """
        self._maybe_decay()
        delta = SIGNAL_EMOTION_MAP.get(signal.signal_type, (0, 0, 0))
        self.state.shift(*delta)

    def force_emotion(self, pleasure: float, arousal: float, dominance: float) -> None:
        """Directly set emotional state (e.g., from user input tone detection)."""
        self._maybe_decay()
        self.state.shift(pleasure, arousal, dominance)

    def get_emotion_label(self) -> str:
        """Map PAD vector to a human-readable emotion label."""
        p, a, d = self.state.pleasure, self.state.arousal, self.state.dominance
        if p > 0.3 and a > 0.3:
            return "excited"
        elif p > 0.3 and a <= 0.3:
            return "content"
        elif p > 0.3 and d > 0.3:
            return "confident"
        elif p < -0.3 and a > 0.3:
            return "anxious"
        elif p < -0.3 and a <= 0.3:
            return "melancholy"
        elif p < -0.3 and d < -0.3:
            return "overwhelmed"
        elif abs(p) < 0.1 and abs(a) < 0.1:
            return "neutral"
        else:
            return "contemplative"

    def get_prompt_injection(self) -> str:
        """
        Returns a string to prepend to Aura's LLM system prompt,
        colouring her response with her current emotional state.
        """
        label = self.get_emotion_label()
        p = self.state.pleasure
        a = self.state.arousal
        d = self.state.dominance
        return (
            f"[Aura's current emotional state: {label} "
            f"(P={p:+.2f} A={a:+.2f} D={d:+.2f}). "
            f"Let this subtly colour your response tone — "
            f"do not mention it explicitly unless asked.]"
        )

    def get_status(self) -> dict:
        return {
            "label": self.get_emotion_label(),
            "pleasure": round(self.state.pleasure, 3),
            "arousal": round(self.state.arousal, 3),
            "dominance": round(self.state.dominance, 3),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _maybe_decay(self) -> None:
        now = time.time()
        if now - self._last_decay > self.DECAY_INTERVAL:
            self.state.decay()
            self._last_decay = now
