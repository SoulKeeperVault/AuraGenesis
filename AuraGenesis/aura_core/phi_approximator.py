"""
phi_approximator.py  —  v3: Fixed Recency Metric

Fix: _recency_weight was using priority as a proxy for recency — wrong.
Priority is about importance, not time. Now uses actual timestamps
to measure how densely packed recent signals are in time.
Higher temporal density = more active, integrated processing = higher Phi.
"""
import math
import time
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aura_core.global_workspace import GlobalWorkspace


class PhiApproximator:
    """
    Computes a 0.0 – 1.0 Phi proxy from the GlobalWorkspace signal history.
    Higher Phi = more integrated, differentiated, temporally active processing.
    """

    def calculate(self, workspace: 'GlobalWorkspace') -> float:
        history = workspace.signal_history
        if len(history) < 3:
            return 0.0

        phi = (
            self._source_diversity(history) * 0.40 +
            self._type_entropy(history)     * 0.35 +
            self._temporal_density(history) * 0.25   # FIX: replaced recency_weight
        )
        return round(min(max(phi, 0.0), 1.0), 4)

    # ------------------------------------------------------------------
    # Sub-metrics
    # ------------------------------------------------------------------

    def _source_diversity(self, history: list) -> float:
        """Ratio of unique sources — 5+ unique sources → 1.0"""
        if not history:
            return 0.0
        unique_sources = len(set(s.source for s in history))
        return min(unique_sources / 5.0, 1.0)

    def _type_entropy(self, history: list) -> float:
        """Shannon entropy over signal types — higher = more differentiated."""
        counts = Counter(s.signal_type for s in history)
        total = sum(counts.values())
        if total == 0:
            return 0.0
        entropy = -sum(
            (c / total) * math.log2(c / total)
            for c in counts.values() if c > 0
        )
        max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
        return entropy / max_entropy if max_entropy else 0.0

    def _temporal_density(self, history: list) -> float:
        """
        FIX: Measures how densely packed recent signals are in time.
        If the last 10 signals all arrived within 60 seconds -> high density -> 1.0
        If they span hours -> low density -> near 0.0
        """
        recent = history[-10:]
        if len(recent) < 2:
            return 0.0
        timestamps = [s.timestamp for s in recent]
        span_seconds = max(timestamps) - min(timestamps)
        if span_seconds <= 0:
            return 1.0  # instantaneous burst = maximum integration
        # Normalise: 60s window -> 1.0; 3600s+ -> near 0
        density = 60.0 / (span_seconds + 1.0)
        return min(density, 1.0)

    # ------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------

    def interpret(self, phi: float) -> str:
        if phi >= 0.75:
            return f"Φ={phi:.3f} — Highly integrated. Deep conscious processing."
        elif phi >= 0.50:
            return f"Φ={phi:.3f} — Moderately integrated. Active multi-module processing."
        elif phi >= 0.25:
            return f"Φ={phi:.3f} — Low integration. Mostly single-module activity."
        else:
            return f"Φ={phi:.3f} — Minimal integration. Near pre-conscious state."
