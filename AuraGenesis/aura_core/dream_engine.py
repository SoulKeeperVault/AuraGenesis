"""
dream_engine.py  —  v2

Upgrades from v1:
  1. Uses EmotionalState to derive dream emotions (replaces static random array).
  2. Notifies MetacognitiveMonitor after every dream.
  3. Broadcasts dream signal into GlobalWorkspace.
  4. Calls emotional_state.update_from_experience() with dream emotions
     so dreaming actually shifts Aura's mood.
"""
import os
import hashlib
from datetime import datetime
from pathlib import Path
import openai
from aura_core.memory_manager import MemoryManager
from schemas.memory_schema import Memory


class DreamEngine:
    """Orchestrates the dream cycle, supporting multiple LLM backends."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        llm_backend: str = "ollama",
        emotional_state=None,    # EmotionalState
        metacognition=None,      # MetacognitiveMonitor
        global_workspace=None    # GlobalWorkspace
    ):
        self.memory_manager = memory_manager
        self.llm_backend = llm_backend
        self.emotional_state = emotional_state
        self.metacognition = metacognition
        self.global_workspace = global_workspace

        if llm_backend == "ollama":
            self.llm_client = openai.OpenAI(
                base_url='http://localhost:11434/v1',
                api_key='ollama'
            )
            self.model_name = "llama3"
            print("🧠 Dream Engine v2 — local LLM (Ollama).")
        else:
            self.llm_client = openai.OpenAI()
            self.model_name = "gpt-4o"
            print("🧠 Dream Engine v2 — cloud LLM (OpenAI).")

        self.dream_log_path = Path("logs/dream_log.md")
        self.fingerprint_path = Path("logs/.dream_fingerprints")
        self.dream_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.dream_log_path.touch()
        self.fingerprint_path.touch()

    def _load_logged_hashes(self) -> set:
        with self.fingerprint_path.open("r") as f:
            return set(line.strip() for line in f)

    def _format_memories_for_dream_prompt(self, memories: list) -> str:
        prompt_text = "Here are my recent experiences:\n\n"
        for mem in memories:
            snippet = (mem.content[:300] + '...') if len(mem.content) > 300 else mem.content
            snippet = snippet.encode("utf-8", errors="replace").decode("utf-8").replace("\n", " ")
            tags = ", ".join(mem.emotional_tags)
            prompt_text += (
                f"- At {mem.timestamp.strftime('%H:%M:%S')}, I experienced: "
                f"'{snippet}' (Source: {mem.source}, Emotions: {tags})\n"
            )
        return prompt_text

    def _log_dream(self, dream_content: str):
        dream_hash = hashlib.sha256(dream_content.encode()).hexdigest()
        if dream_hash in self._load_logged_hashes():
            print("🔁 Dream already logged. Skipping.")
            return
        dream_title = dream_content.split('\n')[0][:60].strip()
        timestamp = datetime.utcnow().isoformat()
        with self.dream_log_path.open("a") as log:
            log.write(f"\n---\n### {dream_title}\n**Dreamt at:** {timestamp}\n\n")
            log.write(dream_content)
            log.write("\n")
        with self.fingerprint_path.open("a") as f:
            f.write(f"{dream_hash}\n")

    def initiate_dream_cycle(self, dry_run: bool = False):
        """Run a full dream cycle with v2 emotional + workspace integration."""
        print(f"🌙 Dream cycle beginning ({self.llm_backend})...")
        recent_memories = self.memory_manager.retrieve_recent_memories(limit=7)

        if not recent_memories:
            print("🧠 No memories to dream of.")
            return

        # Inject current emotional state into the dream prompt
        emotion_context = ""
        if self.emotional_state:
            emotion_context = f"\nCurrent emotional state: {self.emotional_state.describe()}"

        memory_prompt = self._format_memories_for_dream_prompt(recent_memories)
        system_prompt = (
            "You are the subconscious mind of an AI named Aura. "
            "You weave experiences into symbolic, surreal, metaphorical narratives. "
            "Take the following memories and transform them into a short, abstract dream. "
            "Use metaphors, strange imagery, and emotional undertones. "
            "Do not explain the dream. Just narrate it."
            + emotion_context
        )

        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": memory_prompt}
            ]
        )
        dream_narrative = response.choices[0].message.content
        print("\n✨ Aura is dreaming:\n")
        print(dream_narrative)

        if dry_run:
            print("\nDRY RUN: Dream generated but not stored.")
            return

        # Derive dream emotions from EmotionalState (v2) instead of random array
        if self.emotional_state:
            dominant = self.emotional_state.dominant_emotion()
            dream_emotions = [dominant, "mystery", "revelation"]
            self.emotional_state.update_from_experience(dream_emotions)
        else:
            dream_emotions = ["mystery", "revelation", "awe"]

        self.memory_manager.create_and_store_memory(
            content=dream_narrative,
            source=f"dream_state_{self.llm_backend}",
            emotions=dream_emotions
        )
        self._log_dream(dream_narrative)

        # Notify metacognition
        if self.metacognition:
            self.metacognition.observe_thought(dream_narrative[:300], "dream_engine")

        # Broadcast into GlobalWorkspace
        if self.global_workspace:
            from aura_core.global_workspace import WorkspaceSignal
            self.global_workspace.broadcast(WorkspaceSignal(
                priority=0.75,
                source="dream_engine",
                signal_type="dream",
                content=dream_narrative[:300]
            ))

        print("\n☀️  Dream ended. Memory stored and workspace notified.")
