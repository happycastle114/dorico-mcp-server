"""
Tests for instrument database.
"""

import pytest

from dorico_mcp.tools.instruments import (
    INSTRUMENTS,
    InstrumentFamily,
    check_range,
    get_instrument,
    get_transposition_interval,
)


class TestInstrumentDatabase:
    """Tests for instrument database."""

    def test_instruments_exist(self):
        """Check that common instruments are in the database."""
        common_instruments = [
            "violin",
            "viola",
            "cello",
            "flute",
            "oboe",
            "clarinet",
            "horn",
            "trumpet",
            "trombone",
            "piano",
        ]
        for inst in common_instruments:
            assert inst in INSTRUMENTS, f"{inst} not in database"

    def test_get_instrument_by_name(self):
        violin = get_instrument("violin")
        assert violin is not None
        assert violin.name == "Violin"
        assert violin.family == InstrumentFamily.STRING

    def test_get_instrument_case_insensitive(self):
        violin1 = get_instrument("violin")
        violin2 = get_instrument("VIOLIN")
        violin3 = get_instrument("Violin")
        assert violin1 == violin2 == violin3

    def test_get_unknown_instrument(self):
        result = get_instrument("kazoo")
        assert result is None


class TestRangeCheck:
    """Tests for instrument range checking."""

    def test_violin_in_range(self):
        result = check_range("violin", "A4")
        assert result["in_range"] is True
        assert result["in_comfortable_range"] is True

    def test_violin_low_extreme(self):
        result = check_range("violin", "G3")
        assert result["in_range"] is True  # G3 is the lowest string

    def test_violin_too_low(self):
        result = check_range("violin", "F3")
        assert result["in_range"] is False
        assert "issue" in result

    def test_violin_high_extreme(self):
        result = check_range("violin", "E7")
        assert result["in_range"] is True

    def test_piano_full_range(self):
        # Piano has the widest range
        assert check_range("piano", "A0")["in_range"] is True
        assert check_range("piano", "C8")["in_range"] is True

    def test_unknown_instrument(self):
        result = check_range("kazoo", "C4")
        assert "error" in result


class TestTransposition:
    """Tests for transposition intervals."""

    def test_violin_no_transposition(self):
        result = get_transposition_interval("violin")
        assert result["semitones"] == 0

    def test_clarinet_bb_transposition(self):
        result = get_transposition_interval("clarinet")
        assert result["semitones"] == -2  # Sounds M2 lower
        assert result["direction"] == "down"

    def test_horn_f_transposition(self):
        result = get_transposition_interval("horn")
        assert result["semitones"] == -7  # Sounds P5 lower
        assert result["direction"] == "down"

    def test_unknown_instrument_transposition(self):
        result = get_transposition_interval("kazoo")
        assert "error" in result


class TestInstrumentFamilies:
    """Tests for instrument family classification."""

    def test_woodwind_family(self):
        woodwinds = ["flute", "oboe", "clarinet", "bassoon"]
        for inst_name in woodwinds:
            inst = get_instrument(inst_name)
            assert inst.family == InstrumentFamily.WOODWIND

    def test_brass_family(self):
        brass = ["horn", "trumpet", "trombone", "tuba"]
        for inst_name in brass:
            inst = get_instrument(inst_name)
            assert inst.family == InstrumentFamily.BRASS

    def test_string_family(self):
        strings = ["violin", "viola", "cello", "double_bass"]
        for inst_name in strings:
            inst = get_instrument(inst_name)
            assert inst.family == InstrumentFamily.STRING
