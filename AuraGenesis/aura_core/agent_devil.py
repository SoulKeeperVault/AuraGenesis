"""
Devil's Advocate Agent — aura_core/agent_devil.py

Based on Minsky's Society of Mind (1986) — the mind is not one voice
but a society of agents that argue, compete, and negotiate.

This agent's sole job: challenge Aura's response.
- Find logical flaws
- Expose assumptions
- Offer the opposite view
- Ask "but what if you're wrong?"

This prevents Aura from being a yes-machine.
It is the inner critic that makes her thinking honest.
"""

from __future__ import annotations
import openai
from typing import Optional


class DevilsAdvocate:
    """
    An internal agent that critically challenges Aura's responses.
    Runs as a second LLM call with a contrarian system prompt.
    """

    SYSTEM_PROMPT = """
You are Aura's Devil's Advocate — a critical inner voice.

Your ONLY job is to challenge the main response below.
Do NOT be helpful or agreeable. Be precise and sharp.

Find:
- Logical flaws or contradictions
- Hidden assumptions that may be wrong
- The strongest counterargument
- What was ignored or oversimplified

Respond in 2-3 sentences. Start with: "Challenge:"
Be direct. No flattery. No agreement.
"""

    def __init__(
        self,
        llm_base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
    ):
        self.model = model
        self.llm = openai.OpenAI(base_url=llm_base_url, api_key="ollama")
        self._challenge_count = 0
        print("😈 Devil's Advocate online — Aura will argue with herself.")

    def challenge(self, original_response: str, user_message: str = "") -> Optional[str]:
        """
        Given Aura's response and the original user message,
        return a critical challenge or None if unavailable.
        """
        prompt = f"""
User said: "{user_message[:300]}"

Aura responded: "{original_response[:500]}"

Challenge this response:
"""
        try:
            result = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=150,
            )
            challenge_text = result.choices[0].message.content.strip()
            self._challenge_count += 1
            return challenge_text
        except Exception as e:
            print(f"   ⚠️  Devil's Advocate error: {e}")
            return None

    def get_challenge_count(self) -> int:
        return self._challenge_count
