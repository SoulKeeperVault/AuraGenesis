import pytest
from aura_personality.self_journal import Main

def test_initialization():
    """Tests the basic initialization of the Main class."""
    instance = Main()
    assert instance is not None, "Instance should not be None"
