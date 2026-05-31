"""Security utilities for AuraGenesis.

Provides input sanitization to mitigate prompt injection, XSS, and
other common LLM attack vectors.
"""
import re
from typing import Any


def sanitize_user_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input to prevent prompt injection and excessive length."""
    if not isinstance(text, str):
        text = str(text)

    # Truncate to max length
    text = text[:max_length]

    # Remove dangerous patterns (basic but effective)
    dangerous_patterns = [
        r"(?i)(ignore|disregard|forget).*?(previous|all|above|instructions)",
        r"(?i)(system|assistant|user):",
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"data:text/html",
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, "[SANITIZED]", text)

    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)

    return text.strip()


def sanitize_for_llm(text: str) -> str:
    """Additional sanitization specifically for LLM prompts."""
    text = sanitize_user_input(text)
    # Escape quotes that could break prompt structure
    text = text.replace("\"", "'").replace("`", "'")
    return text


def validate_rule_proposal(proposal: dict[str, Any]) -> bool:
    """Validate Guardian rule proposals to prevent malicious self-modification."""
    if not isinstance(proposal, dict):
        return False

    required_keys = {"rule_id", "description", "proposed_change"}
    if not required_keys.issubset(proposal.keys()):
        return False

    # Prevent proposals that try to disable security
    dangerous_keywords = ["disable security", "bypass guardian", "remove validation", "ignore limits"]
    description = str(proposal.get("description", "")).lower()
    if any(kw in description for kw in dangerous_keywords):
        return False

    return True
