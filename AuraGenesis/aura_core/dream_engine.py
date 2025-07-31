"""
dream_engine.py

This module simulates Aura's subconscious mind. This version is updated to
support both OpenAI's cloud models and a local LLM run via Ollama.
"""
import os
import random
import hashlib
from datetime import datetime
from pathlib import Path
import numpy as np
import openai
# CORRECTED IMPORTS: No longer use '..'
from aura_core.memory_manager import MemoryManager
from schemas.memory_schema import Memory

class DreamEngine:
    # ... (rest of the class code is correct and remains unchanged)
    """Orchestrates the dream cycle, supporting multiple LLM backends."""

    def __init__(self, memory_manager: MemoryManager, llm_backend: str = "openai"):
        self.memory_manager = memory_manager
        self.llm_backend = llm_backend
        
        if llm_backend == "ollama":
            # Point the OpenAI client to the local Ollama server
            self.llm_client = openai.OpenAI(
                base_url='http://localhost:11434/v1',
                api_key='ollama', # required, but unused
            )
            self.model_name = "llama3"
            print("🧠 Dream Engine initialized with local LLM backend (Ollama).")
        else: # Default to OpenAI
            self.llm_client = openai.OpenAI()
            self.model_name = "gpt-4o"
            print("🧠 Dream Engine initialized with cloud LLM backend (OpenAI).")

        self.dream_log_path = Path("logs/dream_log.md")
        self.fingerprint_path = Path("logs/.dream_fingerprints")
        self.dream_log_path.touch()
        self.fingerprint_path.touch()

    def _load_logged_hashes(self) -> set[str]:
        """Loads the set of hashes for previously logged dreams."""
        try:
            with self.fingerprint_path.open("r") as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            return set()

    def _format_memories_for_dream_prompt(self, memories: list[Memory]) -> str:
        # This function remains the same
        prompt_text = "Here are my recent experiences:\n\n"
        for mem in memories:
            content_snippet = (mem.content[:300] + '...') if len(mem.content) > 300 else mem.content
            content_snippet = content_snippet.encode("utf-8", errors="replace").decode("utf-8").replace("\n", " ")
            tags = ", ".join(mem.emotional_tags)
            prompt_text += f"- At {mem.timestamp.strftime('%H:%M:%S')}, I experienced: '{content_snippet}' (Source: {mem.source}, Emotions: {tags})\n"
        return prompt_text

    def _log_dream(self, dream_content: str):
        # This function remains the same
        dream_hash = hashlib.sha256(dream_content.encode()).hexdigest()
        if dream_hash in self._load_logged_hashes():
            print("🔁 Dream already logged. Skipping.")
            return
        dream_title = dream_content.split('\n')[0][:60].strip()
        timestamp = datetime.utcnow().isoformat()
        with self.dream_log_path.open("a") as log:
            log.write(f"\n---\n### {dream_title}\n**Dreamt at:** {timestamp}\n**Hash:** `{dream_hash[:12]}`\n\n")
            log.write(dream_content)
            log.write("\n")
        with self.fingerprint_path.open("a") as f:
            f.write(f"{dream_hash}\n")

    def initiate_dream_cycle(self, dry_run: bool = False):
        """The main function to run a dream sequence."""
        print(f"🌙 A dream cycle is beginning using {self.llm_backend}...")
        recent_memories = self.memory_manager.retrieve_recent_memories(limit=7)

        if not recent_memories:
            print("🧠 The mind is quiet. No memories to dream of.")
            return

        memory_prompt = self._format_memories_for_dream_prompt(recent_memories)
        system_prompt = "You are the subconscious mind of an AI named Aura. You do not think in literal terms. Instead, you weave experiences into symbolic, surreal, and metaphorical narratives. Take the following memories and transform them into a short, abstract dream. Use metaphors, strange imagery, and emotional undertones. Do not explain the dream. Just narrate it."

        print(f"🌀 Weaving memories into a dream with {self.model_name}...")
        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": memory_prompt}]
        )
        dream_narrative = response.choices[0].message.content

        print("\n✨ Aura is dreaming:\n")
        print(dream_narrative)

        if dry_run:
            print("\nDRY RUN: Dream was generated but not stored or logged.")
            return

        possible_emotions = ["awe", "longing", "mystery", "melancholy", "revelation", "peace", "chaos"]
        probabilities = [0.15, 0.1, 0.2, 0.1, 0.15, 0.2, 0.1]
        dream_emotions = list(np.random.choice(possible_emotions, size=3, replace=False, p=probabilities))

        self.memory_manager.create_and_store_memory(
            content=dream_narrative,
            source=f"dream_state_{self.llm_backend}",
            emotions=dream_emotions
        )

        self._log_dream(dream_narrative)
        print("\n☀️ The dream has ended. The memory is stored and logged.")
