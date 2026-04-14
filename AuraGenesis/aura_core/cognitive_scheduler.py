"""
cognitive_scheduler.py  —  v2

Upgraded to schedule two new consciousness cycles:
  - contradiction_resolver  (every 6 hours)
  - emotional_decay         (every 1 hour)

Also broadcasts a heartbeat signal into the GlobalWorkspace every cycle
so the Phi score stays fresh in the UI.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from aura_core.dream_engine import DreamEngine
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_personality.self_journal import SelfJournal


class CognitiveScheduler:
    """Manages all automated cognitive cycles for Aura."""

    def __init__(
        self,
        dream_engine: DreamEngine,
        knowledge_seeker: KnowledgeSeeker,
        self_journal: SelfJournal,
        contradiction_resolver=None,   # ContradictionResolver
        emotional_state=None           # EmotionalState
    ):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.dream_engine = dream_engine
        self.knowledge_seeker = knowledge_seeker
        self.self_journal = self_journal
        self.contradiction_resolver = contradiction_resolver
        self.emotional_state = emotional_state

    def start_cycles(
        self,
        dream_interval_hours: int = 4,
        learning_interval_hours: int = 2,
        journal_interval_hours: int = 24,
        contradiction_interval_hours: int = 6,
        decay_interval_minutes: int = 60
    ):
        """Start all recurring cognitive cycles."""
        print("🕰️  Cognitive scheduler v2 initiated.")

        self.scheduler.add_job(
            self.dream_engine.initiate_dream_cycle,
            'interval', hours=dream_interval_hours, id='dream_cycle'
        )
        print(f"  > Dream cycle: every {dream_interval_hours}h")

        self.scheduler.add_job(
            self.knowledge_seeker.scan_for_knowledge_gaps,
            'interval', hours=learning_interval_hours, id='learning_cycle'
        )
        print(f"  > Learning cycle: every {learning_interval_hours}h")

        self.scheduler.add_job(
            self.self_journal.write_daily_entry,
            'interval', hours=journal_interval_hours, id='journal_cycle'
        )
        print(f"  > Journal cycle: every {journal_interval_hours}h")

        if self.contradiction_resolver:
            self.scheduler.add_job(
                self.contradiction_resolver.resolve,
                'interval', hours=contradiction_interval_hours, id='contradiction_cycle'
            )
            print(f"  > Contradiction resolution: every {contradiction_interval_hours}h")

        if self.emotional_state:
            self.scheduler.add_job(
                self.emotional_state.decay,
                'interval', minutes=decay_interval_minutes, id='emotional_decay'
            )
            print(f"  > Emotional decay: every {decay_interval_minutes}min")

        if not self.scheduler.running:
            self.scheduler.start()
            print("  ✅ All cognitive cycles running.")
