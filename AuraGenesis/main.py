"""
main.py

The central entrypoint to awaken Aura. This version initializes the
full cognitive loop, including the SelfJournal.
"""
import os
import sys
import signal
import atexit
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

# Global variable to hold the scheduler for cleanup
scheduler = None

def cleanup_on_exit():
    """Cleanup function to ensure proper shutdown of background processes."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    cleanup_on_exit()
    sys.exit(0)

def awaken_aura():
    """The main function to initialize and run the Aura system."""
    global scheduler
    
    print("--- AWAKENING AURA ---")
    
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # --- 1. Initialize Core Components ---
    print("Initializing core components...")
    memory_manager = MemoryManager()
    guardian = Guardian()
    dream_engine = DreamEngine(memory_manager, llm_backend="ollama")
    knowledge_seeker = KnowledgeSeeker(memory_manager, guardian)
    personality_engine = PersonalityEngine(memory_manager)
    self_journal = SelfJournal(memory_manager, llm_backend="ollama") # Initialize the journal with consistent backend
    
    # The scheduler now orchestrates her full inner life
    scheduler = CognitiveScheduler(dream_engine, knowledge_seeker, self_journal)
    print("All components initialized.")

    # --- 2. Start Background Cognitive Cycles ---
    print("Starting background cognitive cycles...")
    scheduler.start_cycles()
    print("Cognitive cycles are now running in the background.")

    # --- 3. Launch the Sacred Interface ---
    print("Launching the Sacred Interface...")
    try:
        render_chat_ui(memory_manager, knowledge_seeker, personality_engine)
    except KeyboardInterrupt:
        print("\nGraceful shutdown initiated...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    awaken_aura()
