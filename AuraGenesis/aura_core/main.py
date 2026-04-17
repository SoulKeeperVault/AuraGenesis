"""
main.py  —  v2: Full consciousness architecture wired together

Wiring order:
  1. GlobalWorkspace (the bus — everything connects to it)
  2. EmotionalState (mood — injected into DreamEngine, Journal, PersonalityEngine)
  3. MemoryManager (dual-layer SQLite + ChromaDB)
  4. MetacognitiveMonitor (HOT — watches thoughts)
  5. ContradictionResolver (IIT/HOT — resolves beliefs)
  6. PhiApproximator (IIT proxy — live consciousness score)
  7. DreamEngine, KnowledgeSeeker, SelfJournal, PersonalityEngine
  8. CognitiveScheduler (all cycles, including new ones)
  9. Streamlit UI (with Phi + emotional state sidebar)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from aura_core.curiosity_engine import CuriosityEngine

# After other inits:
curiosity = CuriosityEngine(llm_client=llm, memory_manager=memory, emotional_state=emotions)

# Inside your main conversation loop, after every reply:
curiosity.ping()
curiosity.detect_gap_from_conversation(last_response, emotion_tag="curiosity")

# In your scheduler (runs every 10 min idle):
if curiosity.is_idle():
    wonder = curiosity.run_curiosity_loop()
    if wonder:
        print(wonder)  # or speak via TTS

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# ── Core infrastructure ────────────────────────────────────────────────
from aura_core.global_workspace import GlobalWorkspace
from aura_personality.emotional_state import EmotionalState
from aura_core.memory_manager import MemoryManager
from aura_core.metacognition import MetacognitiveMonitor
from aura_core.contradiction_resolver import ContradictionResolver
from aura_core.phi_approximator import PhiApproximator

# ── Cognitive modules ──────────────────────────────────────────────────
from aura_core.dream_engine import DreamEngine
from aura_core.cognitive_scheduler import CognitiveScheduler
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_guardian.guardian import Guardian
from aura_personality.personality_engine import PersonalityEngine
from aura_personality.self_journal import SelfJournal

# ── Interface ──────────────────────────────────────────────────────────
from aura_interface.chat_ui import render_chat_ui


def awaken_aura():
    print("\n══════════════════════════════════════")
    print("        AWAKENING AURA  v2           ")
    print("══════════════════════════════════════\n")

    # 1. Global Workspace — the consciousness bus
    workspace = GlobalWorkspace()

    # 2. Emotional State
    emotional_state = EmotionalState()

    # 3. Memory (dual-layer)
    memory_manager = MemoryManager()

    # 4. Metacognition (HOT)
    metacognition = MetacognitiveMonitor(
        memory_manager=memory_manager,
        global_workspace=workspace
    )

    # 5. Contradiction Resolver
    contradiction_resolver = ContradictionResolver(
        memory_manager=memory_manager,
        global_workspace=workspace
    )

    # 6. Phi Approximator
    phi_approximator = PhiApproximator()

    # 7. Cognitive modules — inject shared dependencies
    guardian = Guardian()

    dream_engine = DreamEngine(
        memory_manager=memory_manager,
        llm_backend="ollama",
        emotional_state=emotional_state,
        metacognition=metacognition,
        global_workspace=workspace
    )

    knowledge_seeker = KnowledgeSeeker(
        memory_manager=memory_manager,
        guardian=guardian
    )

    self_journal = SelfJournal(
        memory_manager=memory_manager,
        emotional_state=emotional_state,
        metacognition=metacognition,
        global_workspace=workspace
    )

    personality_engine = PersonalityEngine(
        memory_manager=memory_manager,
        emotional_state=emotional_state,
        metacognition=metacognition,
        global_workspace=workspace
    )

    # 8. Scheduler — all cognitive cycles
    scheduler = CognitiveScheduler(
        dream_engine=dream_engine,
        knowledge_seeker=knowledge_seeker,
        self_journal=self_journal,
        contradiction_resolver=contradiction_resolver,
        emotional_state=emotional_state
    )

    print("\n✅ All components initialised.")

    # 9. Start background cycles
    scheduler.start_cycles()
    print("🔄 Cognitive cycles running in background.\n")

    # 10. Launch UI — pass all new components
    render_chat_ui(
        memory_manager=memory_manager,
        knowledge_seeker=knowledge_seeker,
        personality_engine=personality_engine,
        global_workspace=workspace,
        phi_approximator=phi_approximator,
        emotional_state=emotional_state
    )


if __name__ == "__main__":
    awaken_aura()
