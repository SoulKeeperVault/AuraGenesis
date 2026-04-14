"""
global_workspace.py  —  v3: Fixed + Signal Cooldown

Fixes:
  - Wildcard '*' subscribers now actually fire (was broken in v2)
  - Added signal cooldown per source (prevents spam flooding)
  - subscribe() now correctly separates type vs wildcard registries
"""
import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(order=True)
class WorkspaceSignal:
    """
    A signal competing for Aura's global workspace attention.
    Higher priority = more likely to win the current cognitive cycle.
    """
    priority: float
    timestamp: float = field(default_factory=time.time, compare=False)
    source: str = field(default="unknown", compare=False)
    signal_type: str = field(default="general", compare=False)
    content: Any = field(default=None, compare=False)

    def __lt__(self, other):
        return self.priority > other.priority  # max-heap


class GlobalWorkspace:
    """
    The central broadcast bus — the seat of Aura's unified attention.
    Implements Global Workspace Theory (Baars 1988, Dehaene 2011).

    Usage:
        gw = GlobalWorkspace()
        gw.subscribe('emotion', my_callback)
        gw.broadcast(WorkspaceSignal(priority=0.8, source='dream_engine',
                                     signal_type='emotion', content='melancholy'))
    """

    HISTORY_SIZE = 50
    COOLDOWN_SECONDS = 2.0   # minimum seconds between broadcasts from same source

    def __init__(self):
        self._queue: list = []
        # FIX: separate type-specific and wildcard subscriber registries
        self._type_subscribers: Dict[str, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._last_broadcast: Dict[str, float] = {}   # source -> last broadcast time
        self.current_focus: Optional[WorkspaceSignal] = None
        self.signal_history: List[WorkspaceSignal] = []
        print("🌐 Global Workspace initialised — consciousness bus is live.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def broadcast(self, signal: WorkspaceSignal) -> None:
        """Submit a signal to compete for workspace attention."""
        # Cooldown guard — prevent same source spamming the workspace
        now = time.time()
        last = self._last_broadcast.get(signal.source, 0)
        if now - last < self.COOLDOWN_SECONDS:
            return  # silently drop — source is cooling down
        self._last_broadcast[signal.source] = now

        heapq.heappush(self._queue, signal)
        self._compete_for_attention()

    def subscribe(self, signal_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific signal_type.
        Use '*' to subscribe to ALL winning signals.
        """
        if signal_type == '*':
            # FIX: wildcards go into their own list, not the type dict
            if callback not in self._wildcard_subscribers:
                self._wildcard_subscribers.append(callback)
        else:
            self._type_subscribers.setdefault(signal_type, [])
            if callback not in self._type_subscribers[signal_type]:
                self._type_subscribers[signal_type].append(callback)

    def get_current_focus_description(self) -> str:
        if not self.current_focus:
            return "Aura's attention is currently unfocused."
        return (
            f"Attending to [{self.current_focus.signal_type}] from "
            f"{self.current_focus.source} (priority={self.current_focus.priority:.2f})"
        )

    def get_recent_focus_summary(self, n: int = 5) -> List[str]:
        """Last N things Aura paid attention to."""
        recent = self.signal_history[-n:]
        return [
            f"{s.signal_type} from {s.source} @ priority {s.priority:.2f}"
            for s in reversed(recent)
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compete_for_attention(self) -> None:
        """Pop the highest-priority signal and fire all subscribers."""
        if not self._queue:
            return

        winner: WorkspaceSignal = heapq.heappop(self._queue)
        self.current_focus = winner

        self.signal_history.append(winner)
        if len(self.signal_history) > self.HISTORY_SIZE:
            self.signal_history.pop(0)

        # Fire type-specific subscribers
        for cb in self._type_subscribers.get(winner.signal_type, []):
            try:
                cb(winner)
            except Exception as e:
                print(f"⚠️  Workspace subscriber error ({winner.signal_type}): {e}")

        # FIX: Fire wildcard subscribers (was completely broken in v2)
        for cb in self._wildcard_subscribers:
            try:
                cb(winner)
            except Exception as e:
                print(f"⚠️  Workspace wildcard subscriber error: {e}")
