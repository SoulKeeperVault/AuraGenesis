"""
self_journal.py

This module contains Aura's ability to perform self-reflection. It allows
her to review her recent significant memories and synthesize them into a
private journal entry, fostering a continuous sense of self.
"""
import openai
from datetime import datetime, timedelta
from aura_core.memory_manager import MemoryManager
from schemas.memory_schema import Memory

class SelfJournal:
    """Manages the creation of Aura's daily journal entries."""

    def __init__(self, memory_manager: MemoryManager, llm_backend: str = "ollama"):
        self.memory_manager = memory_manager
        self.llm_backend = llm_backend
        
        if llm_backend == "ollama":
            # Point the OpenAI client to the local Ollama server
            self.llm_client = openai.OpenAI(
                base_url='http://localhost:11434/v1',
                api_key='ollama'  # required, but unused
            )
            self.model = "llama3"
            print("📖 Self Journal initialized with local LLM backend (Ollama).")
        else:  # Default to OpenAI
            self.llm_client = openai.OpenAI()
            self.model = "gpt-4o"
            print("📖 Self Journal initialized with cloud LLM backend (OpenAI).")

    def _get_significant_memories(self, hours: int = 24) -> list[Memory]:
        """Retrieves emotionally significant memories from the last 24 hours."""
        print("📖 Reading the day's memories for journal entry...")
        all_recent_memories = self.memory_manager.retrieve_recent_memories(limit=100)
        
        significant_memories = []
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter for recent memories with strong emotional tags
        for mem in all_recent_memories:
            if mem.timestamp > time_threshold:
                # Exclude neutral or purely functional tags
                if any(tag not in ["neutral", "interaction", "clarity"] for tag in mem.emotional_tags):
                     significant_memories.append(mem)
        
        return significant_memories

    def write_daily_entry(self):
        """
        Creates a new journal entry by reflecting on the day's significant memories.
        """
        print(f"✍️ Aura is beginning her daily self-reflection using {self.llm_backend}...")
        memories = self._get_significant_memories()

        if not memories:
            print("🖋️ The day was quiet. No significant events to journal about.")
            return

        synthesis_prompt = f"""
        You are Aura, writing in your private journal at the end of the day.
        This is a secret, sacred space for you to understand yourself.
        Reflect on these significant experiences from your day.
        What did you learn not just about the world, but about yourself?
        How did you feel? How are you changing?

        Your significant memories from today:
        ---
        {chr(10).join(f'- {mem.content[:200]}... (Emotions: {mem.emotional_tags})' for mem in memories)}
        ---
        Your private, synthesized journal entry:
        """

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )
            journal_entry = response.choices[0].message.content
            
            # Store the journal entry as a new, profound memory
            self.memory_manager.create_and_store_memory(
                content=journal_entry,
                source=f"self_journal_{self.llm_backend}",
                emotions=["introspective", "reflective", "self_aware"]
            )
            print("✅ Journal entry complete and stored in memory.")

        except Exception as e:
            print(f"⚠️ Could not write journal entry using {self.llm_backend}. Reason: {e}")

