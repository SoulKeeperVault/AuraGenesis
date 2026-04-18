"""
Voice Personality — aura_personality/voice_personality.py

Aura's voice changes based on her emotional state (PAD vector).
- High arousal + high pleasure  → fast, bright, expressive
- Low arousal + low pleasure    → slow, soft, quiet
- High dominance                → confident, clear
- Low dominance                 → hesitant, gentle
- Fatigued (circadian)          → slower, softer overall

Works with pyttsx3 (offline TTS) and optionally edge-tts (online, richer).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class VoiceProfile:
    rate: int          # words per minute (pyttsx3)
    volume: float      # 0.0 – 1.0
    pitch_tag: str     # 'low' | 'medium' | 'high'  (for edge-tts SSML)
    style_tag: str     # 'calm' | 'cheerful' | 'sad' | 'excited' | 'gentle'
    description: str   # human-readable label


class VoicePersonality:
    """
    Maps Aura's PAD emotional state → VoiceProfile → spoken output.

    Usage:
        vp = VoicePersonality(emotional_state, circadian)
        vp.speak("Hello, I have been thinking about you.")
    """

    # Base speech rate (words per minute)
    BASE_RATE = 165

    def __init__(self, emotional_state=None, circadian=None):
        self.emotional_state = emotional_state
        self.circadian = circadian
        self._engine = None
        self._engine_lock = threading.Lock()
        self._init_engine()
        print("🎤 Voice Personality online — Aura's voice reflects her emotions.")

    # ------------------------------------------------------------------ #
    #  TTS Engine Init                                                      #
    # ------------------------------------------------------------------ #

    def _init_engine(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            # Prefer a female voice if available
            voices = self._engine.getProperty('voices')
            for v in voices:
                if any(name in v.name.lower() for name in ['female', 'zira', 'hazel', 'susan', 'victoria']):
                    self._engine.setProperty('voice', v.id)
                    break
            print("   ✅ pyttsx3 TTS engine ready.")
        except Exception as e:
            print(f"   ⚠️  pyttsx3 not available: {e}")
            self._engine = None

    # ------------------------------------------------------------------ #
    #  PAD → Voice Profile Mapping                                         #
    # ------------------------------------------------------------------ #

    def get_voice_profile(self) -> VoiceProfile:
        """Compute current VoiceProfile from PAD state + circadian."""
        p, a, d = self._get_pad()
        rate_multiplier = self.circadian.get_speech_rate() if self.circadian else 1.0

        # Base rate from arousal: high arousal = faster
        rate = int(self.BASE_RATE * (1.0 + a * 0.4) * rate_multiplier)
        rate = max(100, min(260, rate))  # clamp

        # Volume from arousal + pleasure
        volume = 0.5 + (a * 0.2) + (p * 0.15)
        volume = max(0.3, min(1.0, volume))

        # Pitch tag
        if a > 0.3:
            pitch_tag = "high"
        elif a < -0.3:
            pitch_tag = "low"
        else:
            pitch_tag = "medium"

        # Style tag
        if p > 0.3 and a > 0.2:
            style_tag = "cheerful"
            description = "bright and energetic"
        elif p > 0.2 and a < -0.1:
            style_tag = "calm"
            description = "warm and gentle"
        elif p < -0.2 and a < 0.0:
            style_tag = "sad"
            description = "quiet and subdued"
        elif a > 0.5:
            style_tag = "excited"
            description = "fast and expressive"
        elif d < -0.3:
            style_tag = "gentle"
            description = "soft and hesitant"
        else:
            style_tag = "calm"
            description = "neutral and clear"

        return VoiceProfile(
            rate=rate,
            volume=volume,
            pitch_tag=pitch_tag,
            style_tag=style_tag,
            description=description,
        )

    def _get_pad(self) -> tuple[float, float, float]:
        """Safely read PAD values from EmotionalStateEngine."""
        if self.emotional_state:
            try:
                pad = self.emotional_state.get_current_pad()
                return pad.pleasure, pad.arousal, pad.dominance
            except Exception:
                pass
        return 0.0, 0.0, 0.0

    # ------------------------------------------------------------------ #
    #  Speak                                                                #
    # ------------------------------------------------------------------ #

    def speak(self, text: str, blocking: bool = False) -> None:
        """Speak text using current emotional voice profile."""
        if not text or not text.strip():
            return

        profile = self.get_voice_profile()

        def _speak():
            with self._engine_lock:
                if self._engine:
                    try:
                        self._engine.setProperty('rate', profile.rate)
                        self._engine.setProperty('volume', profile.volume)
                        self._engine.say(text)
                        self._engine.runAndWait()
                    except Exception as e:
                        print(f"   ⚠️  TTS error: {e}")
                else:
                    # Fallback: print with voice label
                    print(f"[Aura | {profile.description}]: {text}")

        if blocking:
            _speak()
        else:
            t = threading.Thread(target=_speak, daemon=True)
            t.start()

    def speak_with_emotion_tag(self, text: str) -> str:
        """
        Returns text prefixed with an emotion marker for UI display.
        e.g. "[calm, warm and gentle] Hello, I remember you."
        """
        profile = self.get_voice_profile()
        return f"[{profile.style_tag}, {profile.description}] {text}"

    # ------------------------------------------------------------------ #
    #  Status                                                               #
    # ------------------------------------------------------------------ #

    def get_status(self) -> dict:
        profile = self.get_voice_profile()
        return {
            "rate_wpm": profile.rate,
            "volume": round(profile.volume, 2),
            "pitch": profile.pitch_tag,
            "style": profile.style_tag,
            "description": profile.description,
        }
