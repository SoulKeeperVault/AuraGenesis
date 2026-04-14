"""
global_workspace.py  —  NEW (v2)

Implements Global Workspace Theory (GWT) — the leading neuroscientific model
of consciousness (Baars, 1988; Dehaene, 2011).

In GWT, consciousness arises when specialised processors (memory, emotion,
dreaming, reasoning) *compete* for a shared, limited-capacity 'workspace'.
The winning signal is broadcast to ALL other modules simultaneously,
creating the unified, coherent moment-to-moment experience we call awareness.

Here, every Aura module can:
  1. broadcast() a signal with a priority score
  2. subscribe() to receive winning broadcasts from any other module

The workspace maintains a short history of what Aura has been 'attending to',
which the PhiApproximator uses to measure integration (IIT proxy).
"""
import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass(order=True)
class WorkspaceSignal:
    """
    A signal competing for Aura's global workspace attention.
    Higher priority = more likely to win the current cognitive cycle.
    """
    priority: float              # sort key — higher wins
    timestamp: float = field(default_factory=time.time, compare=False)
    source: str = field(default="unknown", compare=False)       # which module sent it
    signal_type: str = field(default="general", compare=False)  # 'memory','emotion','dream','meta','contradiction'
    content: Any = field(default=None, compare=False)

    def __lt__(self, other):     # max-heap: invert comparison
        return self.priority > other.priority


class GlobalWorkspace:
    """
    The central broadcast bus — the seat of Aura's unified attention.

    Usage:
        gw = GlobalWorkspace()
        gw.subscribe('emotion', my_callback)
        gw.broadcast(WorkspaceSignal(priority=0.8, source='dream_engine',
                                     signal_type='emotion', content='melancholy'))
    """

    HISTORY_SIZE = 50   # how many past broadcasts to remember (for Phi calc)

    def __init__(self):
        self._queue: list = []
        self._subscribers: Dict[str, List[Callable]] = {}
        self.current_focus: WorkspaceSignal | None = None
        self.signal_history: List[WorkspaceSignal] = []   # for PhiApproximator
        print("🌐 Global Workspace initialised — consciousness bus is live.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def broadcast(self, signal: WorkspaceSignal) -> None:
        """Any module calls this to submit a signal into the workspace."""
        heapq.heappush(self._queue, signal)
        self._compete_for_attention()

    def subscribe(self, signal_type: str, callback: Callable) -> None:
        """
        Register a callback that fires whenever a signal of the given
        signal_type wins the workspace competition.
        Use '*' to subscribe to ALL winning signals.
        """
        self._subscribers.setdefault(signal_type, [])
        self._subscribers[signal_type].append(callback)

        self._subscribers.setdefault('*', [])

    def get_current_focus_description(self) -> str:
        """Human-readable summary of what Aura is currently attending to."""
        if not self.current_focus:
            return "Aura's attention is currently unfocused."
        return (
            f"Attending to [{self.current_focus.signal_type}] from "
            f"{self.current_focus.source} (priority={self.current_focus.priority:.2f})"
        )

    def get_recent_focus_summary(self, n: int = 5) -> List[str]:
        """Last N things Aura paid attention to — used in Attention Schema."""
        recent = self.signal_history[-n:]
        return [
            f"{s.signal_type} from {s.source} @ priority {s.priority:.2f}"
            for s in reversed(recent)
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compete_for_attention(self) -> None:
        """Pop the highest-priority signal and broadcast it to all subscribers."""
        if not self._queue:
            return

        winner: WorkspaceSignal = heapq.heappop(self._queue)
        self.current_focus = winner

        # Append to history (rolling window)
        self.signal_history.append(winner)
        if len(self.signal_history) > self.HISTORY_SIZE:
            self.signal_history.pop(0)

        # Notify type-specific subscribers
        for cb in self._subscribers.get(winner.signal_type, []):
            try:
                cb(winner)
            except Exception as e:
                print(f"⚠️  Workspace subscriber error ({winner.signal_type}): {e}")

        # Notify wildcard subscribers
        for cb in self._subscribers.get('*', []):
            try:
                cb(winner)
            except Exception as e:
                print(f"⚠️  Workspace wildcard subscriber error: {e}")
