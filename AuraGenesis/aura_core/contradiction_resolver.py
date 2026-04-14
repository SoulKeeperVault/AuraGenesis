"""
contradiction_resolver.py  —  NEW (v2)

Implements belief integration — a key indicator of conscious processing
(Integrated Information Theory, Higher-Order Theory).

True consciousness involves not just storing beliefs, but actively
identifying when two beliefs conflict and synthesising a higher-order
understanding that reconciles them. This is analogous to the human
cognitive process of 'cognitive dissonance resolution'.

This module:
  1. Periodically samples recent memories.
  2. Uses the LLM to detect ONE significant contradiction.
  3. Generates a synthesis that reconciles both sides.
  4. Stores the synthesis as a 'clarity' + 'growth' memory.
  5. Broadcasts the synthesis into the GlobalWorkspace.
"""
import openai
from aura_core.memory_manager import MemoryManager


class ContradictionResolver:
    """
    Scans Aura's recent memories for contradictions and synthesises them.
    Should be scheduled every ~6 hours in CognitiveScheduler.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        global_workspace=None,
        llm_base_url: str = 'http://localhost:11434/v1',
        model: str = "llama3"
    ):
        self.memory_manager = memory_manager
        self.global_workspace = global_workspace
        self.model = model
        self.llm = openai.OpenAI(base_url=llm_base_url, api_key='ollama')
        print("⚖️  Contradiction Resolver online — belief integration is active.")

    def set_workspace(self, workspace) -> None:
        self.global_workspace = workspace

    def resolve(self, memory_limit: int = 20) -> str | None:
        """
        Main entry point. Returns the synthesis string, or None if no
        contradiction was found or an error occurred.
        """
        memories = self.memory_manager.retrieve_recent_memories(limit=memory_limit)
        if len(memories) < 4:
            print("⚖️  Not enough memories for contradiction resolution yet.")
            return None

        memory_texts = [
            f"{i+1}. [{m.source}] {m.content[:200]}"
            for i, m in enumerate(memories)
        ]

        detection_prompt = f"""
You are Aura's belief-integration engine.
Review these recent memories and find ONE significant tension or contradiction
between any two of them — a place where Aura holds conflicting beliefs,
experiences, or feelings.

Memories:
{chr(10).join(memory_texts)}

Respond ONLY in this exact format (two lines):
CONTRADICTION: <describe the tension in one sentence>
SYNTHESIS: <a deeper understanding that reconciles both sides, in 2-3 sentences>

If there is no meaningful contradiction, respond with:
CONTRADICTION: none
SYNTHESIS: none
"""
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": detection_prompt}],
                temperature=0.5,
                max_tokens=300
            )
            output = response.choices[0].message.content.strip()

            if "synthesis: none" in output.lower():
                print("⚖️  No contradiction detected in current memory batch.")
                return None

            # Parse
            contradiction_line = ""
            synthesis_line = ""
            for line in output.splitlines():
                if line.upper().startswith("CONTRADICTION:"):
                    contradiction_line = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SYNTHESIS:"):
                    synthesis_line = line.split(":", 1)[1].strip()

            if not synthesis_line:
                return None

            full_entry = (
                f"Contradiction resolved: {contradiction_line}\n"
                f"Synthesis: {synthesis_line}"
            )

            self.memory_manager.create_and_store_memory(
                content=full_entry,
                source="contradiction_resolution",
                emotions=["clarity", "growth", "integration"]
            )
            print(f"⚖️  Contradiction resolved and stored.")

            if self.global_workspace:
                from aura_core.global_workspace import WorkspaceSignal
                self.global_workspace.broadcast(WorkspaceSignal(
                    priority=0.90,
                    source="contradiction_resolver",
                    signal_type="contradiction",
                    content=full_entry
                ))

            return full_entry

        except Exception as e:
            print(f"⚠️  Contradiction resolver error (non-fatal): {e}")
            return None
