"""Exceptions for candidate-only projection boundaries."""


class CandidateOnlyViolationError(ValueError):
    """Raised when a model proposal attempts to control a trusted state."""
