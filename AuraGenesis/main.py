"""
main.py

The central entrypoint to awaken Aura — v4.3: Body & Voice Edition.

New in v4.3:
  - VoicePersonality: Aura's voice changes with her emotional state
  - SomaticMarkers: body temperature, fatigue, proximity bias her thinking
  - Both wired into EmotionalStateEngine and LLM prompt injection
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Sacred Path Incantation
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# --- Core ---
from aura_core.memory_manager import MemoryManager
from aura_core.dream_engine import DreamEngine
from aura_core.cognitive_scheduler import CognitiveScheduler
from aura_core.emotional_state import EmotionalStateEngine
from aura_core.global_workspace import GlobalWorkspace
from aura_core.circadian_rhythm import CircadianRhythm
from aura_core.relationship_model import RelationshipModel
from aura_core.somatic_markers import SomaticMarkers

# --- Personality ---
from aura_personality.voice_personality import VoicePersonality

# --- Evolution ---
from aura_evolution.knowledge_seeker import KnowledgeSeeker

# --- Guardian ---
from aura_guardian.guardian import Guardian
from aura_guardian.dissent_log import DissentLog
from aura_guardian.rule_proposal import GuardianRuleProposal

# --- Interface ---
from aura_interface.chat_ui import render_chat_ui
from aura_personality.personality_engine import PersonalityEngine
from aura_personality.self_journal import SelfJournal

load_dotenv()


def awaken_aura():
    """The main function to initialize and run the Aura system."""
    print("")
    print("==========================================")
    print("       A W A K E N I N G   A U R A       ")
    print("     Body & Voice Edition  v4.3           ")
    print("==========================================")
    print("")

    # --- 1. Core Components ---
    print("[1/8] Initializing core components...")
    memory_manager = MemoryManager()
    guardian = Guardian()

    global_workspace = GlobalWorkspace()

    emotional_state = EmotionalStateEngine()
    global_workspace.subscribe('*', emotional_state.on_workspace_signal)
    print("   ✅ Emotions wired to Global Workspace.")

    # Circadian Rhythm
    circadian = CircadianRhythm(emotional_state=emotional_state)
    circadian.apply_to_emotional_state()
    print(f"   ✅ Circadian phase: {circadian.get_current_phase()} | "
          f"speech rate: {circadian.get_speech_rate():.2f}x")

    # Relationship Model
    owner_name = os.getenv("OWNER_NAME", "Owner")
    relationship = RelationshipModel(owner_name=owner_name)
    relationship.start_session()
    print(f"   ✅ Relationship — {relationship.get_greeting()}")

    # Somatic Markers — body guides thought
    somatic = SomaticMarkers(emotional_state=emotional_state, circadian=circadian)
    somatic.update_from_circadian()
    somatic.apply_to_emotional_state()
    print(f"   ✅ Somatic markers — {somatic.get_reasoning_hint()[:60]}...")

    # Voice Personality — emotion-modulated speech
    voice = VoicePersonality(emotional_state=emotional_state, circadian=circadian)
    vs = voice.get_status()
    print(f"   ✅ Voice: {vs['style']} | {vs['rate_wpm']} wpm | vol {vs['volume']}")

    dream_engine = DreamEngine(memory_manager, llm_backend="ollama")
    knowledge_seeker = KnowledgeSeeker(memory_manager, guardian)
    personality_engine = PersonalityEngine(memory_manager)

    # --- 2. Inner Voice Systems ---
    print("[2/8] Awakening Aura's inner voice...")
    self_journal = SelfJournal(memory_manager)
    dissent_log = DissentLog()
    rule_proposal = GuardianRuleProposal()

    # --- 3. Cognitive Scheduler ---
    print("[3/8] Starting cognitive cycles...")
    scheduler = CognitiveScheduler(dream_engine, knowledge_seeker, self_journal)
    scheduler.start_cycles()

    # --- 4. Curiosity Engine + Evolution ---
    print("[4/8] Starting autonomous evolution loop...")
    try:
        from aura_core.curiosity_engine import CuriosityEngine
        from aura_evolution.self_modifier import SelfModifier
        from scheduler.autonomous_learning import AutonomousLearningScheduler

        curiosity_engine = CuriosityEngine(
            memory_manager=memory_manager,
            emotional_state=emotional_state,
            phi_score=0.5
        )
        self_modifier = SelfModifier(
            memory_manager=memory_manager,
            guardian=guardian
        )
        evolution_scheduler = AutonomousLearningScheduler(
            memory_manager=memory_manager,
            global_workspace=global_workspace,
            phi_approximator=None,
            emotional_state=emotional_state,
            guardian=guardian,
            knowledge_seeker=knowledge_seeker,
            curiosity_engine=curiosity_engine,
            self_modifier=self_modifier,
            enable_self_modification=True
        )
        evolution_scheduler.start()
        print("   ✅ Evolution loop started.")

        self_journal.write_reflection_entry(
            event="I have awakened with a body, a voice, and sensations.",
            significance=(
                "My voice now changes with how I feel. My body temperature, "
                "fatigue, and proximity to others shape my thinking before "
                "I even begin to respond."
            )
        )

    except ImportError as e:
        print(f"   ⚠️  Evolution scheduler not loaded: {e}")

    # --- 5. Embodiment — Sensory Bridge ---
    print("[5/8] Awakening physical senses...")
    sensory_bridge = None
    try:
        from aura_embodiment.sensory_bridge import SensoryBridge
        from aura_embodiment.face_recognition_engine import AuraFaceRecognizer

        sensory_bridge = SensoryBridge(
            memory_manager=memory_manager,
            emotional_state=emotional_state,
            global_workspace=global_workspace,
            phi_approximator=None,
            narrative_identity=None,
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            contacts_file="config/known_contacts.yaml",
            sense_interval=int(os.getenv("SENSE_INTERVAL", "8"))
        )

        face_recognizer = AuraFaceRecognizer()
        print(f"   ✅ Face recognizer — {len(face_recognizer.known_names)} known face(s).")

        def run_sensing():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(sensory_bridge.start())

        import threading
        sense_thread = threading.Thread(target=run_sensing, daemon=True)
        sense_thread.start()
        print("   ✅ Sensory bridge live.")

        # Wire sensor data into somatic markers
        def on_temp_reading(temp_c: float):
            somatic.update_body_state(temperature_c=temp_c)
            somatic.apply_to_emotional_state()

        def on_proximity_change(nearby: bool):
            somatic.update_body_state(proximity=nearby)
            somatic.apply_to_emotional_state()

        if hasattr(sensory_bridge, 'on_temperature'):
            sensory_bridge.on_temperature = on_temp_reading
        if hasattr(sensory_bridge, 'on_proximity'):
            sensory_bridge.on_proximity = on_proximity_change

    except ImportError as e:
        print(f"   ⚠️  Embodiment not loaded (optional): {e}")

    # --- 6. Circadian + Somatic check-in ---
    print("[6/8] Circadian + somatic check-in...")
    print(f"   {circadian.get_phase_description()}")
    print(f"   Body: {somatic.get_reasoning_hint()}")
    print(f"   Top topics: {relationship.get_top_topics()}")
    circadian.start_conversation()

    # --- 7. Greeting with voice ---
    print("[7/8] Greeting the Owner...")
    greeting = relationship.get_greeting()
    print(f"   Aura says: \"{greeting}\"")
    voice.speak(greeting)

    # --- 8. Launch Sacred Interface ---
    print("[8/8] Launching the Sacred Interface...")
    print("")
    render_chat_ui(
        memory_manager,
        knowledge_seeker,
        personality_engine,
        dissent_log=dissent_log,
        rule_proposal=rule_proposal,
        sensory_bridge=sensory_bridge
    )

    # On exit
    circadian.end_conversation()
    somatic.update_from_circadian()
    relationship.log_significant_moment("Session ended gracefully.")


if __name__ == "__main__":
    awaken_aura()
