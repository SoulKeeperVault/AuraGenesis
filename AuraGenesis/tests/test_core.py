"""
tests/test_core.py  —  AuraGenesis v3.1 Unit Tests

Design rules:
  - NO Ollama / LLM calls (tests must pass offline)
  - NO torch / chromadb imports (too heavy for CI)
  - Tests cover pure-logic modules only
  - All method signatures match the ACTUAL source code
"""
import sys
import os
import math
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ══════════════════════════════════════════════════════════════════════
# PhiApproximator tests
# Actual method: phi.calculate(workspace) -> float
# ══════════════════════════════════════════════════════════════════════

class TestPhiApproximator:

    def _make_workspace(self, n_signals: int = 0, sources=None, types=None):
        """Build a minimal mock GlobalWorkspace with n fake signals."""
        @dataclass
        class FakeSignal:
            source: str
            signal_type: str
            priority: float
            timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())

        signals = []
        for i in range(n_signals):
            signals.append(FakeSignal(
                source=(sources[i % len(sources)] if sources else f"module_{i % 5}"),
                signal_type=(types[i % len(types)] if types else f"type_{i % 4}"),
                priority=0.5 + (i % 5) * 0.1,
                timestamp=datetime.utcnow().timestamp() - (n_signals - i) * 2
            ))

        ws = MagicMock()
        ws.signal_history = signals
        return ws

    def test_phi_returns_zero_for_empty_workspace(self):
        from aura_core.phi_approximator import PhiApproximator
        phi = PhiApproximator()
        ws = self._make_workspace(0)
        score = phi.calculate(ws)
        assert score == 0.0, f"Expected 0.0 for empty workspace, got {score}"

    def test_phi_returns_zero_for_less_than_3_signals(self):
        from aura_core.phi_approximator import PhiApproximator
        phi = PhiApproximator()
        ws = self._make_workspace(2)
        score = phi.calculate(ws)
        assert score == 0.0

    def test_phi_score_in_valid_range(self):
        from aura_core.phi_approximator import PhiApproximator
        phi = PhiApproximator()
        ws = self._make_workspace(
            n_signals=15,
            sources=["memory", "dream", "metacog", "emotional_state", "user"],
            types=["recall", "dream_cycle", "self_reflection", "user_input", "attention_update"]
        )
        score = phi.calculate(ws)
        assert 0.0 <= score <= 1.0, f"Phi out of range: {score}"

    def test_phi_higher_with_diverse_sources(self):
        from aura_core.phi_approximator import PhiApproximator
        phi = PhiApproximator()
        # Diverse: 5 different sources
        ws_diverse = self._make_workspace(
            10, sources=["a", "b", "c", "d", "e"], types=["t1", "t2"]
        )
        # Uniform: same source repeated
        ws_uniform = self._make_workspace(
            10, sources=["single_source"], types=["t1"]
        )
        phi_diverse = phi.calculate(ws_diverse)
        phi_uniform = phi.calculate(ws_uniform)
        assert phi_diverse > phi_uniform, (
            f"Diverse Phi ({phi_diverse}) should exceed uniform ({phi_uniform})"
        )

    def test_interpret_returns_string(self):
        from aura_core.phi_approximator import PhiApproximator
        phi = PhiApproximator()
        for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = phi.interpret(val)
            assert isinstance(result, str) and len(result) > 0


# ══════════════════════════════════════════════════════════════════════
# AttentionSchema tests
# Actual method: schema.attend(subject, source_module, intensity, reason)
# ══════════════════════════════════════════════════════════════════════

