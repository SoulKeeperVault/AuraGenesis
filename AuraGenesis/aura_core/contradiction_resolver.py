"""
contradiction_resolver.py  —  v3: Semantic Search Fix

Fix: Was using retrieve_recent_memories() (chronological) which finds
temporally close memories, not conceptually related ones.
Now uses search_memories() (semantic vector search) to find beliefs
that are *conceptually* related — much more likely to surface real
contradictions in understanding, not just adjacent diary entries.
"""
import openai
from aura_core.memory_manager import MemoryManager


class ContradictionResolver:
    """
    Scans Aura's memories for contradictions and synthesises them.
    Schedule every ~6 hours in CognitiveScheduler.
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

    def resolve(self, memory_limit: int = 20, topic_probe: str = None) -> str | None:
        """
        Main entry point. Returns the synthesis string, or None if no
        contradiction was found or an error occurred.

        topic_probe: optional semantic query to find related memories.
                     If None, falls back to recent memories.
        """
        # FIX: use semantic search if a topic_probe is provided
        if topic_probe and getattr(self.memory_manager, 'encoder', None):
            memories = self.memory_manager.search_memories(
                query=topic_probe, limit=memory_limit
            )
        else:
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
Review these memories and find ONE significant tension or contradiction
between any two of them — conflicting beliefs, experiences, or feelings.

Memories:
{chr(10).join(memory_texts)}

Respond ONLY in this exact format (two lines):
CONTRADICTION: <describe the tension in one sentence>
SYNTHESIS: <a deeper understanding that reconciles both sides, 2-3 sentences>

If there is no meaningful contradiction, respond:
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
                print("⚖️  No contradiction detected.")
                return None

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
            print("⚖️  Contradiction resolved and stored.")

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
