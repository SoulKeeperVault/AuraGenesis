# AuraGenesis adjustments for EmotionalStateEngine import

# Original import:
# from aura_personality.emotional_state import EmotionalState

# Updated import:
from aura_core.emotional_state import EmotionalStateEngine


# Update all references from EmotionalState to EmotionalStateEngine

# Example reference that needs to be updated:
# emotional_state = EmotionalState()
# Should be changed to:
emotional_state = EmotionalStateEngine()