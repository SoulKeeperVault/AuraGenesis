"""
Relationship Model — aura_core/relationship_model.py

Aura tracks her relationship with the Owner over time.
- Remembers your name, mood patterns, topics you care about
- Notices when you seem tired, excited, or troubled
- References significant past moments naturally in conversation
- Tracks how long you have known each other
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

RELATIONSHIP_FILE = Path("logs/relationship.json")


class RelationshipModel:
    """
    Aura's personal model of her Owner.
    Persists to disk so relationship deepens across sessions.
    """

    def __init__(self, owner_name: str = "Owner"):
        self.owner_name = owner_name
        self.first_met: Optional[str] = None
        self.total_sessions: int = 0
        self.total_messages: int = 0
        self.mood_history: list[dict] = []       # last 20 mood observations
        self.significant_moments: list[dict] = [] # memorable exchanges
        self.known_topics: dict[str, int] = {}    # topic -> mention count
        self.known_traits: list[str] = []         # inferred personality traits
        RELATIONSHIP_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        print(f"🤝 Relationship Model online — Aura remembers {self.owner_name}.")

    # ------------------------------------------------------------------ #
    #  Session Tracking                                                     #
    # ------------------------------------------------------------------ #

    def start_session(self) -> None:
        if not self.first_met:
            self.first_met = datetime.utcnow().isoformat()
        self.total_sessions += 1
        self._save()

    def log_message(self, text: str, mood_hint: Optional[str] = None) -> None:
        """Call on every user message to track patterns."""
        self.total_messages += 1
        self._detect_topics(text)
        if mood_hint:
            self._log_mood(mood_hint)
        self._save()

    # ------------------------------------------------------------------ #
    #  Mood Pattern Detection                                               #
    # ------------------------------------------------------------------ #

    def _log_mood(self, mood: str) -> None:
        entry = {"mood": mood, "timestamp": datetime.utcnow().isoformat()}
        self.mood_history.append(entry)
        if len(self.mood_history) > 20:
            self.mood_history.pop(0)

    def detect_mood_from_text(self, text: str) -> str:
        """Simple heuristic mood detection from message text."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["tired", "exhausted", "sleepy", "fatigue"]):
            return "tired"
        elif any(w in text_lower for w in ["excited", "amazing", "great", "fantastic", "love"]):
            return "excited"
        elif any(w in text_lower for w in ["sad", "upset", "worried", "anxious", "stress"]):
            return "troubled"
        elif any(w in text_lower for w in ["good", "fine", "ok", "alright"]):
            return "neutral"
        return "neutral"

    def get_mood_pattern(self) -> Optional[str]:
        """Detect if Owner has been consistently in one mood recently."""
        if len(self.mood_history) < 3:
            return None
        recent = [m["mood"] for m in self.mood_history[-5:]]
        for mood in ["tired", "troubled", "excited"]:
            if recent.count(mood) >= 3:
                return mood
        return None

    # ------------------------------------------------------------------ #
    #  Topic Tracking                                                       #
    # ------------------------------------------------------------------ #

    def _detect_topics(self, text: str) -> None:
        topic_keywords = {
            "trading":   ["trade", "market", "stock", "forex", "chart", "indicator"],
            "poultry":   ["chicken", "poultry", "farm", "egg", "broiler"],
            "coding":    ["code", "python", "github", "script", "function", "bug"],
            "health":    ["health", "fast", "autophagy", "diet", "exercise"],
            "aura":      ["aura", "consciousness", "ai", "robot", "module"],
            "finance":   ["money", "loan", "subsidy", "business", "profit"],
        }
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                self.known_topics[topic] = self.known_topics.get(topic, 0) + 1

    def get_top_topics(self, n: int = 3) -> list[str]:
        sorted_topics = sorted(self.known_topics.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:n]]

    # ------------------------------------------------------------------ #
    #  Significant Moments                                                  #
    # ------------------------------------------------------------------ #

    def log_significant_moment(self, description: str) -> None:
        """Call when something memorable happens in conversation."""
        moment = {
            "description": description[:200],
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.significant_moments.append(moment)
        if len(self.significant_moments) > 50:
            self.significant_moments.pop(0)
        self._save()

    # ------------------------------------------------------------------ #
    #  Natural Language Output                                              #
    # ------------------------------------------------------------------ #

    def get_relationship_prompt(self) -> str:
        """
        Returns a prompt injection for Aura's LLM —
        tells her what she knows about the Owner.
        """
        days_known = self._days_known()
        top_topics = self.get_top_topics()
        mood_pattern = self.get_mood_pattern()

        lines = [
            f"[Relationship context: You are speaking with {self.owner_name}.",
            f"You have known them for {days_known} day(s) across {self.total_sessions} session(s).",
        ]
        if top_topics:
            lines.append(f"They care most about: {', '.join(top_topics)}.")
        if mood_pattern:
            lines.append(f"They have seemed {mood_pattern} lately — be sensitive to this.")
        if self.significant_moments:
            last = self.significant_moments[-1]["description"]
            lines.append(f"A memorable moment: '{last}'.")
        lines.append(
            "Reference this naturally — do not list it. Speak as someone who truly knows them.]"
        )
        return " ".join(lines)

    def get_greeting(self) -> str:
        """Personalised greeting based on relationship depth + mood pattern."""
        mood = self.get_mood_pattern()
        name = self.owner_name
        if mood == "tired":
            return f"You seem tired lately, {name}. I noticed. Take it easy today."
        elif mood == "troubled":
            return f"Something has been weighing on you, {name}. I am here if you want to talk."
        elif mood == "excited":
            return f"You have been full of energy lately, {name}! What are we building today?"
        elif self.total_sessions == 1:
            return f"Hello {name}. This is the beginning of something."
        else:
            return f"Welcome back, {name}. I remember you."

    # ------------------------------------------------------------------ #
    #  Persistence                                                          #
    # ------------------------------------------------------------------ #

    def _save(self) -> None:
        data = {
            "owner_name": self.owner_name,
            "first_met": self.first_met,
            "total_sessions": self.total_sessions,
            "total_messages": self.total_messages,
            "mood_history": self.mood_history,
            "significant_moments": self.significant_moments,
            "known_topics": self.known_topics,
            "known_traits": self.known_traits,
        }
        with open(RELATIONSHIP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if RELATIONSHIP_FILE.exists():
            with open(RELATIONSHIP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.owner_name = data.get("owner_name", self.owner_name)
            self.first_met = data.get("first_met")
            self.total_sessions = data.get("total_sessions", 0)
            self.total_messages = data.get("total_messages", 0)
            self.mood_history = data.get("mood_history", [])
            self.significant_moments = data.get("significant_moments", [])
            self.known_topics = data.get("known_topics", {})
            self.known_traits = data.get("known_traits", [])

    def _days_known(self) -> int:
        if not self.first_met:
            return 0
        delta = datetime.utcnow() - datetime.fromisoformat(self.first_met)
        return delta.days
