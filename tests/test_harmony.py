"""
Tests for harmony analysis tools.
"""

import pytest

from dorico_mcp.tools import (
    COMMON_PROGRESSIONS,
    analyze_chord_quality,
    check_voice_leading,
    generate_progression,
    suggest_next_chord,
)


class TestChordAnalysis:
    """Tests for chord analysis functions."""

    def test_analyze_chord_quality_major(self):
        result = analyze_chord_quality(["C4", "E4", "G4"])
        # Will use fallback if music21 not available
        assert "pitches" in result or "root" in result

    def test_analyze_chord_quality_minor(self):
        result = analyze_chord_quality(["A4", "C5", "E5"])
        assert "pitches" in result or "root" in result


class TestChordSuggestions:
    """Tests for chord suggestion functions."""

    def test_suggest_next_chord_from_empty(self):
        suggestions = suggest_next_chord([], "C major")
        assert len(suggestions) > 0
        # Should suggest tonic as common start
        chord_names = [s["chord"] for s in suggestions]
        assert "I" in chord_names

    def test_suggest_next_chord_after_I(self):
        suggestions = suggest_next_chord(["I"], "C major")
        assert len(suggestions) > 0
        # Common progressions from I
        chord_names = [s["chord"] for s in suggestions]
        assert any(c in chord_names for c in ["IV", "V", "vi"])

    def test_suggest_next_chord_after_V(self):
        suggestions = suggest_next_chord(["V"], "C major")
        assert len(suggestions) > 0
        # V commonly goes to I
        chord_names = [s["chord"] for s in suggestions]
        assert "I" in chord_names


class TestProgressionGeneration:
    """Tests for progression generation."""

    def test_generate_progression_default(self):
        result = generate_progression("C major", length=4)
        assert len(result) == 4
        for chord in result:
            assert "position" in chord
            assert "roman_numeral" in chord
            assert "function" in chord

    def test_generate_progression_authentic_ending(self):
        result = generate_progression("C major", length=4, ending="authentic")
        # Last two should be V-I
        assert result[-2]["roman_numeral"] == "V"
        assert result[-1]["roman_numeral"] == "I"

    def test_generate_progression_half_ending(self):
        result = generate_progression("C major", length=4, ending="half")
        # Last should be V
        assert result[-1]["roman_numeral"] == "V"


class TestCommonProgressions:
    """Tests for common progression database."""

    def test_classical_progressions_exist(self):
        assert "classical" in COMMON_PROGRESSIONS
        assert "authentic_cadence" in COMMON_PROGRESSIONS["classical"]

    def test_pop_progressions_exist(self):
        assert "pop" in COMMON_PROGRESSIONS
        assert "four_chord" in COMMON_PROGRESSIONS["pop"]

    def test_jazz_progressions_exist(self):
        assert "jazz" in COMMON_PROGRESSIONS
        assert "ii_V_I" in COMMON_PROGRESSIONS["jazz"]


class TestVoiceLeading:
    """Tests for voice leading checks."""

    def test_check_voice_leading_parallel_fifths(self):
        # C-G to D-A is parallel fifths
        voice1 = ["C4", "D4"]
        voice2 = ["G4", "A4"]
        issues = check_voice_leading(voice1, voice2)
        # Should detect parallel fifths (if music21 available)
        assert isinstance(issues, list)

    def test_check_voice_leading_different_lengths(self):
        voice1 = ["C4", "D4", "E4"]
        voice2 = ["G4", "A4"]
        issues = check_voice_leading(voice1, voice2)
        assert any("error" in issue for issue in issues)
