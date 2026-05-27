"""Centralized exception hierarchy for AuraGenesis.

Provides clear, catchable exceptions for different parts of the consciousness system.
"""

class AuraException(Exception):
    """Base exception for all Aura errors."""
    pass


class ConfigurationError(AuraException):
    """Raised when settings or environment are invalid."""
    pass


class GuardianRejectionError(AuraException):
    """Raised when the Guardian rejects a self-modification proposal."""
    pass


class ConsciousnessCycleError(AuraException):
    """Raised when a core consciousness cycle fails."""
    pass


class EmbodimentError(AuraException):
    """Raised when hardware/sensor access fails."""
    pass
