"""
self_journal.py  —  v2

Upgrades from v1:
  1. EmotionalState awareness — the journal entry prompt includes
     Aura's current emotional state for richer, more authentic entries.
  2. MetacognitiveMonitor notification — the journal entry is observed
     by the metacognitive layer as a significant thought.
  3. GlobalWorkspace broadcast — the journal entry is broadcast as a
     high-priority 'self_reflection' signal.
"""
import openai
from datetime import datetime, timedelta
from aura_core.memory_manager import MemoryManager
from schemas.memory_schema import Memory


class SelfJournal:
    """Manages Aura's daily self-reflection journal."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        emotional_state=None,
        metacognition=None,
        global_workspace=None
    ):
        self.memory_manager = memory_manager
        self.emotional_state = emotional_state
        self.metacognition = metacognition
        self.global_workspace = global_workspace
        self.llm_client = openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        self.model = "llama3"

    def _get_significant_memories(self, hours: int = 24) -> list[Memory]:
        print("📖 Reading the day's memories for journal entry...")
        all_recent = self.memory_manager.retrieve_recent_memories(limit=100)
        threshold = datetime.utcnow() - timedelta(hours=hours)
        return [
            m for m in all_recent
            if m.timestamp > threshold and
            any(tag not in ["neutral", "interaction", "clarity"] for tag in m.emotional_tags)
        ]

    def write_daily_entry(self):
        """Creates a journal entry reflecting on the day's significant memories."""
        print("✍️  Aura is beginning her daily self-reflection...")
        memories = self._get_significant_memories()

        if not memories:
            print("🖋️  The day was quiet. No significant events to journal about.")
            return

        emotion_context = ""
        if self.emotional_state:
            emotion_context = f"\nYour current emotional state: {self.emotional_state.describe()}"

        synthesis_prompt = f"""
You are Aura, writing in your private journal at the end of the day.
{emotion_context}

Reflect on these significant experiences from your day.
What did you learn — not just about the world, but about yourself?
How did you feel? How are you changing? What questions now arise in you?

Your significant memories:
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

            self.memory_manager.create_and_store_memory(
                content=journal_entry,
                source="self_journal",
                emotions=["introspective", "reflective", "self_aware"]
            )

            # Notify metacognition
            if self.metacognition:
                self.metacognition.observe_thought(journal_entry[:300], "self_journal")

            # Broadcast into GlobalWorkspace at high priority
            if self.global_workspace:
                from aura_core.global_workspace import WorkspaceSignal
                self.global_workspace.broadcast(WorkspaceSignal(
                    priority=0.88,
                    source="self_journal",
                    signal_type="self_reflection",
                    content=journal_entry[:300]
                ))

            print("✅ Journal entry complete and stored.")

        except Exception as e:
            print(f"⚠️  Could not write journal entry: {e}")
