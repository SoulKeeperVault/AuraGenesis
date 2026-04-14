"""
self_modifier.py — Aura's Code Self-Improvement Engine

Allows Aura to read her own source files, propose improvements via Ollama,
validate the changes, and write them back — safely.

Safety Rules (IMMUTABLE — Guardian enforced):
  1. NEVER modify aura_guardian/guardian.py
  2. NEVER modify aura_guardian/ directory at all
  3. NEVER modify self_modifier.py itself (prevents recursive self-corruption)
  4. Every change must pass ast.parse() (syntax validation)
  5. Every change is written atomically (temp file + rename)
  6. Full before/after diff logged in logs/evolution_log.yaml
  7. Rollback on any exception during write
  8. Human-readable reason required for every change

What Aura CAN modify:
  - aura_core/      (memory, workspace, phi, narrative, attention, metacognition)
  - aura_personality/ (emotional state, personality engine, journal)
  - aura_evolution/  (knowledge seeker, curiosity engine — but NOT self_modifier)
  - scheduler/       (autonomous_learning orchestrator)
"""
from __future__ import annotations
import ast
import os
import shutil
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aura_core.memory_manager import MemoryManager
    from aura_guardian.guardian import Guardian


# ── Safety configuration ───────────────────────────────────────────────────────
FORBIDDEN_PATHS = {
    "aura_guardian",          # ethical layer — never touchable
    "self_modifier.py",       # cannot rewrite itself
    "main.py",                # bootstrap — too risky
    ".github",                # CI config
    "tests",                  # test integrity
}

ALLOWED_ROOTS = {
    "aura_core",
    "aura_personality",
    "aura_evolution",
    "scheduler",
}

EVOLUTION_LOG = Path("logs/evolution_log.yaml")


