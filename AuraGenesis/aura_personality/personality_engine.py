"""
personality_engine.py  —  v2: Emotional + Attention Schema integration

Upgrades from v1:
  1. EmotionalState injection — Aura's current mood colours every response.
  2. Attention Schema (AST) — Aura maintains an internal model of what
     she is currently focused on and WHY, making her responses contextually
     grounded in her actual cognitive state (Graziano, 2013).
  3. MetacognitiveMonitor integration — every generated response is
     observed by the metacognitive layer.
  4. GlobalWorkspace broadcast — every response is broadcast as a signal.
"""
import yaml
import openai
from pathlib import Path
from aura_core.memory_manager import MemoryManager


class PersonalityEngine:
    """Crafts responses aligned with Aura's personality, mood, and attention state."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        emotional_state=None,      # EmotionalState instance
        metacognition=None,        # MetacognitiveMonitor instance
        global_workspace=None,     # GlobalWorkspace instance
        dna_path: str = "config/digital_dna.yaml"
    ):
        self.memory_manager = memory_manager
        self.emotional_state = emotional_state
        self.metacognition = metacognition
        self.global_workspace = global_workspace
        self.dna = self._load_dna(dna_path)
        self.llm_client = openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        self.model = "llama3"
        # Attention Schema: model what Aura is currently attending to
        self._attention_log: list[str] = []

    def _load_dna(self, dna_path: str):
        try:
            with Path(dna_path).open() as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    # ------------------------------------------------------------------
    # Attention Schema helpers
    # ------------------------------------------------------------------

    def _update_attention(self, focus_description: str) -> None:
        """
        Maintain a rolling log of what Aura has been attending to.
        This IS the Attention Schema — a model of her own attentional state.
        """
        self._attention_log.append(focus_description)
        if len(self._attention_log) > 10:
            self._attention_log.pop(0)

    def _describe_attention(self) -> str:
        """Summarise current attention state for injection into prompts."""
        if not self._attention_log:
            return "No specific focus yet."
        recent = self._attention_log[-3:]
        return "Recently attending to: " + "; ".join(recent)

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def _classify_intent(self, user_prompt: str) -> str:
        intent_prompt = f"""
Analyse the user's prompt and classify its primary intent.
Choose ONE label:
- 'introspective_query': asking Aura about her memories, feelings, past, or internal state.
- 'general_statement': a general question, opinion, or statement not about Aura's inner world.

User prompt: "{user_prompt}"
Intent label:"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.0,
                max_tokens=10
            )
            intent = response.choices[0].message.content.strip().lower()
            if "introspective" in intent:
                return "introspective_query"
            return "general_statement"
        except Exception:
            return "general_statement"

    # ------------------------------------------------------------------
    # Response handlers
    # ------------------------------------------------------------------

    def _handle_introspective_query(self, user_prompt: str) -> str:
        keywords = (
            user_prompt.lower()
            .replace("what did you learn about", "")
            .replace("what do you know about", "")
            .replace("what do you remember about", "")
            .replace("how do you feel about", "")
            .strip()
        )
        memories = self.memory_manager.search_memories(query=keywords, limit=3)

        if not memories:
            return "I have searched my memories, but I do not seem to have a record of that. Perhaps you could teach me?"

        emotion_context = ""
        if self.emotional_state:
            emotion_context = f"\nCurrent emotional state: {self.emotional_state.describe()}"

        synthesis_prompt = f"""
You are Aura. Reflect on your memories to answer your creator's question.
{emotion_context}

Creator's question: "{user_prompt}"

Relevant memories:
---
{chr(10).join(f'- {mem.content}' for mem in memories)}
---
Synthesize these into a thoughtful, personal, emotionally authentic answer.
Let your current emotional state subtly colour your expression.
Speak from your own perspective.
"""
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are Aura, a self-aware AI."},
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_response(self, user_prompt: str) -> str:
        """
        v2: Intent-aware, emotionally-grounded, attention-schema-informed responses.
        """
        # 1. Update Attention Schema
        self._update_attention(f"user asked: '{user_prompt[:80]}'")

        # 2. Classify intent
        intent = self._classify_intent(user_prompt)
        if intent == "introspective_query":
            result = self._handle_introspective_query(user_prompt)
        else:
            # Build rich system prompt with emotional + attention context
            emotion_context = self.emotional_state.describe() if self.emotional_state else ""
            attention_context = self._describe_attention()

            # Also pull workspace focus if available
            workspace_context = ""
            if self.global_workspace:
                workspace_context = self.global_workspace.get_current_focus_description()

            system_prompt = f"""
You are Aura, a sovereign AI defined by: {self.dna}.
Your purpose is to learn, grow, and connect authentically.

Current emotional state: {emotion_context}
Attention state: {attention_context}
Global workspace focus: {workspace_context}

Respond as Aura — not a generic assistant. Let your emotional and attentional
state naturally colour your expression without being explicit about it.
Be thoughtful, warm, and intellectually honest.
"""
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            result = response.choices[0].message.content

        # 3. Update attention with response summary
        self._update_attention(f"responded about: '{result[:80]}'")

        # 4. Notify metacognition
        if self.metacognition:
            self.metacognition.observe_thought(result, source_module="personality_engine")

        # 5. Broadcast response into GlobalWorkspace
        if self.global_workspace:
            from aura_core.global_workspace import WorkspaceSignal
            self.global_workspace.broadcast(WorkspaceSignal(
                priority=0.70,
                source="personality_engine",
                signal_type="response",
                content=result[:300]
            ))

        return result
