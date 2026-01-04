"""
Harmony Analysis Tools.

This module provides music theory analysis and generation capabilities
using the music21 library.
"""

from typing import Any

try:
    import music21
    from music21 import chord, key, roman

    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False


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
) -> list[dict[str, str]]:
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
