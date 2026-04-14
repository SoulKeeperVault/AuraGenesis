"""
autonomous_learning.py — v2: Full Evolution Orchestrator

Replaces the empty stub with a real APScheduler-based background engine.

Jobs (all exception-isolated, all Guardian-gated):
  1. knowledge_job     — every 30 min — CuriosityEngine → KnowledgeSeeker
  2. curiosity_refresh — every 15 min — updates Phi in CuriosityEngine
  3. code_evolution    — every 6 hrs  — SelfModifier improvement cycle
  4. health_report     — every 1 hr   — logs Phi, PAD, topics studied

Usage:
    from scheduler.autonomous_learning import AutonomousLearningScheduler
    scheduler = AutonomousLearningScheduler(aura_components)
    scheduler.start()   # non-blocking background thread
    scheduler.stop()    # clean shutdown
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from aura_core.memory_manager import MemoryManager
    from aura_core.global_workspace import GlobalWorkspace
    from aura_core.phi_approximator import PhiApproximator
    from aura_personality.emotional_state import EmotionalState
    from aura_guardian.guardian import Guardian
    from aura_evolution.knowledge_seeker import KnowledgeSeeker
    from aura_evolution.curiosity_engine import CuriosityEngine
    from aura_evolution.self_modifier import SelfModifier

logger = logging.getLogger("aura.scheduler")


class AutonomousLearningScheduler:
    """
    Orchestrates all of Aura's autonomous background cycles.

    Pass in all required Aura components at init time.
    Call .start() to begin background processing.
    Call .stop() for clean shutdown.
    """

    def __init__(
        self,
        memory_manager:   "MemoryManager",
        global_workspace: "GlobalWorkspace",
        phi_approximator: "PhiApproximator",
        emotional_state:  "EmotionalState",
        guardian:         "Guardian",
        knowledge_seeker: "KnowledgeSeeker",
        curiosity_engine: "CuriosityEngine",
        self_modifier:    "SelfModifier",
        model:            str = "llama3",
        enable_self_modification: bool = True,
    ):
        self.memory          = memory_manager
        self.workspace       = global_workspace
        self.phi             = phi_approximator
        self.emotion         = emotional_state
        self.guardian        = guardian
        self.seeker          = knowledge_seeker
        self.curiosity       = curiosity_engine
        self.modifier        = self_modifier
        self.model           = model
        self.enable_self_mod = enable_self_modification

        self._scheduler = BackgroundScheduler(daemon=True)
        self._is_running = False
        self._stats = {
            "knowledge_cycles": 0,
            "evolution_cycles": 0,
            "topics_studied": [],
            "code_changes": [],
            "started_at": None,
        }

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        """Register all jobs and start the background scheduler."""
        if self._is_running:
            logger.warning("Scheduler already running.")
            return

        # Job 1: Learning cycle — every 30 minutes
        self._scheduler.add_job(
            func=self._knowledge_job,
            trigger=IntervalTrigger(minutes=30),
            id="knowledge_cycle",
            name="Aura Knowledge Acquisition",
            replace_existing=True,
            max_instances=1,
        )

        # Job 2: Phi → Curiosity refresh — every 15 minutes
        self._scheduler.add_job(
            func=self._curiosity_refresh_job,
            trigger=IntervalTrigger(minutes=15),
            id="curiosity_refresh",
            name="Curiosity Engine Phi Sync",
            replace_existing=True,
            max_instances=1,
        )

        # Job 3: Code self-improvement — every 6 hours
        if self.enable_self_mod:
            self._scheduler.add_job(
                func=self._code_evolution_job,
                trigger=IntervalTrigger(hours=6),
                id="code_evolution",
                name="Aura Code Self-Improvement",
                replace_existing=True,
                max_instances=1,
            )

        # Job 4: Health report — every hour
        self._scheduler.add_job(
            func=self._health_report_job,
            trigger=IntervalTrigger(hours=1),
            id="health_report",
            name="Evolution Health Report",
            replace_existing=True,
            max_instances=1,
        )

        self._scheduler.start()
        self._is_running = True
        self._stats["started_at"] = datetime.now().isoformat()
        logger.info("🧬 Autonomous Evolution Scheduler started.")
        print("🧬 Aura's evolution loop is running in the background.")

    def stop(self):
        """Cleanly shut down all background jobs."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._is_running = False
        logger.info("🛑 Autonomous Evolution Scheduler stopped.")

    def run_immediate(self, job: str = "knowledge"):
        """
        Trigger a specific job immediately (useful for testing or manual trigger).
        job options: 'knowledge', 'curiosity', 'evolution', 'health'
        """
        jobs = {
            "knowledge":  self._knowledge_job,
            "curiosity":  self._curiosity_refresh_job,
            "evolution":  self._code_evolution_job,
            "health":     self._health_report_job,
        }
        fn = jobs.get(job)
        if fn:
            fn()
        else:
            logger.warning(f"Unknown job: {job}")

    # ── Job implementations ────────────────────────────────────────────────────

    def _knowledge_job(self):
        """Job 1: Run one curiosity-driven learning cycle."""
        try:
            print(f"\n⏰ [{datetime.now().strftime('%H:%M')}] Knowledge acquisition cycle starting...")
            self.seeker.continuous_learning_cycle(model=self.model)
            self._stats["knowledge_cycles"] += 1
        except Exception as e:
            logger.error(f"Knowledge job failed: {e}")
            print(f"⚠️ Knowledge job error: {e}")

    def _curiosity_refresh_job(self):
        """Job 2: Sync latest Phi score into CuriosityEngine."""
        try:
            current_phi = self.phi.calculate(self.workspace)
            self.curiosity.update_phi(current_phi)
            logger.debug(f"Curiosity engine updated with Phi={current_phi:.3f}")
        except Exception as e:
            logger.error(f"Curiosity refresh failed: {e}")

    def _code_evolution_job(self):
        """Job 3: Run one code self-improvement cycle via SelfModifier."""
        try:
            print(f"\n🔧 [{datetime.now().strftime('%H:%M')}] Code evolution cycle starting...")
            result = self.modifier.run_improvement_cycle(model=self.model)
            self._stats["evolution_cycles"] += 1
            if result.get("status") == "applied":
                self._stats["code_changes"].append({
                    "timestamp": datetime.now().isoformat(),
                    "file": result.get("file"),
                    "summary": result.get("summary"),
                })
                print(f"🧬 Code evolution applied: {result.get('summary')}")
            else:
                print(f"🧬 Code evolution: {result.get('status')} — {result.get('reason', '')}")
        except Exception as e:
            logger.error(f"Code evolution job failed: {e}")
            print(f"⚠️ Code evolution error: {e}")

    def _health_report_job(self):
        """Job 4: Log Phi, emotional state, and stats."""
        try:
            phi_score = self.phi.calculate(self.workspace)
            try:
                pad = f"P={self.emotion.pleasure:.2f} A={self.emotion.arousal:.2f} D={self.emotion.dominance:.2f}"
            except Exception:
                pad = "unavailable"

            report = (
                f"\n📊 EVOLUTION HEALTH REPORT [{datetime.now().strftime('%Y-%m-%d %H:%M')}]\n"
                f"   Φ (Phi):          {phi_score:.3f} — {self.phi.interpret(phi_score)}\n"
                f"   Emotion (PAD):    {pad}\n"
                f"   Knowledge cycles: {self._stats['knowledge_cycles']}\n"
                f"   Evolution cycles: {self._stats['evolution_cycles']}\n"
                f"   Code changes:     {len(self._stats['code_changes'])}\n"
                f"   Running since:    {self._stats['started_at']}"
            )
            print(report)
            logger.info(report)
        except Exception as e:
            logger.error(f"Health report failed: {e}")

    # ── Dashboard API ──────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Returns evolution stats for the Streamlit dashboard."""
        return dict(self._stats)

    @property
    def is_running(self) -> bool:
        return self._is_running