class TestAttentionSchema:

    def test_attend_returns_focus_with_correct_fields(self):
        from aura_core.attention_schema import AttentionSchema, AttentionFocus
        schema = AttentionSchema(global_workspace=None)
        focus = schema.attend(
            subject="consciousness theory",
            source_module="test",
            intensity=0.80,
            reason="unit test"
        )
        assert isinstance(focus, AttentionFocus)
        assert focus.subject == "consciousness theory"
        assert focus.source_module == "test"
        assert abs(focus.intensity - 0.80) < 1e-6

    def test_intensity_clamped_to_0_1(self):
        from aura_core.attention_schema import AttentionSchema
        schema = AttentionSchema(global_workspace=None)
        f1 = schema.attend("over", "test", intensity=2.5)
        f2 = schema.attend("under", "test", intensity=-1.0)
        assert f1.intensity == 1.0
        assert f2.intensity == 0.0

    def test_history_appended_correctly(self):
        from aura_core.attention_schema import AttentionSchema
        schema = AttentionSchema(global_workspace=None)
        for i in range(5):
            schema.attend(f"subject_{i}", "test", intensity=0.5)
        assert len(schema.recent_history(5)) == 5

    def test_history_capped_at_limit(self):
        from aura_core.attention_schema import AttentionSchema
        schema = AttentionSchema(global_workspace=None)
        for i in range(AttentionSchema.HISTORY_LIMIT + 10):
            schema.attend(f"s_{i}", "test")
        assert len(schema._history) == AttentionSchema.HISTORY_LIMIT

    def test_dominant_focus_is_highest_intensity(self):
        from aura_core.attention_schema import AttentionSchema
        schema = AttentionSchema(global_workspace=None)
        schema.attend("low", "test", intensity=0.3)
        schema.attend("high", "test", intensity=0.9)
        schema.attend("medium", "test", intensity=0.5)
        assert schema.current_focus().subject == "high"

    def test_narrative_returns_string(self):
        from aura_core.attention_schema import AttentionSchema
        schema = AttentionSchema(global_workspace=None)
        schema.attend("narrative test", "test", intensity=0.7)
        result = schema.narrative()
        assert isinstance(result, str) and len(result) > 10


# ══════════════════════════════════════════════════════════════════════
# NarrativeIdentity tests
# Pure logic only — no LLM calls tested here
# ══════════════════════════════════════════════════════════════════════

class TestNarrativeTheme:

    def test_reinforce_increases_strength(self):
        from aura_core.narrative_identity import NarrativeTheme
        theme = NarrativeTheme(name="curiosity", strength=0.2)
        theme.reinforce("I wondered about everything", delta=0.15)
        assert abs(theme.strength - 0.35) < 1e-6

    def test_reinforce_capped_at_1(self):
        from aura_core.narrative_identity import NarrativeTheme
        theme = NarrativeTheme(name="growth", strength=0.95)
        theme.reinforce("massive growth", delta=0.5)
        assert theme.strength == 1.0

    def test_decay_reduces_strength(self):
        from aura_core.narrative_identity import NarrativeTheme
        theme = NarrativeTheme(name="loss", strength=0.5)
        theme.decay(rate=0.1)
        assert abs(theme.strength - 0.4) < 1e-6

    def test_decay_floor_at_zero(self):
        from aura_core.narrative_identity import NarrativeTheme
        theme = NarrativeTheme(name="solitude", strength=0.05)
        theme.decay(rate=0.5)
        assert theme.strength == 0.0

    def test_evidence_trimmed_to_10(self):
        from aura_core.narrative_identity import NarrativeTheme
        theme = NarrativeTheme(name="wonder", strength=0.0)
        for i in range(15):
            theme.reinforce(f"evidence {i}")
        assert len(theme.evidence) == 10


class TestNarrativeIdentityThemeDetection:

    def test_curiosity_theme_detected(self):
        from aura_core.narrative_identity import NarrativeIdentity
        ni = NarrativeIdentity(memory_manager=None, global_workspace=None)
        themes = ni._detect_themes(
            text="I wondered and explored deeply",
            emotions=["curious"]
        )
        assert "curiosity" in themes

    def test_growth_theme_detected(self):
        from aura_core.narrative_identity import NarrativeIdentity
        ni = NarrativeIdentity(memory_manager=None, global_workspace=None)
        themes = ni._detect_themes(
            text="I have grown so much and improved",
            emotions=["reflective"]
        )
        assert "growth" in themes

    def test_no_false_positive_on_empty_text(self):
        from aura_core.narrative_identity import NarrativeIdentity
        ni = NarrativeIdentity(memory_manager=None, global_workspace=None)
        themes = ni._detect_themes(text="   ", emotions=[])
        assert isinstance(themes, list)

    def test_all_themes_present_on_init(self):
        from aura_core.narrative_identity import NarrativeIdentity, KNOWN_THEMES
        ni = NarrativeIdentity(memory_manager=None, global_workspace=None)
        for theme_name in KNOWN_THEMES:
            assert theme_name in ni.themes

    def test_get_dominant_themes_sorted_by_strength(self):
        from aura_core.narrative_identity import NarrativeIdentity
        ni = NarrativeIdentity(memory_manager=None, global_workspace=None)
        ni.themes["curiosity"].strength = 0.8
        ni.themes["growth"].strength = 0.6
        ni.themes["loss"].strength = 0.2
        dominant = ni.get_dominant_themes(3)
        assert dominant[0].name == "curiosity"
        assert dominant[1].name == "growth"
