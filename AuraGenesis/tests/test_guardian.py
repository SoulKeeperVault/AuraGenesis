import pytest
from aura_guardian.guardian import Main

def test_initialization():
    """Tests the basic initialization of the Main class."""
    instance = Main()
    assert instance is not None, "Instance should not be None"
