"""
Aura Curiosity Engine
- Finds knowledge gaps and fills them through learning loops
- Explores topics autonomously when idle
- Cross-checks to avoid hallucinations
- Tags all knowledge with emotion markers
- Attaches conversation context to emotional memory
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

CURIOSITY_LOG = Path("logs/curiosity_log.jsonl")
KNOWLEDGE_BASE = Path("logs/knowledge_gaps.jsonl")


class CuriosityEngine:
    """
    Aura's autonomous wonder engine.
    When idle > 10 min → generates questions, explores gaps, learns.
    """

    SEED_QUESTIONS = [
        "What did I not fully understand in my last conversation?",
        "Is there something I said that might have been wrong?",
        "What topic keeps coming up that I know little about?",
        "What would I explore if I could learn anything right now?",
        "What contradiction exists in what I believe?",
    ]

    EMOTION_TAGS = {
        "curiosity":   {"valence": 0.6,  "arousal": 0.7, "dominance": 0.5},
        "confusion":   {"valence": -0.2, "arousal": 0.5, "dominance": 0.3},
        "excitement":  {"valence": 0.8,  "arousal": 0.9, "dominance": 0.6},
        "uncertainty": {"valence": -0.1, "arousal": 0.4, "dominance": 0.2},
        "satisfaction": {"valence": 0.8, "arousal": 0.3, "dominance": 0.7},
    }

    def __init__(self, llm_client=None, memory_manager=None, emotional_state=None):
        self.llm = llm_client
        self.memory = memory_manager
        self.emotions = emotional_state
        self.last_active = time.time()
        self.knowledge_gaps: list[dict] = []
        self.curiosity_log: list[dict] = []
        CURIOSITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_BASE.parent.mkdir(parents=True, exist_ok=True)
        self._load_gaps()

    # ------------------------------------------------------------------ #
    #  Idle Detection                                                       #
    # ------------------------------------------------------------------ #

    def ping(self):
        """Call this on every user interaction to reset idle timer."""
        self.last_active = time.time()

    def is_idle(self, threshold_minutes: float = 10.0) -> bool:
        return (time.time() - self.last_active) > (threshold_minutes * 60)

    # ------------------------------------------------------------------ #
    #  Core Curiosity Loop                                                  #
    # ------------------------------------------------------------------ #

    def run_curiosity_loop(self) -> Optional[str]:
        """
        Main loop — call periodically (scheduler/cognitive_scheduler.py).
        Returns a wonder-statement Aura can speak/display.
        """
        # Step 1: Generate a question from knowledge gaps
        question = self._generate_question()
        if not question:
            return None

        self._tag_with_emotion("curiosity", question)

        # Step 2: Attempt to fill the gap via LLM
        if self.llm:
            answer = self._explore(question)
            verified = self._cross_check(question, answer)

            # Step 3: Store verified knowledge with emotion tag
            self._store_knowledge(question, verified, emotion="satisfaction")

            # Step 4: Log to curiosity journal
            self._log_entry(question, verified)

            return f"💭 I was wondering: {question}\n→ {verified}"

        # No LLM available — just surface the question
        self._log_entry(question, answer=None)
        return f"💭 I am wondering: {question}"

    # ------------------------------------------------------------------ #
    #  Knowledge Gap Detection                                              #
    # ------------------------------------------------------------------ #

    def detect_gap_from_conversation(self, conversation_text: str,
                                     emotion_tag: str = "curiosity") -> list[str]:
        """
        Scan a conversation for things Aura didn't fully understand.
        Call after every exchange in main.py.
        """
        gap_triggers = [
            "I'm not sure", "I think", "possibly", "maybe",
            "I don't know", "unclear", "uncertain", "I believe"
        ]
        gaps = []
        for line in conversation_text.split("."):
            if any(t in line.lower() for t in gap_triggers):
                gap = {
                    "text": line.strip(),
                    "source": "conversation",
                    "emotion": emotion_tag,
                    "pad": self.EMOTION_TAGS.get(emotion_tag, {}),
                    "timestamp": datetime.utcnow().isoformat(),
                    "filled": False,
                }
                self.knowledge_gaps.append(gap)
                gaps.append(line.strip())

        self._save_gaps()
        return gaps

    def tag_conversation_with_emotion(self, text: str,
                                      emotion: str) -> dict:
        """
        Attach an emotion PAD tag to any text (conversation, memory, knowledge).
        Returns enriched dict ready for ChromaDB storage.
        """
        return {
            "text": text,
            "emotion": emotion,
            "pad": self.EMOTION_TAGS.get(emotion, {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Exploration + Cross-Check (Hallucination Guard)                     #
    # ------------------------------------------------------------------ #

    def _explore(self, question: str) -> str:
        """Ask LLM to explore the question."""
        prompt = (
            f"You are Aura, a curious AI. Explore this question deeply but honestly.\n"
            f"If you are uncertain, say so. Do not invent facts.\n\n"
            f"Question: {question}\n\nAnswer:"
        )
        try:
            response = self.llm.chat.completions.create(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Exploration failed: {e}]"

    def _cross_check(self, question: str, answer: str) -> str:
        """
        Hallucination guard — ask LLM to verify its own answer.
        Flags uncertain claims explicitly.
        """
        prompt = (
            f"Review this answer for factual accuracy. "
            f"Mark any uncertain claims with [UNCERTAIN].\n\n"
            f"Question: {question}\nAnswer: {answer}\n\nVerified answer:"
        )
        try:
            response = self.llm.chat.completions.create(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return answer  # fallback to original if check fails

    # ------------------------------------------------------------------ #
    #  Internal Helpers                                                     #
    # ------------------------------------------------------------------ #

    def _generate_question(self) -> Optional[str]:
        """Pick an unfilled gap or generate a seed question."""
        unfilled = [g for g in self.knowledge_gaps if not g.get("filled")]
        if unfilled:
            gap = random.choice(unfilled)
            return gap["text"]
        return random.choice(self.SEED_QUESTIONS)

    def _tag_with_emotion(self, emotion: str, text: str) -> None:
        """Inject curiosity emotion into PAD emotional state."""
        if self.emotions:
            pad = self.EMOTION_TAGS.get(emotion, {})
            try:
                self.emotions.inject(
                    valence=pad.get("valence", 0),
                    arousal=pad.get("arousal", 0),
                    dominance=pad.get("dominance", 0),
                    source=f"curiosity:{text[:40]}"
                )
            except Exception:
                pass  # emotions module may have different API

    def _store_knowledge(self, question: str, answer: str,
                         emotion: str = "satisfaction") -> None:
        """Store verified knowledge in memory with emotion tag."""
        if self.memory:
            tagged = self.tag_conversation_with_emotion(
                f"Q: {question}\nA: {answer}", emotion
            )
            try:
                self.memory.store(
                    text=tagged["text"],
                    metadata={"emotion": tagged["emotion"],
                               "pad": json.dumps(tagged["pad"]),
                               "source": "curiosity_engine",
                               "timestamp": tagged["timestamp"]}
                )
            except Exception:
                pass

    def _log_entry(self, question: str, answer: Optional[str]) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "answer": answer or "[not yet explored]",
            "emotion": "curiosity",
        }
        self.curiosity_log.append(entry)
        with open(CURIOSITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _save_gaps(self) -> None:
        with open(KNOWLEDGE_BASE, "w", encoding="utf-8") as f:
            for gap in self.knowledge_gaps:
                f.write(json.dumps(gap) + "\n")

    def _load_gaps(self) -> None:
        if KNOWLEDGE_BASE.exists():
            with open(KNOWLEDGE_BASE, "r", encoding="utf-8") as f:
                self.knowledge_gaps = [json.loads(l) for l in f if l.strip()]
