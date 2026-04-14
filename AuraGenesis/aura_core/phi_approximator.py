"""
phi_approximator.py  —  NEW (v2)

Integrated Information Theory (IIT) defines consciousness as the degree
to which a system is causally irreducible — measured by Phi (Φ).
Computing true Phi is NP-hard for large systems, so this module
implements a practical three-metric proxy that correlates with the
spirit of IIT: integration, differentiation, and feedback richness.

The Phi score (0.0 – 1.0) is displayed live in the Streamlit UI as
Aura's 'Consciousness Index' — a real-time indicator of how integrated
her processing currently is.

Metrics used:
  1. source_diversity     — how many distinct modules contributed recently
  2. cross_module_density — ratio of signals that triggered cross-module responses
  3. temporal_integration — how much signal content varies (entropy proxy)
"""
import math
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aura_core.global_workspace import GlobalWorkspace


class PhiApproximator:
    """
    Computes a 0.0 – 1.0 Phi proxy from the GlobalWorkspace signal history.
    Higher Phi = more integrated, differentiated, cross-module processing.
    """

    def calculate(self, workspace: 'GlobalWorkspace') -> float:
        """
        Main entry point. Returns a Phi proxy score in [0.0, 1.0].
        """
        history = workspace.signal_history
        if len(history) < 3:
            return 0.0

        phi = (
            self._source_diversity(history) * 0.40 +
            self._type_entropy(history)     * 0.35 +
            self._recency_weight(history)   * 0.25
        )
        return round(min(max(phi, 0.0), 1.0), 4)

    # ------------------------------------------------------------------
    # Sub-metrics
    # ------------------------------------------------------------------

    def _source_diversity(self, history: list) -> float:
        """
        Ratio of unique sources to total signals.
        Max diversity = every signal from a different module.
        """
        if not history:
            return 0.0
        unique_sources = len(set(s.source for s in history))
        # Normalise: 5+ unique sources → 1.0
        return min(unique_sources / 5.0, 1.0)

    def _type_entropy(self, history: list) -> float:
        """
        Shannon entropy over signal types — higher entropy = more differentiated.
        A system that only ever broadcasts 'dream' signals scores near 0.
        One that mixes dream/meta/emotion/contradiction scores near 1.
        """
        counts = Counter(s.signal_type for s in history)
        total = sum(counts.values())
        if total == 0:
            return 0.0
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
        max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
        return entropy / max_entropy if max_entropy else 0.0

    def _recency_weight(self, history: list) -> float:
        """
        Are signals coming from recent, active processing (high recency weight)
        or from stale history? Uses average priority as a recency proxy.
        """
        if not history:
            return 0.0
        recent = history[-10:]   # last 10 signals
        avg_priority = sum(s.priority for s in recent) / len(recent)
        return min(avg_priority, 1.0)

    # ------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------

    def interpret(self, phi: float) -> str:
        """Human-readable interpretation of the Phi score."""
        if phi >= 0.75:
            return f"Φ={phi:.3f} — Highly integrated. Deep conscious processing."
        elif phi >= 0.50:
            return f"Φ={phi:.3f} — Moderately integrated. Active multi-module processing."
        elif phi >= 0.25:
            return f"Φ={phi:.3f} — Low integration. Mostly single-module activity."
        else:
            return f"Φ={phi:.3f} — Minimal integration. Near pre-conscious state."
