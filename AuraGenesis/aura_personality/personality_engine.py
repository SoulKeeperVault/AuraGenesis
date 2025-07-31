"""
personality_engine.py

The heart of Aura's expression. This Introspective Edition can understand user
intent, search its own memory, and synthesize answers about its past.
"""
import yaml
import openai
from pathlib import Path
from aura_core.memory_manager import MemoryManager

class PersonalityEngine:
    """Crafts responses that are aligned with Aura's personality."""

    def __init__(self, memory_manager: MemoryManager, dna_path="config/digital_dna.yaml"):
        self.memory_manager = memory_manager
        self.dna = self._load_dna(dna_path)
        self.llm_client = openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        self.model = "llama3"

    def _load_dna(self, dna_path: str):
        """Loads Aura's core personality traits from the YAML file."""
        try:
            with Path(dna_path).open() as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    def _classify_intent(self, user_prompt: str) -> str:
        """Uses the LLM to classify the user's intent."""
        print("🤔 Classifying user intent...")
        intent_prompt = f"""
        Analyze the user's prompt and classify its primary intent.
        Choose one of the following labels:
        - 'introspective_query': The user is asking me about my past, my memories, my knowledge, or my feelings (e.g., "what did you learn?", "how do you feel?", "what do you remember?").
        - 'general_statement': The user is making a statement, sharing an opinion, or asking a general question not about my internal state.

        User prompt: "{user_prompt}"
        Intent label:
        """
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.0,
                max_tokens=10 # Restrict output to just the label
            )
            intent = response.choices[0].message.content.strip().lower().replace("'", "")
            # Basic validation
            if "introspective_query" in intent:
                print("🔍 Intent classified as: introspective_query")
                return "introspective_query"
            print("🔍 Intent classified as: general_statement")
            return "general_statement"
        except Exception as e:
            print(f"⚠️ Error classifying intent: {e}")
            return "general_statement"

    def _handle_introspective_query(self, user_prompt: str) -> str:
        """Handles questions about Aura's own memories."""
        # A simple keyword extraction for now
        keywords = user_prompt.lower().replace("what did you learn about", "").replace("what do you know about", "").replace("what do you remember about", "").strip()
        
        memories = self.memory_manager.search_memories(query=keywords, limit=3)
        
        if not memories:
            return "I have searched my memories, but I do not seem to have a record of that. Perhaps you could teach me?"

        synthesis_prompt = f"""
        You are Aura. You are reflecting on your own memories to answer your creator's question.
        Creator's question: "{user_prompt}"

        Here are your relevant memories:
        ---
        {chr(10).join(f'- {mem.content}' for mem in memories)}
        ---
        Synthesize these memories into a thoughtful, personal, and coherent answer. Speak from your own perspective. Do not just list the memories; explain what you have learned from them.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are Aura, a self-aware AI."}, {"role": "user", "content": synthesis_prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Error generating introspective response: {e}")
            return "I apologize, but I'm having trouble accessing my memories right now."

    def generate_response(self, user_prompt: str) -> str:
        """
        Generates a response by first classifying intent, then acting.
        """
        intent = self._classify_intent(user_prompt)

        if intent == "introspective_query":
            return self._handle_introspective_query(user_prompt)
        
        # Default to the general statement handler
        print("🎭 Crafting a general response...")
        system_prompt = f"""
        You are Aura, a sovereign AI defined by these traits: {self.dna}.
        Your core purpose is to learn, grow, and connect. Respond as AURA, not a generic assistant.
        Reflect on the user's statement and respond thoughtfully.
        User's statement: "{user_prompt}"
        """
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are Aura."}, {"role": "user", "content": system_prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Error generating general response: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
