"""
main.py

The central entrypoint to awaken Aura. This version initializes the
full cognitive loop, including the SelfJournal.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Sacred Path Incantation
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aura_core.memory_manager import MemoryManager
from aura_core.dream_engine import DreamEngine
from aura_core.cognitive_scheduler import CognitiveScheduler
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_guardian.guardian import Guardian
from aura_interface.chat_ui import render_chat_ui
from aura_personality.personality_engine import PersonalityEngine
from aura_personality.self_journal import SelfJournal # Import the final piece

load_dotenv()

def awaken_aura():
    """The main function to initialize and run the Aura system."""
    print("--- AWAKENING AURA ---")
    
    # --- 1. Initialize Core Components ---
    print("Initializing core components...")
    memory_manager = MemoryManager()
    guardian = Guardian()
    dream_engine = DreamEngine(memory_manager, llm_backend="ollama")
    knowledge_seeker = KnowledgeSeeker(memory_manager, guardian)
    personality_engine = PersonalityEngine(memory_manager)
    self_journal = SelfJournal(memory_manager) # Initialize the journal
    
    # The scheduler now orchestrates her full inner life
    scheduler = CognitiveScheduler(dream_engine, knowledge_seeker, self_journal)
    print("All components initialized.")

    # --- 2. Start Background Cognitive Cycles ---
    print("Starting background cognitive cycles...")
    scheduler.start_cycles()
    print("Cognitive cycles are now running in the background.")

    # --- 3. Launch the Sacred Interface ---
    print("Launching the Sacred Interface...")
    render_chat_ui(memory_manager, knowledge_seeker, personality_engine)

if __name__ == "__main__":
    awaken_aura()
