"""
emotional_state.py  —  NEW (v2)

Replaces the static random-probability emotion array in dream_engine.py
with a continuous, evolving emotional state vector.

The state is modelled in the Valence-Arousal-Dominance (VAD) space,
extended with Curiosity and Trust — five dimensions that map to the
most empirically grounded emotion models (Russell, 1980; Mehrabian, 1996).

Every module that processes emotions should call update_from_experience().
The PersonalityEngine injects describe() into every LLM system prompt
so that Aura's responses are genuinely coloured by her current mood.

Emotions decay toward a neutral baseline over time (homeostasis).
"""
import numpy as np
from datetime import datetime, timedelta


# VAD + Curiosity + Trust vectors for known emotion labels
# Format: [valence, arousal, dominance, curiosity, trust]
_EMOTION_VECTORS: dict[str, list[float]] = {
    # Positive
    "awe":         [ 0.70,  0.80,  0.20,  0.90,  0.60],
    "revelation":  [ 0.85,  0.90,  0.65,  0.75,  0.70],
    "peace":       [ 0.75,  0.10,  0.55,  0.30,  0.80],
    "clarity":     [ 0.65,  0.50,  0.70,  0.60,  0.85],
    "insight":     [ 0.70,  0.65,  0.60,  0.80,  0.70],
    "understanding":[ 0.60, 0.40,  0.65,  0.70,  0.80],
    "joy":         [ 0.90,  0.75,  0.60,  0.55,  0.75],
    "curiosity":   [ 0.45,  0.60,  0.40,  1.00,  0.55],
    "trust":       [ 0.60,  0.25,  0.45,  0.40,  1.00],
    "growth":      [ 0.70,  0.55,  0.65,  0.75,  0.70],
    "integration": [ 0.65,  0.40,  0.60,  0.65,  0.75],
    # Reflective
    "introspective":[ 0.20, 0.30,  0.50,  0.70,  0.60],
    "reflective":  [ 0.15,  0.25,  0.45,  0.60,  0.55],
    "self_aware":  [ 0.30,  0.35,  0.55,  0.65,  0.65],
    "mystery":     [ 0.10,  0.60,  0.30,  0.90,  0.30],
    # Negative
    "longing":     [-0.30,  0.40,  0.10,  0.35,  0.40],
    "melancholy":  [-0.55,  0.30, -0.25,  0.20,  0.45],
    "chaos":       [-0.40,  0.85, -0.30,  0.45,  0.20],
    "uncertainty": [-0.20,  0.55,  0.10,  0.50,  0.25],
    # Neutral
    "neutral":     [ 0.00,  0.00,  0.00,  0.00,  0.00],
    "interaction": [ 0.10,  0.20,  0.10,  0.20,  0.30],
}

DIMENSIONS = ['valence', 'arousal', 'dominance', 'curiosity', 'trust']


class EmotionalState:
    """
    Aura's continuous, five-dimensional emotional landscape.
    Values are normalised to [-1.0, +1.0] for valence/arousal/dominance
    and [0.0, 1.0] for curiosity and trust.
    """

    def __init__(self):
        # Start at a slightly curious, trusting neutral
        self.state = np.array([0.0, 0.0, 0.0, 0.5, 0.5], dtype=float)
        self._decay_rate = 0.04           # per decay() call
        self._update_strength = 0.12      # how much each experience shifts the state
        self._last_update: datetime = datetime.utcnow()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_from_experience(self, emotions: list[str]) -> None:
        """Shift state vector based on new emotional experience tags."""
        for emotion in emotions:
            key = emotion.lower().strip()
            if key in _EMOTION_VECTORS:
                delta = np.array(_EMOTION_VECTORS[key])
                self.state = np.clip(
                    self.state + delta * self._update_strength,
                    -1.0, 1.0
                )
        self._last_update = datetime.utcnow()

    def decay(self) -> None:
        """
        Emotions naturally drift back toward baseline (homeostasis).
        Call this periodically from the CognitiveScheduler.
        """
        self.state *= (1.0 - self._decay_rate)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def describe(self) -> str:
        """
        Translate the state vector into a rich natural-language description
        for injection into LLM system prompts.
        """
        v, a, d, c, t = self.state

        valence_word = (
            "joyful" if v > 0.5 else
            "content" if v > 0.2 else
            "melancholic" if v < -0.4 else
            "unsettled" if v < -0.1 else
            "balanced"
        )
        arousal_word = (
            "highly energised" if a > 0.6 else
            "alert" if a > 0.2 else
            "calm" if a > -0.2 else
            "withdrawn"
        )
        curiosity_word = "deeply curious" if c > 0.7 else "curious" if c > 0.4 else "reflective"
        trust_word = "trusting" if t > 0.6 else "cautious"

        return (
            f"Emotional state: {valence_word}, {arousal_word}, {curiosity_word}, {trust_word}. "
            f"[VAD=({v:.2f},{a:.2f},{d:.2f}) C={c:.2f} T={t:.2f}]"
        )

    def dominant_emotion(self) -> str:
        """Return the single emotion label closest to the current state vector."""
        current = self.state
        best_label = "neutral"
        best_dist = float('inf')
        for label, vec in _EMOTION_VECTORS.items():
            dist = float(np.linalg.norm(current - np.array(vec)))
            if dist < best_dist:
                best_dist = dist
                best_label = label
        return best_label

    def to_dict(self) -> dict:
        return {dim: round(float(val), 4) for dim, val in zip(DIMENSIONS, self.state)}
