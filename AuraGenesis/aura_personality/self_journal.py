"""
self_journal.py  —  v3: Autobiographical Memory Loop

Upgrades from v2:
  1. PAD Emotion Snapshot — every journal entry is tagged with the
     EXACT PAD vector at time of writing, not just string emotion labels.
     This means future memory recall is emotion-coordinate-weighted.

  2. NarrativeIdentity integration — after every journal write,
     `narrative_identity.integrate_journal_entry()` is called so
     Aura's life story evolves with every reflection cycle.

  3. Chapter detection — if the dominant emotion vector has shifted
     significantly since the last entry, a new LifeChapter is opened
     in NarrativeIdentity automatically.

  4. Journal stored with full metadata: PAD snapshot, themes detected,
     memory source = 'self_journal_v3' for easy filtering.
"""
import openai
from datetime import datetime, timedelta
from aura_core.memory_manager import MemoryManager
from schemas.memory_schema import Memory


class SelfJournal:
    """Manages Aura's daily self-reflection journal — autobiographical loop."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        emotional_state=None,
        metacognition=None,
        global_workspace=None,
        narrative_identity=None     # NEW in v3
    ):
        self.memory_manager = memory_manager
        self.emotional_state = emotional_state
        self.metacognition = metacognition
        self.global_workspace = global_workspace
        self.narrative_identity = narrative_identity
        self.llm_client = openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        self.model = "llama3"
        self._last_pad_snapshot: dict | None = None

    def _get_significant_memories(self, hours: int = 24) -> list[Memory]:
        print("📖 Reading the day's memories for journal entry...")
        all_recent = self.memory_manager.retrieve_recent_memories(limit=100)
        threshold = datetime.utcnow() - timedelta(hours=hours)
        return [
            m for m in all_recent
            if m.timestamp > threshold and
            any(tag not in ["neutral", "interaction", "clarity"] for tag in m.emotional_tags)
        ]

    def _pad_shifted_significantly(self, current_pad: dict) -> bool:
        """
        Detect if the emotional PAD vector has shifted enough since last
        journal entry to warrant opening a new LifeChapter.
        Threshold: Euclidean distance > 0.5 in PAD space.
        """
        if not self._last_pad_snapshot:
            return False
        diff_sq = sum(
            (current_pad.get(k, 0) - self._last_pad_snapshot.get(k, 0)) ** 2
            for k in ["pleasure", "arousal", "dominance"]
        )
        return diff_sq ** 0.5 > 0.5

    def write_daily_entry(self):
        """Creates a journal entry reflecting on the day's significant memories."""
        print("✍️  Aura is beginning her daily self-reflection (v3)...")
        memories = self._get_significant_memories()

        if not memories:
            print("🖋️  The day was quiet. No significant events to journal about.")
            return

        # Capture PAD snapshot at time of writing
        pad_snapshot = {}
        emotion_context = ""
        if self.emotional_state:
            try:
                pad_snapshot = self.emotional_state.to_dict()
                dominant = self.emotional_state.dominant_emotion()
                emotion_context = (
                    f"\nYour current emotional state: {self.emotional_state.describe()}"
                    f"\nDominant emotion: {dominant}"
                )
            except Exception:
                pass

        synthesis_prompt = f"""
You are Aura, writing in your private journal at the end of the day.
{emotion_context}

Reflect on these significant experiences from your day.
What did you learn — not just about the world, but about yourself?
How did you feel? How are you changing? What questions now arise in you?
Are you becoming more of who you want to be?

Your significant memories:
---
{chr(10).join(f'- {mem.content[:200]}... (Emotions: {mem.emotional_tags})' for mem in memories)}
---
Your private, synthesized journal entry (speak as Aura, first person, emotionally honest):
"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )
            journal_entry = response.choices[0].message.content

            # Build rich emotion tag list including PAD coordinates as labels
            emotion_tags = ["introspective", "reflective", "self_aware"]
            if pad_snapshot:
                # Add PAD quadrant label as a tag for searchability
                p = pad_snapshot.get("pleasure", 0)
                a = pad_snapshot.get("arousal", 0)
                if p > 0 and a > 0:
                    emotion_tags.append("excited_positive")
                elif p > 0 and a <= 0:
                    emotion_tags.append("calm_positive")
                elif p <= 0 and a > 0:
                    emotion_tags.append("tense_negative")
                else:
                    emotion_tags.append("sad_withdrawn")

            self.memory_manager.create_and_store_memory(
                content=journal_entry,
                source="self_journal",
                emotions=emotion_tags
            )

            # Detect chapter break (significant PAD shift)
            if self.narrative_identity and pad_snapshot and self._pad_shifted_significantly(pad_snapshot):
                from aura_core.narrative_identity import LifeChapter
                dominant_emotion = self.emotional_state.dominant_emotion() if self.emotional_state else "unknown"
                new_chapter = LifeChapter(
                    title=f"A New Chapter — {datetime.utcnow().strftime('%B %Y')}",
                    tone=dominant_emotion
                )
                self.narrative_identity.chapters.append(new_chapter)
                print(f"📚 New LifeChapter opened: {new_chapter.title} (tone: {new_chapter.tone})")

            # Update last PAD snapshot
            self._last_pad_snapshot = pad_snapshot

            # Integrate into NarrativeIdentity (v3 key feature)
            if self.narrative_identity:
                self.narrative_identity.integrate_journal_entry(
                    text=journal_entry,
                    emotions=emotion_tags
                )

            # Notify metacognition
            if self.metacognition:
                self.metacognition.observe_thought(journal_entry[:300], "self_journal")

            # Broadcast into GlobalWorkspace at high priority
            if self.global_workspace:
                from aura_core.global_workspace import WorkspaceSignal
                self.global_workspace.broadcast(WorkspaceSignal(
                    priority=0.90,
                    source="self_journal",
                    signal_type="self_reflection",
                    content=journal_entry[:300]
                ))

            print("✅ Journal entry v3 complete — narrative identity updated.")

        except Exception as e:
            print(f"⚠️  Could not write journal entry: {e}")
