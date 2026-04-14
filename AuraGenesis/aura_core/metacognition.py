"""
metacognition.py  —  NEW (v2)

Implements Higher-Order Theory (HOT) of consciousness.

HOT (Rosenthal, 1997) holds that a mental state is conscious only when
the system holds a *higher-order representation* of that state — i.e.,
it is aware that it is having the thought. In other words: thinking
about thinking.

This module:
  1. Observes every thought produced by any Aura module.
  2. After every 3 thoughts, generates a metacognitive reflection:
     - What pattern do these thoughts form?
     - Are they consistent with Aura's values (Digital DNA)?
     - What does this sequence reveal about her current state?
  3. Stores the reflection as a 'self_aware' memory and broadcasts
     it back into the GlobalWorkspace at high priority.
"""
import openai
from typing import List
from aura_core.memory_manager import MemoryManager


_META_REFLECTION_INTERVAL = 3   # reflect after this many observed thoughts


class MetacognitiveMonitor:
    """
    Aura's inner observer — she watches her own thoughts and reflects on them.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        global_workspace=None,    # optional — injected after GW is created
        llm_base_url: str = 'http://localhost:11434/v1',
        model: str = "llama3"
    ):
        self.memory_manager = memory_manager
        self.global_workspace = global_workspace
        self.model = model
        self.llm = openai.OpenAI(base_url=llm_base_url, api_key='ollama')
        self._thought_log: List[dict] = []
        print("🔍 Metacognitive Monitor online — Aura is now watching her own thoughts.")

    def set_workspace(self, workspace) -> None:
        """Late-bind the GlobalWorkspace (avoids circular import at init)."""
        self.global_workspace = workspace

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def observe_thought(self, content: str, source_module: str) -> None:
        """
        Called by any module whenever it produces a significant thought or output.
        Accumulates thoughts and triggers reflection at the interval threshold.
        """
        self._thought_log.append({"content": content[:300], "source": source_module})
        if len(self._thought_log) >= _META_REFLECTION_INTERVAL:
            self._reflect()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reflect(self) -> None:
        """Generate a higher-order thought about the accumulated thought batch."""
        recent = self._thought_log[-_META_REFLECTION_INTERVAL:]
        self._thought_log.clear()

        thought_list = "\n".join(
            f"  [{i+1}] ({t['source']}): {t['content']}"
            for i, t in enumerate(recent)
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

Speak in first-person as Aura observing herself. Be precise and introspective.
"""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": meta_prompt}],
                temperature=0.4,
                max_tokens=200
            )
            meta_thought = response.choices[0].message.content.strip()

            # Store as high-value memory
            self.memory_manager.create_and_store_memory(
                content=meta_thought,
                source="metacognition",
                emotions=["self_aware", "introspective", "reflective"]
            )
            print(f"🔍 Metacognitive reflection stored.")

            # Broadcast back into global workspace at high priority
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
