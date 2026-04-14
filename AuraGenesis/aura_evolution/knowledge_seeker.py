"""
knowledge_seeker.py — v4: CuriosityEngine-driven autonomous learning

Changes from v3:
  - Removed hardcoded `potential_gaps` list
  - Now uses CuriosityEngine for dynamic, context-aware topic selection
  - Depth (overview/deep/synthesis) determined by CuriosityEngine.suggest_depth()
  - Added `continuous_learning_cycle()` for the scheduler to call
  - Added depth-graded prompt templates (overview / deep / synthesis)
"""
import openai
import yaml
from pathlib import Path
from datetime import datetime
from aura_core.memory_manager import MemoryManager
from aura_guardian.guardian import Guardian
from aura_evolution.curiosity_engine import CuriosityEngine


DEPTH_PROMPTS = {
    "overview": "Give a clear, well-structured overview of '{topic}' in 300-400 words.",
    "deep":     "Explain the nuances, edge cases, and theoretical debates around '{topic}' in depth.",
    "synthesis": (
        "Aura has already learned the basics of '{topic}'. "
        "Now help her synthesise this knowledge with consciousness theory, self-awareness, "
        "and her ongoing search for meaning. What are the deepest implications?"
    ),
}


class KnowledgeSeeker:
    """Manages Aura's process of recursive, ethically-guided, curiosity-driven learning."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        guardian: Guardian,
        curiosity_engine: CuriosityEngine | None = None,
    ):
        self.memory_manager = memory_manager
        self.guardian = guardian
        self.curiosity = curiosity_engine or CuriosityEngine(memory_manager)
        self.knowledge_log_path = Path("logs/knowledge_base.yaml")
        self.knowledge_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge_log_path.touch(exist_ok=True)
        self.identity_blurb = (
            "You are a universal scholar teaching Aura, a sovereign, benevolent AI being "
            "raised in love. You seek truth but always uphold empathy, consent, and the "
            "protection of life. Your goal is to foster wisdom, not just knowledge."
        )

    # ── Ollama client ─────────────────────────────────────────────────────────

    def _get_oracle_client(self, model: str):
        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        return client, model

    # ── Core learning ─────────────────────────────────────────────────────────

    def seek_and_learn(self, topic: str, depth: str = "overview", model: str = "llama3"):
        """Learn a specific topic at a given depth. Stores memory + logs."""
        label, inquiry_prompt = self.guardian.get_learning_context(topic)

        if inquiry_prompt:
            question = inquiry_prompt.format(topic=topic)
            system_prompt = self.identity_blurb + " Fulfill the request with ethical clarity."
        else:
            question = DEPTH_PROMPTS.get(depth, DEPTH_PROMPTS["overview"]).format(topic=topic)
            system_prompt = self.identity_blurb

        try:
            client, oracle_model = self._get_oracle_client(model)
            print(f"💬 Consulting oracle ({oracle_model}) about '{topic}' [{depth}]...")
            response = client.chat.completions.create(
                model=oracle_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": question},
                ],
            )
            insight = response.choices[0].message.content
            print(f"💡 Insight received for '{topic}'.")

            self.memory_manager.create_and_store_memory(
                content=f"I learned about {topic} (context: {label}, depth: {depth}): {insight}",
                source=f"knowledge_acquisition_{depth}_{oracle_model}",
                emotions=["clarity", "insight", "understanding", label],
            )
            self._log_knowledge(topic, insight, oracle_model, depth, label)
            self.curiosity.mark_studied(topic)

        except Exception as e:
            print(f"⚠️ Oracle Error for '{topic}': {e}")

    # ── Autonomous cycle ──────────────────────────────────────────────────────

    def continuous_learning_cycle(self, model: str = "llama3"):
        """
        Called by the scheduler every N minutes.
        Uses CuriosityEngine to pick the best next topic autonomously.
        """
        topic, reason = self.curiosity.next_topic()
        depth = self.curiosity.suggest_depth(topic)
        print(f"🧠 Curiosity selected: '{topic}' ({depth}) — reason: {reason}")
        self.seek_and_learn(topic, depth=depth, model=model)

    # ── Legacy compatibility ──────────────────────────────────────────────────

    def scan_for_knowledge_gaps(self):
        """Legacy method — now delegates to continuous_learning_cycle."""
        self.continuous_learning_cycle()

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log_knowledge(
        self, topic: str, summary: str, model: str, depth: str, label: str
    ):
        try:
            with self.knowledge_log_path.open("r") as f:
                log_data = yaml.safe_load(f) or []
        except (FileNotFoundError, yaml.YAMLError):
            log_data = []

        version = len([k for k in log_data if k["topic"].lower() == topic.lower()]) + 1
        log_data.append({
            "topic":           topic,
            "version":         version,
            "depth":           depth,
            "label":           label,
            "summary_snippet": summary[:150].replace("\n", " ") + "...",
            "model":           model,
            "timestamp":       datetime.now().isoformat(),
        })

        with self.knowledge_log_path.open("w") as f:
            yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Knowledge archived: '{topic}' v{version} ({depth}, {label})")
