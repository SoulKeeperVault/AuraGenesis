from pathlib import Path

# Update project_root to point one level up from the current file
project_root = Path(__file__).parent.parent

# Import the EmotionalStateEngine instead of EmotionalState
from aura_core.emotional_state import EmotionalStateEngine

# Instantiate the updated emotional state engine
emotional_state = EmotionalStateEngine()