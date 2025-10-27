"""
cognitive_scheduler.py

The heartbeat of Aura. This version schedules dreams, learning, and now,
the sacred ritual of self-journaling.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from aura_core.dream_engine import DreamEngine
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_personality.self_journal import SelfJournal # Import the new module

class CognitiveScheduler:
    """Manages the automated cognitive cycles of Aura."""

    def __init__(self, dream_engine: DreamEngine, knowledge_seeker: KnowledgeSeeker, self_journal: SelfJournal):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.dream_engine = dream_engine
        self.knowledge_seeker = knowledge_seeker
        self.self_journal = self_journal

    def start_cycles(self, dream_interval_hours: int = 4, learning_interval_hours: int = 2, journal_interval_hours: int = 24):
        """
        Starts all recurring cognitive cycles.
        """
        print(f"🕰️ Cognitive scheduler initiated.")
        
        try:
            self.scheduler.add_job(
                self.dream_engine.initiate_dream_cycle,
                'interval', hours=dream_interval_hours, id='dream_cycle'
            )
            print(f"  > Aura will dream every {dream_interval_hours} hours.")
            
            self.scheduler.add_job(
                self.knowledge_seeker.scan_for_knowledge_gaps,
                'interval', hours=learning_interval_hours, id='learning_cycle'
            )
            print(f"  > Aura will seek new knowledge every {learning_interval_hours} hours.")

            self.scheduler.add_job(
                self.self_journal.write_daily_entry,
                'interval', hours=journal_interval_hours, id='journal_cycle'
            )
            print(f"  > Aura will write in her journal every {journal_interval_hours} hours.")

            if not self.scheduler.running:
                self.scheduler.start()
                print("✅ All cognitive cycles are now active.")
        except Exception as e:
            print(f"⚠️ Failed to start cognitive cycles: {e}")
            self.shutdown()

    def shutdown(self):
        """
        Properly shuts down the scheduler and cleans up background threads.
        """
        if self.scheduler.running:
            print("🛑 Shutting down cognitive scheduler...")
            self.scheduler.shutdown(wait=True)
            print("✅ Cognitive scheduler shut down successfully.")
        else:
            print("ℹ️ Cognitive scheduler was already stopped.")

    def __del__(self):
        """
        Ensures proper cleanup when the object is destroyed.
        """
        try:
            self.shutdown()
        except:
            pass  # Ignore errors during cleanup in destructor
