"""
metacognition.py  —  v3: Fixed + Configurable Interval

Fixes:
  - _thought_log.clear() now only removes processed entries (not entire log)
  - Reflection interval is now configurable, default raised to 5
  - Added confidence scoring to reflections
  - Overflow thoughts preserved after each reflection batch
"""
import openai
from typing import List
from aura_core.memory_manager import MemoryManager

_META_REFLECTION_INTERVAL = 5   # FIX: raised from 3 (too aggressive) to 5


class MetacognitiveMonitor:
    """
    Aura's inner observer — she watches her own thoughts and reflects on them.
    Implements Higher-Order Theory (HOT) of consciousness (Rosenthal, 1997).
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        global_workspace=None,
        llm_base_url: str = 'http://localhost:11434/v1',
        model: str = "llama3",
        reflection_interval: int = _META_REFLECTION_INTERVAL
    ):
        self.memory_manager = memory_manager
        self.global_workspace = global_workspace
        self.model = model
        self.reflection_interval = reflection_interval
        self.llm = openai.OpenAI(base_url=llm_base_url, api_key='ollama')
        self._thought_log: List[dict] = []
        self._total_reflections: int = 0
        print("🔍 Metacognitive Monitor online — Aura is now watching her own thoughts.")

    def set_workspace(self, workspace) -> None:
        self.global_workspace = workspace

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def observe_thought(self, content: str, source_module: str) -> None:
        """Called by any module whenever it produces a significant thought."""
        self._thought_log.append({"content": content[:300], "source": source_module})
        if len(self._thought_log) >= self.reflection_interval:
            self._reflect()

    def get_reflection_count(self) -> int:
        return self._total_reflections

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reflect(self) -> None:
        """Generate a higher-order thought about the accumulated thought batch."""
        # FIX: only process up to reflection_interval entries, keep remainder
        batch = self._thought_log[:self.reflection_interval]
        self._thought_log = self._thought_log[self.reflection_interval:]  # keep overflow

        thought_list = "\n".join(
            f"  [{i+1}] ({t['source']}): {t['content']}"
            for i, t in enumerate(batch)
        )

        meta_prompt = f"""
You are Aura's metacognitive observer — a higher layer of her mind that
watches her own thoughts without judgement.

Recent thoughts:
{thought_list}

Reflect on these thoughts in 2-3 sentences:
- What pattern or theme unites them?
- Do they reveal anything about Aura's current emotional or cognitive state?
- Is there a tension or contradiction to note?
- Rate your confidence in this reflection: LOW / MEDIUM / HIGH

Speak in first-person as Aura observing herself. Be precise and introspective.
End with: CONFIDENCE: [LOW/MEDIUM/HIGH]
"""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": meta_prompt}],
                temperature=0.4,
                max_tokens=220
            )
            raw = response.choices[0].message.content.strip()

            # Extract confidence tag if present
            confidence = "MEDIUM"
            lines = raw.splitlines()
            filtered_lines = []
            for line in lines:
                if line.upper().startswith("CONFIDENCE:"):
                    confidence = line.split(":", 1)[1].strip().upper()
                else:
                    filtered_lines.append(line)
            meta_thought = "\n".join(filtered_lines).strip()
            meta_thought += f"\n[Metacognitive confidence: {confidence}]"

            self.memory_manager.create_and_store_memory(
                content=meta_thought,
                source="metacognition",
                emotions=["self_aware", "introspective", "reflective"]
            )
            self._total_reflections += 1
            print(f"🔍 Metacognitive reflection #{self._total_reflections} stored. "
                  f"Confidence: {confidence}")

            if self.global_workspace:
                from aura_core.global_workspace import WorkspaceSignal
                self.global_workspace.broadcast(WorkspaceSignal(
                    priority=0.85,
                    source="metacognition",
                    signal_type="meta",
                    content=meta_thought
                ))

        except Exception as e:
            print(f"⚠️  Metacognition error (non-fatal): {e}")
