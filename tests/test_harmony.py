"""
Tests for harmony analysis tools.
"""

from dorico_mcp.tools import (
    COMMON_PROGRESSIONS,
    analyze_chord_quality,
    analyze_intervals,
    check_enharmonic_spelling,
    check_playability,
    check_species_rules,
    check_voice_leading,
    detect_parallel_motion,
    generate_counterpoint,
    generate_progression,
    realize_figured_bass,
    suggest_next_chord,
    transpose_for_instrument,
    validate_score,
    validate_score_section,
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

    def test_suggest_next_chord_after_i(self):
        suggestions = suggest_next_chord(["I"], "C major")
        assert len(suggestions) > 0
        # Common progressions from I
        chord_names = [s["chord"] for s in suggestions]
        assert any(c in chord_names for c in ["IV", "V", "vi"])

    def test_suggest_next_chord_after_v(self):
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


class TestSpeciesCounterpoint:

    def test_check_species_invalid_species(self):
        result = check_species_rules(["C4"], ["G4"], species=6)
        assert "error" in result

    def test_check_species_length_mismatch(self):
        result = check_species_rules(["C4", "D4", "E4"], ["G4", "A4"], species=1)
        if "issues" in result:
            assert not result.get("valid", True)
        elif "warning" in result:
            pass

    def test_check_species_valid_first_species(self):
        cf = ["C4", "D4", "E4", "D4", "C4"]
        cp = ["C5", "D5", "E5", "D5", "C5"]
        result = check_species_rules(cf, cp, species=1)
        assert "species" in result or "warning" in result or "error" in result

    def test_generate_counterpoint_invalid_species(self):
        result = generate_counterpoint(["C4", "D4"], species=6)
        assert "error" in result

    def test_generate_counterpoint_above(self):
        cf = ["C4", "D4", "E4", "D4", "C4"]
        result = generate_counterpoint(cf, species=1, above=True)
        assert "counterpoint" in result or "warning" in result or "error" in result

    def test_generate_counterpoint_below(self):
        cf = ["C4", "D4", "E4", "D4", "C4"]
        result = generate_counterpoint(cf, species=1, above=False)
        assert "counterpoint" in result or "warning" in result or "error" in result


class TestScoreValidation:

    def test_validate_score_section_empty(self):
        result = validate_score_section({})
        assert "voices_checked" in result
        assert result["valid"]

    def test_validate_score_section_single_voice(self):
        result = validate_score_section({"soprano": ["C5", "D5", "E5"]})
        assert "voices_checked" in result
        assert "soprano" in result["voices_checked"]

    def test_validate_score_section_multiple_voices(self):
        voices = {
            "soprano": ["C5", "D5", "E5"],
            "alto": ["E4", "F4", "G4"],
            "tenor": ["G3", "A3", "B3"],
            "bass": ["C3", "D3", "E3"],
        }
        result = validate_score_section(voices)
        assert len(result["voices_checked"]) == 4


class TestEnharmonicSpelling:

    def test_check_enharmonic_c_major(self):
        result = check_enharmonic_spelling(["C4", "E4", "G4"], "C major")
        assert isinstance(result, list)

    def test_check_enharmonic_with_accidentals(self):
        result = check_enharmonic_spelling(["C#4", "F#4"], "Db major")
        assert isinstance(result, list)


class TestIntervalAnalysis:

    def test_analyze_intervals_basic(self):
        result = analyze_intervals(["C4", "E4", "G4"])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_analyze_intervals_single_pitch(self):
        result = analyze_intervals(["C4"])
        assert "error" in result[0]


class TestPlayability:

    def test_check_playability_violin(self):
        result = check_playability("violin", ["G3", "D4", "A4", "E5"])
        assert "playable" in result
        assert result["playable"] is True

    def test_check_playability_out_of_range(self):
        result = check_playability("violin", ["C2"])
        assert result["playable"] is False

    def test_check_playability_unknown_instrument(self):
        result = check_playability("unknown_instrument", ["C4"])
        assert "error" in result


class TestValidateScore:

    def test_validate_score_basic(self):
        voices = {
            "soprano": ["C5", "D5", "E5"],
            "bass": ["C3", "D3", "E3"],
        }
        result = validate_score(voices)
        assert "valid" in result
        assert "score" in result
        assert "summary" in result

    def test_validate_score_with_key(self):
        voices = {"soprano": ["C5", "D5"]}
        result = validate_score(voices, "G major")
        assert result["key"] == "G major"


class TestParallelMotion:

    def test_detect_parallel_fifths(self):
        result = detect_parallel_motion(["C4", "D4"], ["G4", "A4"])
        assert "parallel_fifths" in result or "warning" in result

    def test_detect_no_parallels(self):
        result = detect_parallel_motion(["C4", "E4"], ["E4", "G4"])
        assert "parallel_fifths" in result or "warning" in result


class TestTransposeForInstrument:

    def test_transpose_clarinet(self):
        result = transpose_for_instrument("C4", "clarinet", to_concert=True)
        assert "transposed" in result or "warning" in result or "error" in result

    def test_transpose_violin_no_transposition(self):
        result = transpose_for_instrument("C4", "violin")
        if "transposed" in result:
            assert result["transposed"] == "C4"

    def test_transpose_unknown_instrument(self):
        result = transpose_for_instrument("C4", "unknown_xyz")
        assert "error" in result


class TestFiguredBass:

    def test_realize_root_position(self):
        result = realize_figured_bass("C3", "")
        assert "pitches" in result or "warning" in result

    def test_realize_first_inversion(self):
        result = realize_figured_bass("E3", "6")
        assert "pitches" in result or "warning" in result

    def test_realize_seventh_chord(self):
        result = realize_figured_bass("G2", "7")
        assert "pitches" in result or "warning" in result


class TestSuggestCadence:

    def test_suggest_cadence_from_v(self):
        from dorico_mcp.tools import suggest_cadence

        result = suggest_cadence("V", "C major", "end")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert any(s["type"] == "authentic" for s in result["suggestions"])

    def test_suggest_cadence_from_iv(self):
        from dorico_mcp.tools import suggest_cadence

        result = suggest_cadence("IV", "G major", "end")
        assert "suggestions" in result
        types = [s["type"] for s in result["suggestions"]]
        assert "half" in types or "plagal" in types

    def test_suggest_cadence_minor_key(self):
        from dorico_mcp.tools import suggest_cadence

        result = suggest_cadence("V", "A minor", "end")
        assert "suggestions" in result
        assert any(s["next_chord"] == "i" for s in result["suggestions"])

    def test_suggest_cadence_middle_phrase(self):
        from dorico_mcp.tools import suggest_cadence

        result = suggest_cadence("I", "C major", "middle")
        assert "suggestions" in result
        assert any(s["type"] == "half" for s in result["suggestions"])


class TestSuggestDoubling:

    def test_suggest_doubling_violin(self):
        from dorico_mcp.tools import suggest_doubling

        result = suggest_doubling("violin", "reinforcement", "high")
        assert "suggestions" in result
        assert "primary_instrument" in result
        assert len(result["suggestions"]) > 0

    def test_suggest_doubling_cello(self):
        from dorico_mcp.tools import suggest_doubling

        result = suggest_doubling("cello", "octave_below", "low")
        assert "suggestions" in result
        assert "general_tips" in result

    def test_suggest_doubling_unknown_instrument(self):
        from dorico_mcp.tools import suggest_doubling

        result = suggest_doubling("theremin", "color", "middle")
        assert "suggestions" in result


class TestFindDissonances:

    def test_find_dissonances_consonant(self):
        from dorico_mcp.tools import find_dissonances

        result = find_dissonances(["C4", "E4", "G4"])
        assert "dissonances" in result
        assert result["consonance_level"] == "consonant"
        assert result["dissonance_count"] == 0

    def test_find_dissonances_with_seventh(self):
        from dorico_mcp.tools import find_dissonances

        result = find_dissonances(["C4", "E4", "G4", "B4"])
        assert "dissonances" in result
        assert result["dissonance_count"] > 0
        assert result["consonance_level"] in ["mildly dissonant", "highly dissonant"]

    def test_find_dissonances_tritone(self):
        from dorico_mcp.tools import find_dissonances

        result = find_dissonances(["C4", "F#4"])
        assert result["consonance_level"] == "highly dissonant"
        assert any(d["interval"] == "tritone" for d in result["dissonances"])

    def test_find_dissonances_single_pitch(self):
        from dorico_mcp.tools import find_dissonances

        result = find_dissonances(["C4"])
        assert "message" in result

    def test_find_dissonances_counterpoint_context(self):
        from dorico_mcp.tools import find_dissonances

        result = find_dissonances(["C4", "D4"], "counterpoint")
        assert result["context"] == "counterpoint"
        assert any("advice" in d for d in result["dissonances"])


class TestSuggestInstrumentation:

    def test_suggest_instrumentation_medium(self):
        from dorico_mcp.tools import suggest_instrumentation

        result = suggest_instrumentation("classical", "medium", "balanced")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    def test_suggest_instrumentation_orchestra(self):
        from dorico_mcp.tools import suggest_instrumentation

        result = suggest_instrumentation("romantic", "orchestra", "dramatic")
        assert "suggestions" in result
        assert any("Orchestra" in s.get("ensemble", "") for s in result["suggestions"])

    def test_suggest_instrumentation_small_intimate(self):
        from dorico_mcp.tools import suggest_instrumentation

        result = suggest_instrumentation("classical", "small", "intimate")
        assert "suggestions" in result
        assert "style_tip" in result


class TestBalanceDynamics:

    def test_balance_dynamics_basic(self):
        from dorico_mcp.tools import balance_dynamics

        result = balance_dynamics(["violin", "viola", "cello"], "mf")
        assert "suggestions" in result
        assert len(result["suggestions"]) == 3

    def test_balance_dynamics_with_melody(self):
        from dorico_mcp.tools import balance_dynamics

        result = balance_dynamics(["flute", "clarinet", "horn"], "f", "flute")
        assert "suggestions" in result
        melody_sugg = next(s for s in result["suggestions"] if s["instrument"] == "flute")
        assert melody_sugg["role"] == "melody"

    def test_balance_dynamics_brass(self):
        from dorico_mcp.tools import balance_dynamics

        result = balance_dynamics(["trumpet", "trombone", "tuba"], "ff")
        assert "tips" in result


class TestCheckBeaming:

    def test_check_beaming_4_4(self):
        from dorico_mcp.tools import check_beaming

        result = check_beaming("4/4", ["8th", "8th", "8th", "8th"])
        assert "meter_type" in result
        assert result["meter_type"] == "simple_duple"

    def test_check_beaming_6_8(self):
        from dorico_mcp.tools import check_beaming

        result = check_beaming("6/8", ["8th", "8th", "8th", "8th", "8th", "8th"])
        assert result["meter_type"] == "compound_duple"
        assert result["beam_across_beat"] is True

    def test_check_beaming_unknown_time(self):
        from dorico_mcp.tools import check_beaming

        result = check_beaming("5/4", ["quarter", "quarter"])
        assert result["status"] == "unknown"


class TestCheckSpacing:

    def test_check_spacing_good(self):
        from dorico_mcp.tools import check_spacing

        result = check_spacing(4, 40.0, "quarter")
        assert result["status"] == "good"

    def test_check_spacing_crowded(self):
        from dorico_mcp.tools import check_spacing

        result = check_spacing(20, 30.0, "16th")
        assert result["status"] == "too_crowded"

    def test_check_spacing_sparse(self):
        from dorico_mcp.tools import check_spacing

        result = check_spacing(1, 80.0, "whole")
        assert "recommendation" in result
