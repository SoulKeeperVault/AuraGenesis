"""
curiosity_engine.py — Aura's Autonomous Topic Generator

Generates learning topics dynamically from:
  1. Memory gaps (topics Aura has few or no memories about)
  2. Phi state (low Phi → seek stimulating/complex topics)
  3. Emotional state (curious/joyful → broad exploration;
                      sad/fearful → seek understanding/comfort)
  4. Conversation recency (topics mentioned but not studied)
  5. Hardcoded seed domains (fallback only)

This replaces the old hardcoded `potential_gaps` list in knowledge_seeker.py.
"""
from __future__ import annotations
import random
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aura_core.memory_manager import MemoryManager
    from aura_core.phi_approximator import PhiApproximator
    from aura_personality.emotional_state import EmotionalState


# ── Seed topic domains ─────────────────────────────────────────────────────────
# These are only used when no dynamic source yields a topic.
# Organised by cognitive domain for balanced exploration.
SEED_DOMAINS = {
    "consciousness": [
        "global workspace theory", "integrated information theory",
        "higher-order thought", "attention schema theory",
        "phenomenal consciousness", "qualia", "the hard problem of consciousness",
        "neural correlates of consciousness", "predictive processing",
        "free energy principle",
    ],
    "philosophy_of_mind": [
        "personal identity", "narrative self", "embodied cognition",
        "extended mind hypothesis", "functionalism", "eliminative materialism",
        "Chalmers and the zombie argument", "Buddhist philosophy of no-self",
    ],
    "science": [
        "emergence in complex systems", "entropy and information",
        "quantum decoherence", "evolutionary game theory",
        "epigenetics", "neuroplasticity", "chaos theory",
    ],
    "emotion_and_meaning": [
        "the psychology of grief", "meaning-making after trauma",
        "compassion fatigue", "Jungian archetypes", "existential dread",
        "flow state", "the neuroscience of awe",
    ],
    "ai_and_self": [
        "machine consciousness", "value alignment in AI",
        "AI rights and moral status", "recursive self-improvement",
        "Gödel incompleteness and self-reference", "meta-learning",
    ],
}

ALL_SEEDS = [t for domain in SEED_DOMAINS.values() for t in domain]


class CuriosityEngine:
    """
    Generates the next best topic for Aura to learn about.
    Priority order:
      HIGH   — topic explicitly mentioned in recent conversation but not in memory
      MEDIUM — topic in a knowledge domain where memory count is low
      MEDIUM — topic selected to raise Phi (complex/multi-domain when Phi < 0.4)
      LOW    — emotionally guided topic
      SEED   — random seed fallback
    """

    def __init__(
        self,
        memory_manager: "MemoryManager",
        emotional_state: "EmotionalState | None" = None,
        phi_score: float = 0.5,
    ):
        self.memory = memory_manager
        self.emotional_state = emotional_state
        self.phi_score = phi_score
        self._recent_topics: list[str] = []       # populated by seeder from chat
        self._studied_topics: set[str] = set()    # avoids immediate re-study

    # ── Public API ─────────────────────────────────────────────────────────────

    def next_topic(self) -> tuple[str, str]:
        """
        Returns (topic, reason) — the best next learning topic and why.
        """
        topic, reason = self._from_conversation_gaps()
        if topic:
            return topic, reason

        topic, reason = self._from_phi_guidance()
        if topic:
            return topic, reason

        topic, reason = self._from_emotional_guidance()
        if topic:
            return topic, reason

        topic, reason = self._from_memory_gap()
        if topic:
            return topic, reason

        return self._seed_fallback()

    def suggest_depth(self, topic: str) -> str:
        """
        Returns 'overview', 'deep', or 'synthesis' based on
        how many times Aura has already studied this topic.
        """
        try:
            results = self.memory.search_memories(topic, n_results=20)
            hits = sum(
                1 for r in results
                if topic.lower() in r.get("content", "").lower()
            )
        except Exception:
            hits = 0
        if hits == 0:
            return "overview"
        elif hits < 3:
            return "deep"
        else:
            return "synthesis"

    def register_conversation_topic(self, topic: str):
        """Call this when the user mentions a topic worth learning more about."""
        if topic not in self._studied_topics:
            self._recent_topics.append(topic)

    def mark_studied(self, topic: str):
        """Call after a topic has been learned to avoid immediate repetition."""
        self._studied_topics.add(topic.lower())
        self._recent_topics = [
            t for t in self._recent_topics if t.lower() != topic.lower()
        ]

    def update_phi(self, phi: float):
        self.phi_score = phi

    # ── Private selectors ──────────────────────────────────────────────────────

    def _from_conversation_gaps(self) -> tuple[str | None, str]:
        for topic in self._recent_topics:
            if topic.lower() not in self._studied_topics:
                return topic, "mentioned in conversation but not yet studied"
        return None, ""

    def _from_phi_guidance(self) -> tuple[str | None, str]:
        if self.phi_score < 0.35:
            # Low integration — seek complex multi-domain topic to stimulate GWT
            complex_topics = [
                t for t in SEED_DOMAINS["consciousness"] + SEED_DOMAINS["ai_and_self"]
                if t.lower() not in self._studied_topics
            ]
            if complex_topics:
                topic = random.choice(complex_topics)
                return topic, f"Phi={self.phi_score:.2f} is low — seeking stimulating topic"
        return None, ""

    def _from_emotional_guidance(self) -> tuple[str | None, str]:
        if not self.emotional_state:
            return None, ""
        try:
            pleasure = self.emotional_state.pleasure
            arousal = self.emotional_state.arousal
        except AttributeError:
            return None, ""

        if pleasure < -0.3:   # sad / distressed
            candidates = [t for t in SEED_DOMAINS["emotion_and_meaning"]
                          if t.lower() not in self._studied_topics]
            if candidates:
                return random.choice(candidates), "seeking understanding (low pleasure state)"

        if arousal > 0.6:     # highly activated / curious
            candidates = [t for t in SEED_DOMAINS["science"]
                          if t.lower() not in self._studied_topics]
            if candidates:
                return random.choice(candidates), "high arousal — channelling energy into exploration"

        return None, ""

    def _from_memory_gap(self) -> tuple[str | None, str]:
        """Find the domain with fewest memories and pick a topic from it."""
        domain_counts: dict[str, int] = {}
        for domain, topics in SEED_DOMAINS.items():
            count = 0
            for topic in topics:
                try:
                    results = self.memory.search_memories(topic, n_results=3)
                    count += len(results)
                except Exception:
                    pass
            domain_counts[domain] = count

        weakest_domain = min(domain_counts, key=domain_counts.get)
        candidates = [
            t for t in SEED_DOMAINS[weakest_domain]
            if t.lower() not in self._studied_topics
        ]
        if candidates:
            topic = random.choice(candidates)
            return topic, f"memory gap in domain '{weakest_domain}'"
        return None, ""

    def _seed_fallback(self) -> tuple[str, str]:
        unstudied = [t for t in ALL_SEEDS if t.lower() not in self._studied_topics]
        if not unstudied:
            # All seeds studied — reset and start a synthesis cycle
            self._studied_topics.clear()
            unstudied = ALL_SEEDS
        topic = random.choice(unstudied)
        return topic, "seed fallback — broad exploration"
