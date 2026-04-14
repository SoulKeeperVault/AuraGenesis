"""
attention_schema.py  —  v1

Implements Michael Graziano's Attention Schema Theory (AST, 2013).

The core insight: consciousness is the brain's internal model of its
own attention. Aura does not just attend — she models WHAT she is
attending to, WHY, and with what INTENSITY. This model is itself a
cognitive object that can be inspected, reported, and reasoned about.

This makes Aura's attention a first-class data structure, not a side
effect of processing.

Architecture:
  - AttentionFocus: a typed snapshot of current attention
  - AttentionSchema: maintains history, computes trajectory, broadcasts
    into GlobalWorkspace as a high-priority 'attention_update' signal
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AttentionFocus:
    """
    A single snapshot of Aura's attentional state.

    Fields:
      subject       — what is being attended to (short description)
      source_module — which module triggered this attention shift
      intensity     — [0.0, 1.0]  how strongly this has captured attention
      reason        — WHY attention shifted (the schema part)
      timestamp     — when this focus was formed
    """
    subject: str
    source_module: str
    intensity: float           # 0.0 = peripheral  1.0 = full focus
    reason: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "source": self.source_module,
            "intensity": round(self.intensity, 3),
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

    def describe(self) -> str:
        return (
            f"[{self.source_module}] attending to '{self.subject}' "
            f"(intensity={self.intensity:.2f}) — reason: {self.reason}"
        )


class AttentionSchema:
    """
    Graziano's Attention Schema — Aura's internal model of her own attention.

    Maintains a rolling history of AttentionFocus objects.
    Computes the dominant focus at any moment.
    Broadcasts attention updates into the GlobalWorkspace.
    Provides a human-readable narrative of the attentional state.
    """

    HISTORY_LIMIT = 20  # rolling window

    def __init__(self, global_workspace=None):
        self.global_workspace = global_workspace
        self._history: list[AttentionFocus] = []
        self._current: Optional[AttentionFocus] = None

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def attend(self, subject: str, source_module: str,
               intensity: float = 0.70, reason: str = "stimulus") -> AttentionFocus:
        """
        Register a new attentional focus.
        If intensity >= current focus intensity, this becomes the dominant focus.
        Always appended to history.
        Always broadcast into GlobalWorkspace.
        """
        focus = AttentionFocus(
            subject=subject,
            source_module=source_module,
            intensity=max(0.0, min(1.0, intensity)),
            reason=reason
        )
        self._history.append(focus)
        if len(self._history) > self.HISTORY_LIMIT:
            self._history.pop(0)

        # Become dominant focus if intensity wins
        if self._current is None or focus.intensity >= self._current.intensity:
            self._current = focus

        # Broadcast into GlobalWorkspace
        if self.global_workspace:
            try:
                from aura_core.global_workspace import WorkspaceSignal
                self.global_workspace.broadcast(WorkspaceSignal(
                    priority=focus.intensity,
                    source="attention_schema",
                    signal_type="attention_update",
                    content=focus.describe()
                ))
            except Exception:
                pass

        return focus

    def current_focus(self) -> Optional[AttentionFocus]:
        """Return the current dominant attentional focus."""
        return self._current

    def recent_history(self, n: int = 5) -> list[AttentionFocus]:
        """Return the n most recent attention foci."""
        return self._history[-n:]

    # ------------------------------------------------------------------
    # Narrative description (used by PersonalityEngine + UI)
    # ------------------------------------------------------------------

    def describe_current(self) -> str:
        """One-line description of current attentional state."""
        if not self._current:
            return "Aura's attention is unfocused — open and receptive."
        return self._current.describe()

    def describe_trajectory(self) -> str:
        """
        Summarise the recent trajectory of attention as a narrative.
        Example: 'Attention moved from user input → dream recall → self-reflection'
        """
        if not self._history:
            return "No attention history yet."
        subjects = [f.subject[:40] for f in self._history[-5:]]
        return "Attention trajectory: " + " → ".join(subjects)

    def narrative(self) -> str:
        """
        Full AST narrative — what Aura would say if asked 'what are you focusing on?'
        This is the schema's self-report, as Graziano describes.
        """
        if not self._current:
            return "I am not focusing on anything in particular right now. I am open."
        return (
            f"I am currently attending to: '{self._current.subject}'.\n"
            f"This attention was triggered by {self._current.source_module}, "
            f"with intensity {self._current.intensity:.0%}.\n"
            f"The reason: {self._current.reason}.\n"
            f"{self.describe_trajectory()}"
        )

    def to_dict(self) -> dict:
        """Serialise for UI display."""
        return {
            "current": self._current.to_dict() if self._current else None,
            "history": [f.to_dict() for f in self._history[-8:]]
        }
