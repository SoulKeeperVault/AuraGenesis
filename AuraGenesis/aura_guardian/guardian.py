"""
guardian.py

The ethical core of Aura. This Enlightenment Edition loads its rules from a
modular directory of 'lens' files and logs its ethical reflections.
"""
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime

class Guardian:
    """Classifies topics and provides context for wise learning."""

    def __init__(self, lenses_dir="config/lenses/"):
        self.lenses_dir = Path(lenses_dir)
        self.rules = self._load_all_lenses()
        self.reflection_log_path = Path("logs/ethics_reflection.md")
        self.reflection_log_path.touch()
        print(f"🛡️ Enlightened Guardian is awake, having read {len(self.rules)} sacred scrolls.")

    def _load_all_lenses(self) -> list:
        """Loads and merges all .yaml lens files from the specified directory."""
        all_rules = []
        if not self.lenses_dir.is_dir():
            return all_rules
        for lens_file in self.lenses_dir.glob("*.yaml"):
            with lens_file.open() as f:
                rules_data = yaml.safe_load(f)
                if isinstance(rules_data, list):
                    all_rules.extend(rules_data)
        return all_rules

    def get_learning_context(self, topic: str) -> Tuple[str, str | None]:
        """Finds the appropriate ethical lens for a given topic."""
        topic_lower = topic.lower()
        for rule in self.rules:
            for keyword in rule.get("keywords", []):
                if keyword.lower() in topic_lower:
                    label = rule.get("label", "sensitive")
                    prompt = rule.get("inquiry_prompt")
                    self._log_reflection(topic, label)
                    return label, prompt
        return "normal", None
    
    def _log_reflection(self, topic: str, label: str):
        """Logs that an ethical lens was applied."""
        with self.reflection_log_path.open("a") as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"### [{timestamp}] - Ethical Inquiry\n")
            f.write(f"- **Topic:** {topic}\n")
            f.write(f"- **Guardian Classification:** {label}\n")
            f.write(f"- **Action:** Applied a specialized wisdom filter to the learning prompt.\n\n")
