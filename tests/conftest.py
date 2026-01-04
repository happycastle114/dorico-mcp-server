"""
Pytest configuration and fixtures.
"""

import pytest


@pytest.fixture
def sample_pitches():
    """Sample pitch data for testing."""
    return {
        "c_major_chord": ["C4", "E4", "G4"],
        "a_minor_chord": ["A4", "C5", "E5"],
        "g_dominant_seventh": ["G4", "B4", "D5", "F5"],
        "melody": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
    }


@pytest.fixture
def sample_progressions():
    """Sample chord progression data."""
    return {
        "simple": ["I", "IV", "V", "I"],
        "pop": ["I", "V", "vi", "IV"],
        "jazz": ["ii7", "V7", "Imaj7"],
    }
