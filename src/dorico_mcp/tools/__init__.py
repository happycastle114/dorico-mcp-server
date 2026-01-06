"""
Harmony Analysis Tools.

This module provides music theory analysis and generation capabilities
using the music21 library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType

MUSIC21_AVAILABLE = False
music21: ModuleType | None = None
chord: ModuleType | None = None
key: ModuleType | None = None
roman: ModuleType | None = None

try:
    import music21 as _music21
    from music21 import chord as _chord
    from music21 import key as _key
    from music21 import roman as _roman

    music21 = _music21
    chord = _chord
    key = _key
    roman = _roman
    MUSIC21_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# Chord Progression Database
# =============================================================================

# Common chord progressions in Roman numerals
COMMON_PROGRESSIONS = {
    "classical": {
        "authentic_cadence": ["V", "I"],
        "half_cadence": ["I", "V"],
        "plagal_cadence": ["IV", "I"],
        "deceptive_cadence": ["V", "vi"],
        "circle_of_fifths": ["I", "IV", "vii°", "iii", "vi", "ii", "V", "I"],
        "pachelbel": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
    },
    "pop": {
        "four_chord": ["I", "V", "vi", "IV"],
        "fifties": ["I", "vi", "IV", "V"],
        "axis": ["vi", "IV", "I", "V"],
        "blues_basic": ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"],
    },
    "jazz": {
        "ii_V_I": ["ii7", "V7", "Imaj7"],
        "rhythm_changes_a": ["Imaj7", "vi7", "ii7", "V7"],
        "turnaround": ["Imaj7", "vi7", "ii7", "V7"],
        "minor_ii_V_i": ["iiø7", "V7b9", "i7"],
    },
}

# Standard voice leading rules
VOICE_LEADING_RULES = {
    "parallel_fifths": "Parallel perfect fifths between voices are forbidden",
    "parallel_octaves": "Parallel octaves between voices are forbidden",
    "hidden_fifths": "Hidden fifths (contrary motion to P5 with soprano leap) avoid if possible",
    "hidden_octaves": "Hidden octaves should be avoided in outer voices",
    "voice_crossing": "Voices should not cross each other",
    "voice_overlap": "A voice should not go above/below adjacent voice's previous note",
    "leading_tone_resolution": "Leading tone (^7) should resolve up to tonic",
    "seventh_resolution": "Chord sevenths should resolve down by step",
    "doubled_leading_tone": "Do not double the leading tone",
}


# =============================================================================
# Analysis Functions
# =============================================================================


def analyze_chord_quality(pitches: list[str]) -> dict[str, Any]:
    """
    Analyze a chord and determine its quality.

    Args:
        pitches: List of pitch names (e.g., ["C4", "E4", "G4"])

    Returns:
        Dictionary with root, quality, and other analysis
    """
    if not MUSIC21_AVAILABLE:
        return _fallback_chord_analysis(pitches)

    try:
        # Create music21 chord
        c = chord.Chord(pitches)

        return {
            "root": c.root().name if c.root() else "Unknown",
            "quality": c.quality,
            "bass": c.bass().name if c.bass() else "Unknown",
            "inversion": c.inversion(),
            "common_name": c.commonName,
            "pitches": [p.nameWithOctave for p in c.pitches],
            "intervals": [str(i) for i in c.orderedPitchClasses],
        }
    except Exception as e:
        return {"error": str(e), "pitches": pitches}


def analyze_roman_numeral(
    pitches: list[str],
    key_str: str,
) -> dict[str, Any]:
    """
    Analyze a chord as a Roman numeral in a given key.

    Args:
        pitches: List of pitch names
        key_str: Key string (e.g., "C major", "A minor")

    Returns:
        Dictionary with Roman numeral analysis
    """
    if not MUSIC21_AVAILABLE:
        return {"error": "music21 not available", "pitches": pitches}

    try:
        # Parse key
        parts = key_str.lower().split()
        root = parts[0].upper()
        mode = "minor" if "minor" in key_str.lower() else "major"
        k = key.Key(root, mode)

        # Create chord
        c = chord.Chord(pitches)

        # Get Roman numeral
        rn = roman.romanNumeralFromChord(c, k)

        return {
            "roman_numeral": rn.figure,
            "key": str(k),
            "quality": rn.quality,
            "function": _get_harmonic_function(rn.figure),
            "secondary": rn.secondaryRomanNumeral is not None,
        }
    except Exception as e:
        return {"error": str(e)}


def suggest_next_chord(
    previous_chords: list[str],
    key_str: str,
    style: str = "classical",
) -> list[dict[str, Any]]:
    """
    Suggest possible next chords based on context.

    Args:
        previous_chords: List of previous chord Roman numerals
        key_str: Current key
        style: Style of suggestions (classical, pop, jazz)

    Returns:
        List of suggested chords with explanations
    """
    suggestions = []

    if not previous_chords:
        # Starting suggestions
        suggestions = [
            {"chord": "I", "reason": "Tonic - stable starting point", "probability": 0.4},
            {"chord": "vi", "reason": "Relative minor - softer opening", "probability": 0.2},
            {"chord": "IV", "reason": "Subdominant - creates motion", "probability": 0.2},
        ]
        return suggestions

    last_chord = previous_chords[-1].upper().replace("7", "")

    # Common progressions based on last chord
    progressions = {
        "I": [
            {"chord": "IV", "reason": "Subdominant - natural progression", "probability": 0.3},
            {"chord": "V", "reason": "Dominant - creates tension", "probability": 0.3},
            {"chord": "vi", "reason": "Relative minor - smooth voice leading", "probability": 0.2},
            {"chord": "ii", "reason": "Supertonic - pre-dominant function", "probability": 0.1},
        ],
        "II": [
            {"chord": "V", "reason": "Dominant - ii-V progression", "probability": 0.5},
            {"chord": "vii°", "reason": "Leading tone chord", "probability": 0.2},
        ],
        "IV": [
            {"chord": "V", "reason": "Dominant - strong progression", "probability": 0.4},
            {"chord": "I", "reason": "Plagal motion", "probability": 0.2},
            {"chord": "ii", "reason": "Supertonic - descending bass", "probability": 0.2},
        ],
        "V": [
            {
                "chord": "I",
                "reason": "Authentic cadence - strongest resolution",
                "probability": 0.5,
            },
            {"chord": "vi", "reason": "Deceptive cadence - unexpected", "probability": 0.2},
            {"chord": "IV", "reason": "Retrogression - back-cycling", "probability": 0.1},
        ],
        "VI": [
            {"chord": "IV", "reason": "Subdominant - common progression", "probability": 0.3},
            {"chord": "ii", "reason": "Supertonic - circle of fifths", "probability": 0.3},
            {"chord": "V", "reason": "Dominant preparation", "probability": 0.2},
        ],
    }

    # Get suggestions for last chord
    key_upper = last_chord.upper().replace("M", "").replace("°", "")
    if key_upper in progressions:
        suggestions = progressions[key_upper]
    else:
        # Default suggestions
        suggestions = [
            {"chord": "I", "reason": "Return to tonic", "probability": 0.3},
            {"chord": "V", "reason": "Dominant function", "probability": 0.3},
        ]

    return suggestions


def generate_progression(
    key_str: str,
    length: int = 4,
    style: str = "classical",
    ending: str = "authentic",
) -> list[dict[str, Any]]:
    """
    Generate a chord progression.

    Args:
        key_str: Key (e.g., "C major")
        length: Number of chords
        style: Style (classical, pop, jazz)
        ending: Cadence type (authentic, half, plagal, deceptive)

    Returns:
        List of chords with Roman numerals and explanations
    """
    result = []

    # Get a template progression
    if style in COMMON_PROGRESSIONS:
        style_progs = COMMON_PROGRESSIONS[style]
        # Pick a progression that fits the length
        for _name, prog in style_progs.items():
            if len(prog) >= length:
                base_prog = prog[:length]
                break
        else:
            base_prog = list(style_progs.values())[0][:length]
    else:
        base_prog = ["I", "IV", "V", "I"][:length]

    # Adjust ending based on cadence type
    if length >= 2:
        if ending == "authentic":
            base_prog[-2:] = ["V", "I"]
        elif ending == "half":
            base_prog[-1] = "V"
        elif ending == "plagal":
            base_prog[-2:] = ["IV", "I"]
        elif ending == "deceptive":
            base_prog[-2:] = ["V", "vi"]

    for i, rn in enumerate(base_prog):
        result.append(
            {
                "position": i + 1,
                "roman_numeral": rn,
                "function": _get_harmonic_function(rn),
            }
        )

    return result


def check_voice_leading(
    voice1: list[str],
    voice2: list[str],
) -> list[dict[str, Any]]:
    """
    Check for voice leading issues between two voices.

    Args:
        voice1: List of pitches for first voice
        voice2: List of pitches for second voice

    Returns:
        List of issues found
    """
    issues = []

    if len(voice1) != len(voice2):
        return [{"error": "Voices must have same length"}]

    if not MUSIC21_AVAILABLE:
        return [{"warning": "music21 not available, limited analysis"}]

    try:
        for i in range(len(voice1) - 1):
            # Get pitches
            p1_start = music21.pitch.Pitch(voice1[i])
            p1_end = music21.pitch.Pitch(voice1[i + 1])
            p2_start = music21.pitch.Pitch(voice2[i])
            p2_end = music21.pitch.Pitch(voice2[i + 1])

            # Calculate intervals
            interval_start = music21.interval.Interval(p1_start, p2_start)
            interval_end = music21.interval.Interval(p1_end, p2_end)

            # Check for parallel fifths
            if interval_start.simpleName == "P5" and interval_end.simpleName == "P5":
                issues.append(
                    {
                        "type": "parallel_fifths",
                        "location": f"beats {i + 1}-{i + 2}",
                        "severity": "error",
                        "description": "Parallel perfect fifths detected",
                    }
                )

            # Check for parallel octaves
            if interval_start.simpleName in ["P1", "P8"] and interval_end.simpleName in [
                "P1",
                "P8",
            ]:
                issues.append(
                    {
                        "type": "parallel_octaves",
                        "location": f"beats {i + 1}-{i + 2}",
                        "severity": "error",
                        "description": "Parallel octaves/unisons detected",
                    }
                )

            # Check for voice crossing
            if p1_start.midi > p2_start.midi and p1_end.midi < p2_end.midi:
                issues.append(
                    {
                        "type": "voice_crossing",
                        "location": f"beat {i + 2}",
                        "severity": "warning",
                        "description": "Voices cross each other",
                    }
                )

    except Exception as e:
        issues.append({"error": str(e)})

    return issues


# =============================================================================
# Helper Functions
# =============================================================================


def _get_harmonic_function(roman_numeral: str) -> str:
    """Get harmonic function (T, S, D) for a Roman numeral."""
    rn = roman_numeral.upper().replace("7", "").replace("°", "")

    tonic_chords = ["I", "III", "VI"]
    subdominant_chords = ["II", "IV"]
    dominant_chords = ["V", "VII"]

    if rn in tonic_chords:
        return "Tonic (T)"
    elif rn in subdominant_chords:
        return "Subdominant (S)"
    elif rn in dominant_chords:
        return "Dominant (D)"
    else:
        return "Unknown"


def _fallback_chord_analysis(pitches: list[str]) -> dict[str, Any]:
    """Fallback chord analysis when music21 is not available."""
    # Simple analysis based on intervals
    if len(pitches) < 2:
        return {"error": "Need at least 2 pitches"}

    return {
        "pitches": pitches,
        "note": "Install music21 for detailed analysis",
        "count": len(pitches),
    }


# =============================================================================
# Counterpoint Analysis Functions
# =============================================================================

# Species counterpoint interval rules
SPECIES_RULES = {
    1: {  # First species - note against note
        "allowed_intervals": ["P1", "m3", "M3", "P5", "m6", "M6", "P8"],
        "start_intervals": ["P1", "P5", "P8"],
        "end_intervals": ["P1", "P8"],
        "forbidden": ["parallel_fifths", "parallel_octaves", "direct_fifths", "direct_octaves"],
        "max_leap": 8,  # octave
    },
    2: {  # Second species - two notes against one
        "strong_beat_intervals": ["P1", "m3", "M3", "P5", "m6", "M6", "P8"],
        "weak_beat_allowed": ["m2", "M2", "m3", "M3", "P4", "P5", "m6", "M6"],  # passing tones ok
        "start_intervals": ["P1", "P5", "P8"],
        "end_intervals": ["P1", "P8"],
    },
    3: {  # Third species - four notes against one
        "first_beat_intervals": ["P1", "m3", "M3", "P5", "m6", "M6", "P8"],
        "other_beats_allowed": "passing_neighbor",
    },
    4: {  # Fourth species - syncopation/suspensions
        "suspensions": ["4-3", "7-6", "9-8", "2-3"],  # 2-3 for bass
        "tied_dissonance_resolves_down": True,
    },
    5: {  # Fifth species - florid
        "combines_all": True,
    },
}


def check_species_rules(
    cantus_firmus: list[str],
    counterpoint: list[str],
    species: int = 1,
) -> dict[str, Any]:
    """
    Check species counterpoint rules.

    Args:
        cantus_firmus: List of pitches for the cantus firmus
        counterpoint: List of pitches for the counterpoint line
        species: Species number (1-5)

    Returns:
        Dictionary with analysis results and any rule violations
    """
    if species not in SPECIES_RULES:
        return {"error": f"Species must be 1-5, got {species}"}

    issues: list[dict[str, Any]] = []
    rules = SPECIES_RULES[species]

    if not MUSIC21_AVAILABLE:
        return {
            "warning": "music21 not available, limited analysis",
            "species": species,
            "cantus_length": len(cantus_firmus),
            "counterpoint_length": len(counterpoint),
        }

    try:
        # For first species, lengths must match
        if species == 1 and len(cantus_firmus) != len(counterpoint):
            issues.append(
                {
                    "type": "length_mismatch",
                    "severity": "error",
                    "description": f"First species requires equal lengths. CF: {len(cantus_firmus)}, CP: {len(counterpoint)}",
                }
            )
            return {"issues": issues, "valid": False}

        # Analyze intervals
        intervals_analysis: list[dict[str, Any]] = []
        for i, (cf_pitch, cp_pitch) in enumerate(zip(cantus_firmus, counterpoint, strict=True)):
            cf_p = music21.pitch.Pitch(cf_pitch)
            cp_p = music21.pitch.Pitch(cp_pitch)
            interval = music21.interval.Interval(cf_p, cp_p)

            intervals_analysis.append(
                {
                    "position": i + 1,
                    "cf": cf_pitch,
                    "cp": cp_pitch,
                    "interval": interval.simpleName,
                    "direction": interval.direction,
                }
            )

            # Check first species rules
            if species == 1:
                allowed = rules.get("allowed_intervals", [])
                start_allowed = rules.get("start_intervals", [])
                end_allowed = rules.get("end_intervals", [])

                if interval.simpleName not in allowed:
                    issues.append(
                        {
                            "type": "dissonance",
                            "position": i + 1,
                            "severity": "error",
                            "description": f"Dissonant interval {interval.simpleName} at position {i + 1}",
                        }
                    )

                if i == 0 and interval.simpleName not in start_allowed:
                    issues.append(
                        {
                            "type": "bad_opening",
                            "severity": "error",
                            "description": f"Must start with P1, P5, or P8. Got {interval.simpleName}",
                        }
                    )

                if i == len(cantus_firmus) - 1 and interval.simpleName not in end_allowed:
                    issues.append(
                        {
                            "type": "bad_ending",
                            "severity": "error",
                            "description": f"Must end with P1 or P8. Got {interval.simpleName}",
                        }
                    )

        # Check for parallel fifths and octaves
        for i in range(len(intervals_analysis) - 1):
            curr = intervals_analysis[i]
            next_int = intervals_analysis[i + 1]

            if curr["interval"] == "P5" and next_int["interval"] == "P5":
                issues.append(
                    {
                        "type": "parallel_fifths",
                        "position": f"{i + 1}-{i + 2}",
                        "severity": "error",
                        "description": "Parallel perfect fifths",
                    }
                )

            if curr["interval"] in ["P1", "P8"] and next_int["interval"] in ["P1", "P8"]:
                issues.append(
                    {
                        "type": "parallel_octaves",
                        "position": f"{i + 1}-{i + 2}",
                        "severity": "error",
                        "description": "Parallel octaves/unisons",
                    }
                )

        # Check melodic motion in counterpoint
        for i in range(len(counterpoint) - 1):
            cp1 = music21.pitch.Pitch(counterpoint[i])
            cp2 = music21.pitch.Pitch(counterpoint[i + 1])
            melodic_interval = abs(cp2.midi - cp1.midi)

            # Check for large leaps
            if melodic_interval > 12:  # larger than octave
                issues.append(
                    {
                        "type": "large_leap",
                        "position": f"{i + 1}-{i + 2}",
                        "severity": "warning",
                        "description": f"Leap of {melodic_interval} semitones exceeds octave",
                    }
                )

        return {
            "species": species,
            "intervals": intervals_analysis,
            "issues": issues,
            "valid": len([i for i in issues if i.get("severity") == "error"]) == 0,
            "error_count": len([i for i in issues if i.get("severity") == "error"]),
            "warning_count": len([i for i in issues if i.get("severity") == "warning"]),
        }

    except Exception as e:
        return {"error": str(e)}


def generate_counterpoint(
    cantus_firmus: list[str],
    species: int = 1,
    above: bool = True,
) -> dict[str, Any]:
    """
    Generate a counterpoint line for a given cantus firmus.

    Args:
        cantus_firmus: List of pitches for the cantus firmus
        species: Species number (1-5)
        above: If True, generate counterpoint above CF; if False, below

    Returns:
        Generated counterpoint with analysis
    """
    if species not in [1, 2, 3, 4, 5]:
        return {"error": f"Species must be 1-5, got {species}"}

    if not MUSIC21_AVAILABLE:
        return {
            "warning": "music21 not available, using simplified generation",
            "counterpoint": _simple_counterpoint(cantus_firmus, above),
        }

    try:
        counterpoint: list[str] = []
        _ = SPECIES_RULES.get(species, SPECIES_RULES[1])

        cf_pitches = [music21.pitch.Pitch(p) for p in cantus_firmus]  # type: ignore[union-attr]

        if species == 1:
            for i, cf_p in enumerate(cf_pitches):
                cp_p = cf_p.transpose("P8" if above else "-P8") if i == 0 else None
                if i == 0 or i == len(cf_pitches) - 1:
                    cp_p = cf_p.transpose("P8") if above else cf_p.transpose("-P8")
                else:
                    candidates = []
                    for interval_name in ["M3", "m3", "M6", "m6", "P5"]:
                        try:
                            candidate = (
                                cf_p.transpose(interval_name)
                                if above
                                else cf_p.transpose("-" + interval_name)
                            )
                            candidates.append(candidate)
                        except Exception:
                            pass

                    if counterpoint and candidates:
                        prev_cp = music21.pitch.Pitch(counterpoint[-1])  # type: ignore[union-attr]
                        best = min(candidates, key=lambda c: abs(c.midi - prev_cp.midi))
                        cp_p = best
                    elif candidates:
                        cp_p = candidates[0]
                    else:
                        cp_p = cf_p.transpose("P8" if above else "-P8")

                counterpoint.append(cp_p.nameWithOctave)

        validation = check_species_rules(cantus_firmus, counterpoint, species)

        return {
            "cantus_firmus": cantus_firmus,
            "counterpoint": counterpoint,
            "species": species,
            "position": "above" if above else "below",
            "validation": validation,
        }

    except Exception as e:
        return {"error": str(e)}


def _simple_counterpoint(cantus_firmus: list[str], above: bool = True) -> list[str]:
    result: list[str] = []
    for pitch in cantus_firmus:
        note = pitch[:-1]
        octave = int(pitch[-1])
        new_octave = octave + 1 if above else octave - 1
        result.append(f"{note}{new_octave}")
    return result


# =============================================================================
# Score Validation Functions
# =============================================================================


def validate_score_section(
    pitches_by_voice: dict[str, list[str]],
    key_str: str = "C major",
) -> dict[str, Any]:
    """
    Validate a section of score for common issues.

    Args:
        pitches_by_voice: Dictionary mapping voice names to pitch lists
        key_str: Key for analysis

    Returns:
        Validation results with issues found
    """
    all_issues: list[dict[str, Any]] = []

    voice_names = list(pitches_by_voice.keys())

    # Check voice leading between all voice pairs
    for i in range(len(voice_names)):
        for j in range(i + 1, len(voice_names)):
            v1_name = voice_names[i]
            v2_name = voice_names[j]
            v1_pitches = pitches_by_voice[v1_name]
            v2_pitches = pitches_by_voice[v2_name]

            if len(v1_pitches) == len(v2_pitches):
                issues = check_voice_leading(v1_pitches, v2_pitches)
                for issue in issues:
                    issue["voices"] = f"{v1_name} - {v2_name}"
                    all_issues.append(issue)

    # Check range for each voice (basic check)
    voice_ranges = {
        "soprano": (60, 81),  # C4 - A5
        "alto": (55, 74),  # G3 - D5
        "tenor": (48, 67),  # C3 - G4
        "bass": (40, 60),  # E2 - C4
    }

    if MUSIC21_AVAILABLE:
        for voice_name, pitches in pitches_by_voice.items():
            voice_lower = voice_name.lower()
            if voice_lower in voice_ranges:
                low, high = voice_ranges[voice_lower]
                for i, pitch in enumerate(pitches):
                    try:
                        p = music21.pitch.Pitch(pitch)
                        if p.midi < low:
                            all_issues.append(
                                {
                                    "type": "out_of_range",
                                    "voice": voice_name,
                                    "position": i + 1,
                                    "pitch": pitch,
                                    "severity": "warning",
                                    "description": f"{pitch} is below {voice_name} range",
                                }
                            )
                        elif p.midi > high:
                            all_issues.append(
                                {
                                    "type": "out_of_range",
                                    "voice": voice_name,
                                    "position": i + 1,
                                    "pitch": pitch,
                                    "severity": "warning",
                                    "description": f"{pitch} is above {voice_name} range",
                                }
                            )
                    except Exception:
                        pass

    return {
        "voices_checked": voice_names,
        "issues": all_issues,
        "error_count": len([i for i in all_issues if i.get("severity") == "error"]),
        "warning_count": len([i for i in all_issues if i.get("severity") == "warning"]),
        "valid": len([i for i in all_issues if i.get("severity") == "error"]) == 0,
    }


def check_enharmonic_spelling(
    pitches: list[str],
    key_str: str = "C major",
) -> list[dict[str, Any]]:
    """
    Check for potentially incorrect enharmonic spellings.

    Args:
        pitches: List of pitches to check
        key_str: Key context for determining correct spelling

    Returns:
        List of potential spelling issues
    """
    issues: list[dict[str, Any]] = []

    if not MUSIC21_AVAILABLE:
        return [{"warning": "music21 not available for enharmonic analysis"}]

    try:
        # Parse key
        parts = key_str.lower().split()
        root = parts[0].upper()
        mode = "minor" if "minor" in key_str.lower() else "major"
        k = key.Key(root, mode)

        # Get scale pitches for the key
        scale_pitches = [p.name for p in k.pitches]

        for i, pitch_str in enumerate(pitches):
            p = music21.pitch.Pitch(pitch_str)
            pitch_name = p.name  # e.g., "C#" or "Db"

            # Check if this spelling makes sense in the key
            # Common enharmonic issues
            enharmonic_pairs = {
                "C#": "Db",
                "Db": "C#",
                "D#": "Eb",
                "Eb": "D#",
                "F#": "Gb",
                "Gb": "F#",
                "G#": "Ab",
                "Ab": "G#",
                "A#": "Bb",
                "Bb": "A#",
                "B": "Cb",
                "Cb": "B",
                "E": "Fb",
                "Fb": "E",
                "B#": "C",
                "C": "B#",
                "E#": "F",
                "F": "E#",
            }

            if pitch_name in enharmonic_pairs:
                alternative = enharmonic_pairs[pitch_name]
                # Check if alternative is in scale
                alt_base = alternative[0]
                if alt_base in [sp[0] for sp in scale_pitches] and pitch_name[0] not in [
                    sp[0] for sp in scale_pitches
                ]:
                    issues.append(
                        {
                            "position": i + 1,
                            "current": pitch_str,
                            "suggested": alternative + pitch_str[-1],  # keep octave
                            "reason": f"In {key_str}, {alternative} may be more appropriate than {pitch_name}",
                            "severity": "suggestion",
                        }
                    )

    except Exception as e:
        issues.append({"error": str(e)})

    return issues


def analyze_intervals(pitches: list[str]) -> list[dict[str, Any]]:
    """
    Analyze intervals between consecutive pitches.

    Args:
        pitches: List of pitches to analyze (e.g., ["C4", "E4", "G4"])

    Returns:
        List of interval analyses
    """
    if len(pitches) < 2:
        return [{"error": "Need at least 2 pitches to analyze intervals"}]

    if not MUSIC21_AVAILABLE:
        return _fallback_interval_analysis(pitches)

    try:
        intervals: list[dict[str, Any]] = []
        for i in range(len(pitches) - 1):
            p1 = music21.pitch.Pitch(pitches[i])  # type: ignore[union-attr]
            p2 = music21.pitch.Pitch(pitches[i + 1])  # type: ignore[union-attr]
            interval = music21.interval.Interval(p1, p2)  # type: ignore[union-attr]

            semitones = p2.midi - p1.midi
            is_consonant = interval.simpleName in ["P1", "m3", "M3", "P5", "m6", "M6", "P8"]

            intervals.append(
                {
                    "from": pitches[i],
                    "to": pitches[i + 1],
                    "name": interval.niceName,
                    "simple_name": interval.simpleName,
                    "semitones": semitones,
                    "direction": "ascending"
                    if semitones > 0
                    else "descending"
                    if semitones < 0
                    else "unison",
                    "consonant": is_consonant,
                }
            )

        return intervals

    except Exception as e:
        return [{"error": str(e)}]


def _fallback_interval_analysis(pitches: list[str]) -> list[dict[str, Any]]:
    return [{"warning": "music21 not available", "pitches": pitches}]


def check_playability(
    instrument: str,
    pitches: list[str],
) -> dict[str, Any]:
    """
    Check if a passage is playable on an instrument.

    Args:
        instrument: Instrument name
        pitches: List of pitches to check

    Returns:
        Playability analysis with issues
    """
    from dorico_mcp.tools.instruments import check_range, get_instrument

    issues: list[dict[str, Any]] = []
    inst_info = get_instrument(instrument)

    if not inst_info:
        return {"error": f"Unknown instrument: {instrument}"}

    for i, pitch in enumerate(pitches):
        result = check_range(instrument, pitch)
        if not result.get("in_range", True):
            issues.append(
                {
                    "position": i + 1,
                    "pitch": pitch,
                    "type": "out_of_range",
                    "severity": "error",
                    "message": result.get("issue", f"{pitch} is out of range"),
                }
            )
        elif not result.get("in_comfortable_range", True):
            issues.append(
                {
                    "position": i + 1,
                    "pitch": pitch,
                    "type": "extreme_range",
                    "severity": "warning",
                    "message": result.get("warning", f"{pitch} is in extreme range"),
                }
            )

    if MUSIC21_AVAILABLE and len(pitches) >= 2:
        for i in range(len(pitches) - 1):
            p1 = music21.pitch.Pitch(pitches[i])  # type: ignore[union-attr]
            p2 = music21.pitch.Pitch(pitches[i + 1])  # type: ignore[union-attr]
            leap = abs(p2.midi - p1.midi)

            if leap > 24:
                issues.append(
                    {
                        "position": f"{i + 1}-{i + 2}",
                        "type": "large_leap",
                        "severity": "warning",
                        "message": f"Large leap of {leap} semitones may be difficult",
                    }
                )

    return {
        "instrument": instrument,
        "pitch_count": len(pitches),
        "playable": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues,
        "error_count": len([i for i in issues if i["severity"] == "error"]),
        "warning_count": len([i for i in issues if i["severity"] == "warning"]),
    }


def validate_score(
    voices: dict[str, list[str]],
    key_str: str = "C major",
    check_ranges: bool = True,
    check_voice_leading: bool = True,
) -> dict[str, Any]:
    """
    Comprehensive score validation.

    Args:
        voices: Dictionary mapping voice/instrument names to pitch lists
        key_str: Key for analysis
        check_ranges: Check voice ranges
        check_voice_leading: Check voice leading rules

    Returns:
        Complete validation report
    """
    all_issues: list[dict[str, Any]] = []

    vl_result = validate_score_section(voices, key_str) if check_voice_leading else {"issues": []}
    all_issues.extend(vl_result.get("issues", []))

    if check_ranges:
        voice_ranges = {
            "soprano": (60, 81),
            "alto": (55, 74),
            "tenor": (48, 67),
            "bass": (40, 60),
        }

        if MUSIC21_AVAILABLE:
            for voice_name, pitches in voices.items():
                voice_lower = voice_name.lower()
                if voice_lower in voice_ranges:
                    low, high = voice_ranges[voice_lower]
                    for i, pitch in enumerate(pitches):
                        try:
                            p = music21.pitch.Pitch(pitch)  # type: ignore[union-attr]
                            if p.midi < low or p.midi > high:
                                all_issues.append(
                                    {
                                        "type": "range_violation",
                                        "voice": voice_name,
                                        "position": i + 1,
                                        "pitch": pitch,
                                        "severity": "warning",
                                    }
                                )
                        except Exception:
                            pass

    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]

    return {
        "voices": list(voices.keys()),
        "key": key_str,
        "valid": len(errors) == 0,
        "score": 100 - (len(errors) * 10) - (len(warnings) * 2),
        "issues": all_issues,
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "total_issues": len(all_issues),
        },
    }


def detect_parallel_motion(
    voice1: list[str],
    voice2: list[str],
) -> dict[str, Any]:
    """
    Detect parallel fifths and octaves between two voices.

    Args:
        voice1: List of pitches for first voice
        voice2: List of pitches for second voice

    Returns:
        Detection results with parallel motion instances
    """
    if len(voice1) != len(voice2):
        return {"error": "Voices must have same length"}

    parallel_fifths: list[dict[str, Any]] = []
    parallel_octaves: list[dict[str, Any]] = []

    if not MUSIC21_AVAILABLE:
        return {"warning": "music21 not available"}

    try:
        for i in range(len(voice1) - 1):
            p1_start = music21.pitch.Pitch(voice1[i])  # type: ignore[union-attr]
            p1_end = music21.pitch.Pitch(voice1[i + 1])  # type: ignore[union-attr]
            p2_start = music21.pitch.Pitch(voice2[i])  # type: ignore[union-attr]
            p2_end = music21.pitch.Pitch(voice2[i + 1])  # type: ignore[union-attr]

            int_start = music21.interval.Interval(p1_start, p2_start)  # type: ignore[union-attr]
            int_end = music21.interval.Interval(p1_end, p2_end)  # type: ignore[union-attr]

            if int_start.simpleName == "P5" and int_end.simpleName == "P5":
                parallel_fifths.append(
                    {
                        "position": f"{i + 1}-{i + 2}",
                        "from": f"{voice1[i]}-{voice2[i]}",
                        "to": f"{voice1[i + 1]}-{voice2[i + 1]}",
                    }
                )

            if int_start.simpleName in ["P1", "P8"] and int_end.simpleName in ["P1", "P8"]:
                parallel_octaves.append(
                    {
                        "position": f"{i + 1}-{i + 2}",
                        "from": f"{voice1[i]}-{voice2[i]}",
                        "to": f"{voice1[i + 1]}-{voice2[i + 1]}",
                    }
                )

        return {
            "parallel_fifths": parallel_fifths,
            "parallel_octaves": parallel_octaves,
            "has_parallels": len(parallel_fifths) > 0 or len(parallel_octaves) > 0,
            "fifths_count": len(parallel_fifths),
            "octaves_count": len(parallel_octaves),
        }

    except Exception as e:
        return {"error": str(e)}


def transpose_for_instrument(
    pitch: str,
    instrument: str,
    to_concert: bool = True,
) -> dict[str, Any]:
    """
    Transpose a pitch for a transposing instrument.

    Args:
        pitch: Pitch to transpose (e.g., "C4")
        instrument: Instrument name (e.g., "clarinet", "horn")
        to_concert: If True, convert written to concert; if False, concert to written

    Returns:
        Transposed pitch and interval info
    """
    from dorico_mcp.tools.instruments import get_instrument

    inst_info = get_instrument(instrument)
    if not inst_info:
        return {"error": f"Unknown instrument: {instrument}"}

    transposition = inst_info.transposition
    if transposition == 0:
        return {
            "original": pitch,
            "transposed": pitch,
            "instrument": instrument,
            "transposition": "none (concert pitch)",
            "semitones": 0,
        }

    if not MUSIC21_AVAILABLE:
        return {"warning": "music21 not available for transposition"}

    try:
        p = music21.pitch.Pitch(pitch)  # type: ignore[union-attr]
        semitones = transposition if to_concert else -transposition
        transposed = p.transpose(semitones)

        direction = "up" if semitones > 0 else "down"
        return {
            "original": pitch,
            "transposed": transposed.nameWithOctave,
            "instrument": instrument,
            "direction": "written_to_concert" if to_concert else "concert_to_written",
            "semitones": abs(transposition),
            "transpose_direction": direction,
        }

    except Exception as e:
        return {"error": str(e)}


FIGURED_BASS_INTERVALS = {
    "": [0, 4, 7],
    "6": [0, 3, 7],
    "64": [0, 5, 9],
    "7": [0, 4, 7, 10],
    "65": [0, 3, 6, 8],
    "43": [0, 3, 6, 9],
    "42": [0, 2, 6, 8],
    "6/3": [0, 3, 7],
    "5/3": [0, 4, 7],
}


def realize_figured_bass(
    bass_pitch: str,
    figures: str = "",
    key_str: str = "C major",
) -> dict[str, Any]:
    """
    Realize figured bass notation into chord pitches.

    Args:
        bass_pitch: Bass note (e.g., "C3")
        figures: Figured bass notation (e.g., "6", "64", "7", "65")
        key_str: Key context

    Returns:
        Realized chord pitches
    """
    intervals = FIGURED_BASS_INTERVALS.get(figures, FIGURED_BASS_INTERVALS[""])

    if not MUSIC21_AVAILABLE:
        return {
            "bass": bass_pitch,
            "figures": figures,
            "warning": "music21 not available, using basic realization",
            "intervals": intervals,
        }

    try:
        bass = music21.pitch.Pitch(bass_pitch)  # type: ignore[union-attr]
        pitches = []

        for interval in intervals:
            p = bass.transpose(interval)
            pitches.append(p.nameWithOctave)

        return {
            "bass": bass_pitch,
            "figures": figures if figures else "5/3 (root position)",
            "pitches": pitches,
            "key": key_str,
        }

    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Cadence Suggestion
# =============================================================================

# Cadence types and their chord progressions
CADENCE_TYPES = {
    "authentic": {
        "chords": ["V", "I"],
        "description": "Perfect Authentic Cadence - strongest resolution",
        "use_case": "End of phrases and pieces",
    },
    "half": {
        "chords": ["I", "V"],
        "description": "Half Cadence - incomplete, questioning",
        "use_case": "End of antecedent phrases",
    },
    "plagal": {
        "chords": ["IV", "I"],
        "description": "Plagal Cadence (Amen cadence)",
        "use_case": "After authentic cadence, hymns",
    },
    "deceptive": {
        "chords": ["V", "vi"],
        "description": "Deceptive Cadence - unexpected resolution",
        "use_case": "Extending phrases, avoiding closure",
    },
    "phrygian": {
        "chords": ["iv6", "V"],
        "description": "Phrygian Half Cadence (in minor)",
        "use_case": "Baroque slow movements, minor keys",
    },
}


def suggest_cadence(
    current_chord: str,
    key_str: str = "C major",
    phrase_position: str = "end",
) -> dict[str, Any]:
    """
    Suggest appropriate cadence types based on context.

    Args:
        current_chord: Current chord (e.g., "V", "IV", "I")
        key_str: Key context (e.g., "C major", "A minor")
        phrase_position: Position in phrase ("end", "middle", "beginning")

    Returns:
        Cadence suggestions with explanations
    """
    is_minor = "minor" in key_str.lower()
    suggestions = []

    # Determine which cadences are appropriate
    if phrase_position == "end":
        # For phrase endings, suggest authentic or deceptive
        if current_chord.upper() in ["V", "V7", "VIIO"]:
            suggestions.append(
                {
                    "type": "authentic",
                    "next_chord": "i" if is_minor else "I",
                    **CADENCE_TYPES["authentic"],
                }
            )
            suggestions.append(
                {
                    "type": "deceptive",
                    "next_chord": "VI" if is_minor else "vi",
                    **CADENCE_TYPES["deceptive"],
                }
            )
        elif current_chord.upper() in ["IV", "II"]:
            suggestions.append(
                {
                    "type": "half",
                    "next_chord": "V",
                    **CADENCE_TYPES["half"],
                }
            )
            suggestions.append(
                {
                    "type": "plagal",
                    "next_chord": "i" if is_minor else "I",
                    **CADENCE_TYPES["plagal"],
                }
            )
        elif current_chord.upper() in ["I", "I6"]:
            suggestions.append(
                {
                    "type": "half",
                    "next_chord": "V",
                    **CADENCE_TYPES["half"],
                }
            )
    elif phrase_position == "middle":
        # For middle of phrase, half cadence is common
        suggestions.append(
            {
                "type": "half",
                "next_chord": "V",
                **CADENCE_TYPES["half"],
            }
        )
        if is_minor:
            suggestions.append(
                {
                    "type": "phrygian",
                    "next_chord": "V",
                    **CADENCE_TYPES["phrygian"],
                }
            )

    if not suggestions:
        # Default suggestions
        suggestions = [
            {"type": "authentic", "next_chord": "V -> I", **CADENCE_TYPES["authentic"]},
            {"type": "half", "next_chord": "-> V", **CADENCE_TYPES["half"]},
        ]

    return {
        "current_chord": current_chord,
        "key": key_str,
        "phrase_position": phrase_position,
        "suggestions": suggestions,
    }


# =============================================================================
# Doubling Suggestions (Orchestration)
# =============================================================================

# Instrument family compatibility for doubling
DOUBLING_COMPATIBILITY = {
    "flute": ["violin", "oboe", "clarinet", "piccolo"],
    "oboe": ["flute", "clarinet", "violin"],
    "clarinet": ["flute", "oboe", "viola", "cello"],
    "bassoon": ["cello", "double_bass", "horn", "trombone"],
    "horn": ["bassoon", "trombone", "cello", "viola"],
    "trumpet": ["oboe", "violin", "horn"],
    "trombone": ["horn", "bassoon", "tuba", "cello"],
    "tuba": ["double_bass", "bassoon", "trombone"],
    "violin": ["flute", "oboe", "trumpet", "viola"],
    "viola": ["clarinet", "horn", "cello", "violin"],
    "cello": ["bassoon", "horn", "viola", "clarinet"],
    "double_bass": ["tuba", "bassoon", "cello"],
}

# Doubling purposes and recommendations
DOUBLING_PURPOSES = {
    "reinforcement": {
        "description": "Strengthen the line at same pitch",
        "interval": "unison",
        "effect": "Fuller, louder sound",
    },
    "octave_above": {
        "description": "Add brightness and clarity",
        "interval": "octave up",
        "effect": "Brighter, more penetrating",
    },
    "octave_below": {
        "description": "Add weight and foundation",
        "interval": "octave down",
        "effect": "Deeper, more grounded",
    },
    "color": {
        "description": "Add timbral variety",
        "interval": "unison",
        "effect": "Blended, unique color",
    },
}


def suggest_doubling(
    instrument: str,
    purpose: str = "reinforcement",
    register: str = "middle",
) -> dict[str, Any]:
    """
    Suggest instruments for doubling a given instrument.

    Args:
        instrument: Primary instrument to double
        purpose: Purpose of doubling (reinforcement, octave_above, octave_below, color)
        register: Register of the passage (low, middle, high)

    Returns:
        Doubling suggestions with rationale
    """
    instrument_key = instrument.lower().replace(" ", "_").replace("-", "_")

    # Get compatible instruments
    compatible = DOUBLING_COMPATIBILITY.get(instrument_key, [])

    if not compatible:
        # Try partial match
        for inst_key in DOUBLING_COMPATIBILITY:
            if inst_key in instrument_key or instrument_key in inst_key:
                compatible = DOUBLING_COMPATIBILITY[inst_key]
                break

    suggestions = []
    purpose_info = DOUBLING_PURPOSES.get(purpose, DOUBLING_PURPOSES["reinforcement"])

    for inst in compatible[:4]:  # Limit to top 4
        suggestion = {
            "instrument": inst.replace("_", " ").title(),
            "purpose": purpose,
            "interval": purpose_info["interval"],
            "effect": purpose_info["effect"],
        }

        # Add register-specific notes
        if register == "high" and inst in ["flute", "piccolo", "violin"]:
            suggestion["notes"] = "Excellent choice for high register"
        elif register == "low" and inst in ["bassoon", "cello", "tuba", "double_bass"]:
            suggestion["notes"] = "Strong foundation in low register"
        elif register == "middle":
            suggestion["notes"] = "Good blend in middle register"

        suggestions.append(suggestion)

    return {
        "primary_instrument": instrument,
        "purpose": purpose_info["description"],
        "register": register,
        "suggestions": suggestions,
        "general_tips": [
            "Doubling at unison thickens the sound",
            "Octave doubling adds clarity and depth",
            "Avoid doubling instruments with very different timbres unless for effect",
            "Consider dynamic balance - winds may need different dynamics than strings",
        ],
    }


# =============================================================================
# Dissonance Detection
# =============================================================================

# Consonant and dissonant intervals
CONSONANT_INTERVALS = {0, 3, 4, 7, 8, 9, 12}  # unison, m3, M3, P5, m6, M6, octave
PERFECT_CONSONANCES = {0, 7, 12}  # unison, P5, octave
IMPERFECT_CONSONANCES = {3, 4, 8, 9}  # thirds and sixths
DISSONANT_INTERVALS = {1, 2, 5, 6, 10, 11}  # m2, M2, P4, tritone, m7, M7

INTERVAL_NAMES_SEMITONES = {
    0: "unison",
    1: "minor 2nd",
    2: "major 2nd",
    3: "minor 3rd",
    4: "major 3rd",
    5: "perfect 4th",
    6: "tritone",
    7: "perfect 5th",
    8: "minor 6th",
    9: "major 6th",
    10: "minor 7th",
    11: "major 7th",
    12: "octave",
}


def find_dissonances(
    pitches: list[str],
    context: str = "counterpoint",
) -> dict[str, Any]:
    """
    Find dissonant intervals in a collection of pitches.

    Args:
        pitches: List of pitches sounding together (e.g., ["C4", "E4", "G4", "B4"])
        context: Context for analysis ("counterpoint", "harmony", "any")

    Returns:
        List of dissonances found with explanations
    """
    if len(pitches) < 2:
        return {
            "pitches": pitches,
            "dissonances": [],
            "message": "Need at least 2 pitches to find intervals",
        }

    def pitch_to_midi(pitch: str) -> int:
        """Convert pitch name to MIDI number."""
        note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        name = pitch[0].upper()
        octave = int(pitch[-1])
        accidental = 0
        if len(pitch) > 2:
            if "#" in pitch:
                accidental = pitch.count("#")
            elif "b" in pitch:
                accidental = -pitch.count("b")
        return (octave + 1) * 12 + note_map[name] + accidental

    dissonances = []
    all_intervals = []

    try:
        midi_pitches = [pitch_to_midi(p) for p in pitches]

        for i in range(len(midi_pitches)):
            for j in range(i + 1, len(midi_pitches)):
                interval = abs(midi_pitches[j] - midi_pitches[i]) % 12
                interval_name = INTERVAL_NAMES_SEMITONES.get(interval, f"{interval} semitones")

                interval_info = {
                    "pitch1": pitches[i],
                    "pitch2": pitches[j],
                    "interval": interval_name,
                    "semitones": interval,
                }

                all_intervals.append(interval_info)

                if interval in DISSONANT_INTERVALS:
                    dissonance = {
                        **interval_info,
                        "type": "dissonant",
                    }

                    # Add context-specific advice
                    if context == "counterpoint":
                        if interval == 1:  # m2
                            dissonance["advice"] = "Avoid minor 2nds in strict counterpoint"
                        elif interval == 2:  # M2
                            dissonance["advice"] = "Use as passing or neighbor tone"
                        elif interval == 5:  # P4
                            dissonance["advice"] = "P4 is dissonant against bass in counterpoint"
                        elif interval == 6:  # tritone
                            dissonance["advice"] = (
                                "Resolve tritone by step (augmented resolves out, diminished in)"
                            )
                        elif interval in [10, 11]:  # 7ths
                            dissonance["advice"] = "7ths must resolve down by step"
                    elif context == "harmony":
                        if interval in [10, 11]:
                            dissonance["advice"] = "7th chord - resolve 7th down by step"
                        elif interval == 6:
                            dissonance["advice"] = "Tritone - dominant function, resolve to tonic"

                    dissonances.append(dissonance)

        # Determine consonance level
        consonance_level = "consonant"
        if len(dissonances) > 0:
            if any(d["semitones"] in [1, 6] for d in dissonances):
                consonance_level = "highly dissonant"
            else:
                consonance_level = "mildly dissonant"

        return {
            "pitches": pitches,
            "context": context,
            "all_intervals": all_intervals,
            "dissonances": dissonances,
            "consonance_level": consonance_level,
            "dissonance_count": len(dissonances),
        }

    except (ValueError, IndexError) as e:
        return {"error": f"Could not parse pitches: {e}"}


ENSEMBLE_PRESETS = {
    "string_quartet": {
        "instruments": ["violin", "violin", "viola", "cello"],
        "description": "Classic chamber ensemble for intimate expression",
        "best_for": ["chamber music", "intimate settings", "polyphonic writing"],
    },
    "wind_quintet": {
        "instruments": ["flute", "oboe", "clarinet", "horn", "bassoon"],
        "description": "Standard woodwind ensemble with horn",
        "best_for": ["colorful textures", "lyrical passages", "light character"],
    },
    "brass_quintet": {
        "instruments": ["trumpet", "trumpet", "horn", "trombone", "tuba"],
        "description": "Powerful brass ensemble",
        "best_for": ["fanfares", "ceremonial music", "strong dynamics"],
    },
    "piano_trio": {
        "instruments": ["violin", "cello", "piano"],
        "description": "Classic romantic chamber combination",
        "best_for": ["romantic repertoire", "sonata form", "virtuosic passages"],
    },
    "full_orchestra": {
        "instruments": [
            "flute",
            "flute",
            "oboe",
            "oboe",
            "clarinet",
            "clarinet",
            "bassoon",
            "bassoon",
            "horn",
            "horn",
            "horn",
            "horn",
            "trumpet",
            "trumpet",
            "trombone",
            "trombone",
            "trombone",
            "tuba",
            "timpani",
            "violin",
            "violin",
            "viola",
            "cello",
            "double_bass",
        ],
        "description": "Full symphony orchestra",
        "best_for": ["symphonic works", "large-scale pieces", "maximum dynamic range"],
    },
    "chamber_orchestra": {
        "instruments": [
            "flute",
            "oboe",
            "clarinet",
            "bassoon",
            "horn",
            "horn",
            "violin",
            "violin",
            "viola",
            "cello",
            "double_bass",
        ],
        "description": "Smaller orchestral forces",
        "best_for": ["baroque/classical style", "clearer textures", "intimate orchestral"],
    },
}


def suggest_instrumentation(
    style: str = "classical",
    size: str = "medium",
    character: str = "balanced",
) -> dict[str, Any]:
    """
    Suggest instrumental ensembles based on style and requirements.

    Args:
        style: Musical style (classical, romantic, modern, baroque, jazz)
        size: Ensemble size (solo, small, medium, large, orchestra)
        character: Character of piece (lyrical, dramatic, light, powerful, intimate)

    Returns:
        Suggested ensembles with rationale
    """
    suggestions = []

    if size == "solo":
        suggestions.append(
            {
                "ensemble": "Solo instrument",
                "instruments": ["piano"],
                "alternatives": ["violin", "cello", "guitar", "flute"],
                "rationale": "Maximum expressive freedom for a single voice",
            }
        )
    elif size == "small":
        if character in ["intimate", "lyrical"]:
            suggestions.append(
                {
                    **ENSEMBLE_PRESETS["piano_trio"],
                    "ensemble": "Piano Trio",
                    "rationale": "Warm, intimate sound ideal for lyrical expression",
                }
            )
        suggestions.append(
            {
                **ENSEMBLE_PRESETS["string_quartet"],
                "ensemble": "String Quartet",
                "rationale": "Versatile, balanced, ideal for contrapuntal writing",
            }
        )
    elif size == "medium":
        suggestions.append(
            {
                **ENSEMBLE_PRESETS["wind_quintet"],
                "ensemble": "Wind Quintet",
                "rationale": "Colorful palette with distinct timbres",
            }
        )
        if character in ["powerful", "dramatic"]:
            suggestions.append(
                {
                    **ENSEMBLE_PRESETS["brass_quintet"],
                    "ensemble": "Brass Quintet",
                    "rationale": "Strong, noble sound for dramatic passages",
                }
            )
        suggestions.append(
            {
                **ENSEMBLE_PRESETS["chamber_orchestra"],
                "ensemble": "Chamber Orchestra",
                "rationale": "Orchestral colors with chamber clarity",
            }
        )
    elif size in ["large", "orchestra"]:
        suggestions.append(
            {
                **ENSEMBLE_PRESETS["full_orchestra"],
                "ensemble": "Full Orchestra",
                "rationale": "Maximum dynamic and timbral range",
            }
        )
        suggestions.append(
            {
                **ENSEMBLE_PRESETS["chamber_orchestra"],
                "ensemble": "Chamber Orchestra",
                "rationale": "Lighter alternative with orchestral palette",
            }
        )

    style_tips = {
        "baroque": "Consider harpsichord continuo, smaller string sections",
        "classical": "Clear textures, balanced winds and strings",
        "romantic": "Larger forces, expanded brass, more doublings",
        "modern": "Extended techniques, unusual combinations welcome",
        "jazz": "Consider rhythm section (piano, bass, drums) plus horns",
    }

    return {
        "style": style,
        "size": size,
        "character": character,
        "suggestions": suggestions,
        "style_tip": style_tips.get(style, "Consider the period style conventions"),
    }


DYNAMIC_BALANCE_RATIOS = {
    "flute": {"base_dynamic": "mf", "projection": 0.7, "blend": 0.8},
    "oboe": {"base_dynamic": "mf", "projection": 0.9, "blend": 0.6},
    "clarinet": {"base_dynamic": "mp", "projection": 0.6, "blend": 0.9},
    "bassoon": {"base_dynamic": "mf", "projection": 0.7, "blend": 0.8},
    "horn": {"base_dynamic": "mf", "projection": 0.8, "blend": 0.9},
    "trumpet": {"base_dynamic": "f", "projection": 1.0, "blend": 0.5},
    "trombone": {"base_dynamic": "f", "projection": 1.0, "blend": 0.6},
    "tuba": {"base_dynamic": "f", "projection": 0.9, "blend": 0.7},
    "violin": {"base_dynamic": "mf", "projection": 0.7, "blend": 1.0},
    "viola": {"base_dynamic": "mf", "projection": 0.5, "blend": 1.0},
    "cello": {"base_dynamic": "mf", "projection": 0.6, "blend": 1.0},
    "double_bass": {"base_dynamic": "mf", "projection": 0.5, "blend": 0.9},
    "piano": {"base_dynamic": "mf", "projection": 0.8, "blend": 0.7},
    "timpani": {"base_dynamic": "f", "projection": 1.0, "blend": 0.5},
}


def balance_dynamics(
    instruments: list[str],
    target_dynamic: str = "mf",
    melody_instrument: str | None = None,
) -> dict[str, Any]:
    """
    Suggest dynamic adjustments for ensemble balance.

    Args:
        instruments: List of instruments in the ensemble
        target_dynamic: Target overall dynamic level (pp, p, mp, mf, f, ff)
        melody_instrument: Instrument carrying the melody (should project)

    Returns:
        Dynamic suggestions for each instrument
    """
    dynamic_levels = {"pp": 1, "p": 2, "mp": 3, "mf": 4, "f": 5, "ff": 6}
    dynamic_names = {1: "pp", 2: "p", 3: "mp", 4: "mf", 5: "f", 6: "ff"}

    target_level = dynamic_levels.get(target_dynamic, 4)
    suggestions = []

    for inst in instruments:
        inst_key = inst.lower().replace(" ", "_").replace("-", "_")
        info = DYNAMIC_BALANCE_RATIOS.get(inst_key)

        if not info:
            for key in DYNAMIC_BALANCE_RATIOS:
                if key in inst_key or inst_key in key:
                    info = DYNAMIC_BALANCE_RATIOS[key]
                    break

        if not info:
            info = {"base_dynamic": "mf", "projection": 0.7, "blend": 0.8}

        adjustment = 0

        if melody_instrument and inst.lower() == melody_instrument.lower():
            adjustment = 1
            role = "melody"
        elif info["projection"] > 0.8:
            adjustment = -1
            role = "accompaniment (reduce for balance)"
        else:
            role = "accompaniment"

        suggested_level = max(1, min(6, target_level + adjustment))
        suggested_dynamic = dynamic_names[suggested_level]

        suggestions.append(
            {
                "instrument": inst,
                "suggested_dynamic": suggested_dynamic,
                "role": role,
                "projection": info["projection"],
                "notes": f"{'Increase' if adjustment > 0 else 'Reduce' if adjustment < 0 else 'Match'} relative to target",
            }
        )

    return {
        "target_dynamic": target_dynamic,
        "melody_instrument": melody_instrument,
        "suggestions": suggestions,
        "tips": [
            "Brass naturally projects more than strings",
            "Woodwinds blend well but can be covered",
            "Double bass provides foundation, rarely needs prominence",
            "Melody should be 1 dynamic level above accompaniment",
        ],
    }


BEAMING_RULES = {
    "simple_duple": {
        "time_signatures": ["2/4", "4/4"],
        "beat_grouping": [2, 2],
        "beam_across_beat": False,
    },
    "simple_triple": {
        "time_signatures": ["3/4"],
        "beat_grouping": [3],
        "beam_across_beat": False,
    },
    "compound_duple": {
        "time_signatures": ["6/8"],
        "beat_grouping": [3, 3],
        "beam_across_beat": True,
    },
    "compound_triple": {
        "time_signatures": ["9/8"],
        "beat_grouping": [3, 3, 3],
        "beam_across_beat": True,
    },
    "compound_quadruple": {
        "time_signatures": ["12/8"],
        "beat_grouping": [3, 3, 3, 3],
        "beam_across_beat": True,
    },
}


def check_beaming(
    time_signature: str,
    note_values: list[str],
) -> dict[str, Any]:
    """
    Check if beaming follows standard notation rules.

    Args:
        time_signature: Time signature (e.g., "4/4", "6/8")
        note_values: List of note values in a bar (e.g., ["8th", "8th", "8th", "8th"])

    Returns:
        Beaming analysis with suggestions
    """
    rule_type = None
    for rtype, info in BEAMING_RULES.items():
        if time_signature in info["time_signatures"]:
            rule_type = rtype
            break

    if not rule_type:
        return {
            "time_signature": time_signature,
            "status": "unknown",
            "message": f"No standard beaming rules defined for {time_signature}",
        }

    rule = BEAMING_RULES[rule_type]
    beat_grouping = rule["beat_grouping"]

    eighth_count = 0
    for nv in note_values:
        if "8th" in nv or "eighth" in nv.lower():
            eighth_count += 1
        elif "16th" in nv or "sixteenth" in nv.lower():
            eighth_count += 0.5

    suggestions = []
    if rule_type.startswith("compound"):
        suggestions.append("Beam in groups of 3 eighth notes")
        suggestions.append("Do not break beams within the dotted-quarter beat")
    else:
        suggestions.append("Beam within each beat, not across beats")
        suggestions.append("Break beams at beat boundaries")

    return {
        "time_signature": time_signature,
        "meter_type": rule_type,
        "beat_grouping": beat_grouping,
        "beam_across_beat": rule["beam_across_beat"],
        "suggestions": suggestions,
        "general_rules": [
            "Beams should clarify the beat structure",
            "Vocal music often uses separate flags instead of beams",
            "Cross-beat beaming is acceptable for rhythmic effect",
        ],
    }


def check_spacing(
    note_count: int,
    bar_width_mm: float = 40.0,
    shortest_note: str = "quarter",
) -> dict[str, Any]:
    """
    Check if note spacing is appropriate for readability.

    Args:
        note_count: Number of notes in the bar
        bar_width_mm: Width of the bar in millimeters
        shortest_note: Shortest note value in the bar

    Returns:
        Spacing analysis with recommendations
    """
    min_spacing = {
        "whole": 30.0,
        "half": 15.0,
        "quarter": 8.0,
        "eighth": 5.0,
        "16th": 3.0,
        "32nd": 2.0,
    }

    min_space = min_spacing.get(shortest_note, 5.0)
    actual_spacing = bar_width_mm / max(note_count, 1)

    if actual_spacing < min_space * 0.7:
        status = "too_crowded"
        recommendation = "Increase bar width or use system breaks"
    elif actual_spacing > min_space * 2.5:
        status = "too_sparse"
        recommendation = "Reduce bar width or add more bars per system"
    else:
        status = "good"
        recommendation = "Spacing is appropriate"

    return {
        "note_count": note_count,
        "bar_width_mm": bar_width_mm,
        "actual_spacing_mm": round(actual_spacing, 1),
        "minimum_recommended_mm": min_space,
        "status": status,
        "recommendation": recommendation,
        "tips": [
            "Consistent spacing aids sight-reading",
            "Proportional spacing: longer notes get more space",
            "Complex passages may need wider bars",
        ],
    }
