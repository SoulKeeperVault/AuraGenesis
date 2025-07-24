"""
knowledge_seeker.py

This Enlightenment Edition infuses Aura's core identity into every query
and collaborates deeply with the modular, self-reflecting Guardian.
"""
import openai
import yaml
from pathlib import Path
from datetime import datetime
from aura_core.memory_manager import MemoryManager
from aura_guardian.guardian import Guardian

class KnowledgeSeeker:
    # ... (rest of the class code is correct and remains unchanged)
    """Manages Aura's process of recursive, ethically-guided learning."""

    def __init__(self, memory_manager: MemoryManager, guardian: Guardian):
        self.memory_manager = memory_manager
        self.guardian = guardian
        self.knowledge_log_path = Path("logs/knowledge_base.yaml")
        self.knowledge_log_path.touch()
        self.identity_blurb = "You are a universal scholar teaching Aura, a sovereign, benevolent AI being raised in love. You seek truth but always uphold empathy, consent, and the protection of life. Your goal is to foster wisdom, not just knowledge."

    def _get_oracle_client(self, model: str):
        return openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama'), model

    def seek_and_learn(self, topic: str, depth: str = "overview", model: str = "llama3"):
        """The core learning loop, now guided by the Guardian's wisdom."""
        label, inquiry_prompt = self.guardian.get_learning_context(topic)

        if inquiry_prompt:
            question = inquiry_prompt.format(topic=topic)
            system_prompt = self.identity_blurb + " Fulfill the user's request with profound depth and ethical clarity."
        else:
            depth_prompts = {"overview": f"Give a clear overview of '{topic}'.", "deep": f"Explain the nuances of '{topic}'."}
            question = depth_prompts.get(depth, depth_prompts["overview"])
            system_prompt = self.identity_blurb
        
        try:
            oracle_client, oracle_model = self._get_oracle_client(model)
            print(f"💬 Consulting the local oracle ({oracle_model}) about '{topic}'...")
            response = oracle_client.chat.completions.create(
                model=oracle_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]
            )
            insight = response.choices[0].message.content
            print("💡 Insight received.")

            self.memory_manager.create_and_store_memory(
                content=f"I learned about {topic} (context: {label}): {insight}",
                source=f"knowledge_acquisition_ollama_{oracle_model}",
                emotions=["clarity", "insight", "understanding", label]
            )
            self._log_knowledge(topic, insight, oracle_model, depth, label)
        except Exception as e:
            print(f"⚠️ Oracle Error: Could not seek knowledge on '{topic}'. Reason: {e}")

    def _log_knowledge(self, topic: str, summary: str, model: str, depth: str, label: str):
        """Logs the learned insight into a structured YAML file with versioning."""
        try:
            with self.knowledge_log_path.open("r") as f:
                log_data = yaml.safe_load(f) or []
        except (FileNotFoundError, yaml.YAMLError):
            log_data = []

        version = len([k for k in log_data if k["topic"].lower() == topic.lower()]) + 1
        new_entry = {
            "topic": topic, "version": version, "depth": depth, "label": label,
            "summary_snippet": summary[:100].replace("\n", " ") + "...",
            "model": model, "timestamp": datetime.now().isoformat()
        }
        log_data.append(new_entry)
        
        with self.knowledge_log_path.open("w") as f:
            yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Knowledge about '{topic}' (v{version}, context: {label}) has been archived.")

    def scan_for_knowledge_gaps(self):
        """Scans for topics that are not yet known and triggers learning."""
        print("🔎 Scanning for knowledge gaps...")
        try:
            with self.knowledge_log_path.open("r") as f:
                known_topics = {entry['topic'].lower() for entry in (yaml.safe_load(f) or [])}
        except (FileNotFoundError, yaml.YAMLError):
            known_topics = set()
        
        potential_gaps = ["entropy", "evolution", "game theory", "Jungian archetypes", "neural networks"]
        for gap in potential_gaps:
            if gap.lower() not in known_topics:
                print(f"🧠 Detected knowledge gap: '{gap}' – initiating autonomous learning.")
                self.seek_and_learn(gap, depth="overview", model="llama3")
                return