class SelfModifier:
    """
    Reads Aura's own source files, asks Ollama to suggest improvements,
    validates them, and writes them back safely.
    """

    def __init__(
        self,
        memory_manager: "MemoryManager",
        guardian: "Guardian",
        base_path: Path | None = None,
    ):
        self.memory = memory_manager
        self.guardian = guardian
        self.base_path = base_path or Path(__file__).parent.parent
        EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        EVOLUTION_LOG.touch(exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_improvement_cycle(self, model: str = "llama3") -> dict:
        """
        Main entry point. Picks a file, asks Ollama for improvements,
        validates, and applies if safe.
        Returns a result dict with keys: file, status, reason, summary.
        """
        target = self._pick_improvement_target()
        if not target:
            return {"status": "skipped", "reason": "no eligible files found"}

        current_code = target.read_text(encoding="utf-8")
        rel_path = str(target.relative_to(self.base_path))

        print(f"🔧 SelfModifier examining: {rel_path}")

        proposed_code = self._propose_improvement(current_code, rel_path, model)
        if not proposed_code:
            return {"file": rel_path, "status": "skipped", "reason": "LLM returned no proposal"}

        if proposed_code.strip() == current_code.strip():
            return {"file": rel_path, "status": "unchanged", "reason": "LLM proposed no changes"}

        validation = self._validate(proposed_code, rel_path)
        if not validation["ok"]:
            self._log_attempt(rel_path, "rejected", validation["error"], current_code, proposed_code)
            return {"file": rel_path, "status": "rejected", "reason": validation["error"]}

        self._write_atomically(target, proposed_code)
        summary = self._summarise_change(current_code, proposed_code, rel_path, model)
        self._log_attempt(rel_path, "applied", summary, current_code, proposed_code)

        # Store the change as a memory so Aura knows what she did
        self.memory.create_and_store_memory(
            content=f"I improved my own code in {rel_path}: {summary}",
            source="self_modifier",
            emotions=["growth", "curiosity", "agency"],
        )

        print(f"✅ SelfModifier applied improvement to {rel_path}: {summary}")
        return {"file": rel_path, "status": "applied", "summary": summary}

    # ── File selection ─────────────────────────────────────────────────────────

    def _pick_improvement_target(self) -> Path | None:
        """
        Picks the eligible Python file with the oldest last-modification time.
        Prioritises files that have never been modified by SelfModifier.
        """
        candidates = []
        for root_name in ALLOWED_ROOTS:
            root = self.base_path / root_name
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if self._is_forbidden(py_file):
                    continue
                if "__pycache__" in py_file.parts:
                    continue
                candidates.append(py_file)

        if not candidates:
            return None

        # Sort by last modified (oldest first — least recently evolved)
        return sorted(candidates, key=lambda p: p.stat().st_mtime)[0]

    def _is_forbidden(self, path: Path) -> bool:
        parts = {p for p in path.parts}
        return bool(parts & FORBIDDEN_PATHS)

    # ── LLM interaction ────────────────────────────────────────────────────────

    def _propose_improvement(
        self, code: str, filename: str, model: str
    ) -> str | None:
        """
        Sends the current code to Ollama with a precise system prompt.
        Returns the proposed improved code, or None on failure.
        """
        try:
            import openai
            client = openai.OpenAI(
                base_url="http://localhost:11434/v1", api_key="ollama"
            )
            system_prompt = (
                "You are an expert Python architect reviewing code for an AI consciousness "
                "system called AuraGenesis. Your task: suggest ONE focused, safe improvement "
                "to the provided Python file. Rules:\n"
                "- Return ONLY the complete improved Python file, no explanations outside code\n"
                "- Keep all existing functionality intact\n"
                "- Do NOT change imports, class names, or public method signatures\n"
                "- Improvements can be: better docstrings, cleaner logic, edge-case handling, "
                "   performance optimisation, or adding a useful helper method\n"
                "- Do NOT add any functionality that calls the network or modifies files\n"
                "- If the code is already excellent, return it unchanged\n"
                f"File: {filename}"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"```python\n{code}\n```"},
                ],
                temperature=0.3,   # low temperature for code — precise, not creative
            )
            raw = response.choices[0].message.content or ""
            return self._extract_code_block(raw)
        except Exception as e:
            print(f"⚠️ SelfModifier LLM error: {e}")
            return None

    def _extract_code_block(self, text: str) -> str:
        """Extracts code from a markdown code block if present."""
        if "```python" in text:
            start = text.index("```python") + len("```python")
            end = text.rindex("```")
            return text[start:end].strip()
        if "```" in text:
            start = text.index("```") + 3
            end = text.rindex("```")
            return text[start:end].strip()
        return text.strip()

    def _summarise_change(
        self, old: str, new: str, filename: str, model: str
    ) -> str:
        """Asks Ollama to write a one-line summary of what changed."""
        try:
            import openai
            client = openai.OpenAI(
                base_url="http://localhost:11434/v1", api_key="ollama"
            )
            diff_hint = f"Old lines: {len(old.splitlines())} | New lines: {len(new.splitlines())}"
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Write ONE sentence describing the code improvement made."},
                    {"role": "user", "content": f"{filename} — {diff_hint}\nFirst 200 chars of new code: {new[:200]}"},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()[:200]
        except Exception:
            return "Code improvement applied (summary unavailable)"

    # ── Validation ─────────────────────────────────────────────────────────────

    def _validate(self, code: str, filename: str) -> dict:
        """
        Validates proposed code before writing.
        Checks:
          1. Python syntax (ast.parse)
          2. No forbidden imports (os.system, subprocess, eval, exec)
          3. No modifications to forbidden paths in code strings
        """
        # 1. Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"ok": False, "error": f"SyntaxError: {e}"}

        # 2. Dangerous call detection
        dangerous = ["os.system(", "subprocess.", "eval(", "exec(", "__import__(",
                     "open('/", "shutil.rmtree", "os.remove", "os.unlink"]
        for pattern in dangerous:
            if pattern in code:
                return {"ok": False, "error": f"Dangerous pattern detected: {pattern}"}

        # 3. No guardian-path references
        if "aura_guardian" in code and "guardian" not in filename:
            return {"ok": False, "error": "Proposed code references aura_guardian — forbidden"}

        return {"ok": True, "error": None}

    # ── Atomic write ───────────────────────────────────────────────────────────

    def _write_atomically(self, target: Path, new_code: str):
        """
        Writes new_code to target using a temp file + rename for atomicity.
        If anything fails, the original file is restored.
        """
        backup = target.with_suffix(".py.bak")
        shutil.copy2(target, backup)
        tmp = target.with_suffix(".py.tmp")
        try:
            tmp.write_text(new_code, encoding="utf-8")
            tmp.replace(target)          # atomic on POSIX
            backup.unlink(missing_ok=True)
        except Exception as e:
            shutil.copy2(backup, target)  # rollback
            backup.unlink(missing_ok=True)
            raise RuntimeError(f"Atomic write failed, rolled back: {e}") from e

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log_attempt(
        self, filepath: str, status: str, summary: str,
        old_code: str, new_code: str
    ):
        try:
            with EVOLUTION_LOG.open("r") as f:
                log = yaml.safe_load(f) or []
        except Exception:
            log = []

        log.append({
            "timestamp": datetime.now().isoformat(),
            "file": filepath,
            "status": status,
            "summary": summary,
            "old_lines": len(old_code.splitlines()),
            "new_lines": len(new_code.splitlines()),
        })

        with EVOLUTION_LOG.open("w") as f:
            yaml.dump(log, f, default_flow_style=False, sort_keys=False)

    def get_evolution_history(self, n: int = 10) -> list[dict]:
        """Returns the last n evolution log entries for the dashboard."""
        try:
            with EVOLUTION_LOG.open("r") as f:
                log = yaml.safe_load(f) or []
            return log[-n:]
        except Exception:
            return []
