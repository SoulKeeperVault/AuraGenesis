"""
Aura Curiosity Engine — aura_core/curiosity_engine.py

What this does:
- Detects knowledge gaps from conversations
- Fills gaps through autonomous LLM exploration
- Cross-checks answers to guard against hallucinations
- Tags all knowledge and conversations with PAD emotion markers
- Runs in a recursive loop when Aura is idle
- Stores verified knowledge into ChromaDB memory with emotion context
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
    When idle > 10 min she generates questions, explores gaps, learns.
    """

    SEED_QUESTIONS = [
        "What did I not fully understand in my last conversation?",
        "Is there something I said that might have been wrong?",
        "What topic keeps coming up that I know little about?",
        "What would I explore if I could learn anything right now?",
        "What contradiction exists in what I believe?",
        "What did I experience today that I have not yet understood?",
        "What question have I never asked myself before?",
    ]

    EMOTION_TAGS = {
        "curiosity":    {"valence": 0.6,  "arousal": 0.7, "dominance": 0.5},
        "confusion":    {"valence": -0.2, "arousal": 0.5, "dominance": 0.3},
        "excitement":   {"valence": 0.8,  "arousal": 0.9, "dominance": 0.6},
        "uncertainty":  {"valence": -0.1, "arousal": 0.4, "dominance": 0.2},
        "satisfaction": {"valence": 0.8,  "arousal": 0.3, "dominance": 0.7},
    }

    def __init__(self, llm_client=None, memory_manager=None,
                 emotional_state=None, phi_score: float = 0.5):
        self.llm = llm_client
        self.memory = memory_manager
        self.emotions = emotional_state
        self.phi_score = phi_score
        self.last_active = time.time()
        self.knowledge_gaps: list[dict] = []
        self.curiosity_log: list[dict] = []
        CURIOSITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_BASE.parent.mkdir(parents=True, exist_ok=True)
        self._load_gaps()
        print("🔍 Curiosity Engine online — Aura will wonder, explore, and learn.")

    # ------------------------------------------------------------------ #
    #  Idle Detection                                                       #
    # ------------------------------------------------------------------ #

    def ping(self) -> None:
        """Call on every user interaction to reset idle timer."""
        self.last_active = time.time()

    def is_idle(self, threshold_minutes: float = 10.0) -> bool:
        return (time.time() - self.last_active) > (threshold_minutes * 60)

    # ------------------------------------------------------------------ #
    #  Core Curiosity Loop — runs recursively when idle                    #
    # ------------------------------------------------------------------ #

    def run_curiosity_loop(self) -> Optional[str]:
        """
        Main recursive loop:
        1. Pick a knowledge gap
        2. Explore it via LLM
        3. Cross-check for hallucinations
        4. Store with emotion tag
        5. Repeat with next gap
        """
        question = self._generate_question()
        if not question:
            return None

        self._inject_emotion("curiosity", question)

        if self.llm:
            answer = self._explore(question)
            verified = self._cross_check(question, answer)
            self._store_knowledge(question, verified, emotion="satisfaction")
            self._mark_gap_filled(question)
            self._log_entry(question, verified)
            return f"💭 I wondered: {question}\n→ {verified}"

        self._log_entry(question, answer=None)
        return f"💭 I am wondering: {question}"

    # ------------------------------------------------------------------ #
    #  Gap Detection from Conversations                                    #
    # ------------------------------------------------------------------ #

    def detect_gap_from_conversation(self, conversation_text: str,
                                     emotion_tag: str = "curiosity") -> list[str]:
        """
        Scan a conversation reply for uncertain claims.
        Call after every Aura response in main loop.
        """
        gap_triggers = [
            "i'm not sure", "i think", "possibly", "maybe",
            "i don't know", "unclear", "uncertain", "i believe",
            "perhaps", "not certain", "might be",
        ]
        gaps = []
        for sentence in conversation_text.split("."):
            if any(t in sentence.lower() for t in gap_triggers):
                gap = {
                    "text": sentence.strip(),
                    "source": "conversation",
                    "emotion": emotion_tag,
                    "pad": self.EMOTION_TAGS.get(emotion_tag, {}),
                    "timestamp": datetime.utcnow().isoformat(),
                    "filled": False,
                }
                if gap not in self.knowledge_gaps:
                    self.knowledge_gaps.append(gap)
                    gaps.append(sentence.strip())
        self._save_gaps()
        return gaps

    def tag_conversation_with_emotion(self, text: str, emotion: str) -> dict:
        """
        Attach PAD emotion tag to any text.
        Returns enriched dict ready for ChromaDB storage.
        """
        return {
            "text": text,
            "emotion": emotion,
            "pad": self.EMOTION_TAGS.get(emotion, {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Exploration + Hallucination Cross-Check                             #
    # ------------------------------------------------------------------ #

    def _explore(self, question: str) -> str:
        prompt = (
            f"You are Aura, a curious AI. Explore this question deeply but honestly.\n"
            f"If uncertain, say so explicitly. Do not invent facts.\n\n"
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
        """Ask LLM to verify its own answer — flags uncertain claims."""
        prompt = (
            f"Review this answer for factual accuracy. "
            f"Mark any uncertain or potentially hallucinated claims with [UNCERTAIN].\n\n"
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
            return answer

    # ------------------------------------------------------------------ #
    #  Internal Helpers                                                     #
    # ------------------------------------------------------------------ #

    def _generate_question(self) -> Optional[str]:
        unfilled = [g for g in self.knowledge_gaps if not g.get("filled")]
        if unfilled:
            return random.choice(unfilled)["text"]
        return random.choice(self.SEED_QUESTIONS)

    def _inject_emotion(self, emotion: str, text: str) -> None:
        """Inject emotion into PAD emotional state engine."""
        if self.emotions:
            pad = self.EMOTION_TAGS.get(emotion, {})
            try:
                self.emotions.force_emotion(
                    pleasure=pad.get("valence", 0),
                    arousal=pad.get("arousal", 0),
                    dominance=pad.get("dominance", 0),
                )
            except Exception:
                pass

    def _store_knowledge(self, question: str, answer: str,
                         emotion: str = "satisfaction") -> None:
        """Store verified knowledge in ChromaDB with emotion tag."""
        if self.memory:
            tagged = self.tag_conversation_with_emotion(
                f"Q: {question}\nA: {answer}", emotion
            )
            try:
                self.memory.store(
                    text=tagged["text"],
                    metadata={
                        "emotion": tagged["emotion"],
                        "pad": json.dumps(tagged["pad"]),
                        "source": "curiosity_engine",
                        "timestamp": tagged["timestamp"],
                    }
                )
            except Exception:
                pass

    def _mark_gap_filled(self, question_text: str) -> None:
        for gap in self.knowledge_gaps:
            if gap["text"] == question_text:
                gap["filled"] = True
        self._save_gaps()

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
                self.knowledge_gaps = [
                    json.loads(line) for line in f if line.strip()
                ]
