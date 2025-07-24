import pytest
from aura_personality.personality_engine import Main

def test_initialization():
    """Tests the basic initialization of the Main class."""
    instance = Main()
    assert instance is not None, "Instance should not be None"
