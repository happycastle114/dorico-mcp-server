"""
Instrument Database.

Contains information about musical instruments including ranges,
transpositions, and characteristics.
"""

from dataclasses import dataclass
from enum import Enum


class InstrumentFamily(str, Enum):
    """Instrument family classification."""

    WOODWIND = "woodwind"
    BRASS = "brass"
    STRING = "string"
    PERCUSSION = "percussion"
    KEYBOARD = "keyboard"
    VOICE = "voice"


@dataclass
class InstrumentInfo:
    """Information about a musical instrument."""

    name: str
    family: InstrumentFamily
    lowest_pitch: str  # Concert pitch
    highest_pitch: str  # Concert pitch
    comfortable_low: str
    comfortable_high: str
    transposition: int  # Semitones (0 = C instrument)
    clef: str
    description: str


# Comprehensive instrument database
INSTRUMENTS: dict[str, InstrumentInfo] = {
    # Woodwinds
    "piccolo": InstrumentInfo(
        name="Piccolo",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="D5",
        highest_pitch="C8",
        comfortable_low="G5",
        comfortable_high="G7",
        transposition=0,  # Sounds octave higher than written
        clef="treble",
        description="Highest woodwind, brilliant and piercing",
    ),
    "flute": InstrumentInfo(
        name="Flute",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="C4",
        highest_pitch="D7",
        comfortable_low="G4",
        comfortable_high="D6",
        transposition=0,
        clef="treble",
        description="Agile, clear tone, wide dynamic range",
    ),
    "oboe": InstrumentInfo(
        name="Oboe",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="Bb3",
        highest_pitch="G6",
        comfortable_low="D4",
        comfortable_high="D6",
        transposition=0,
        clef="treble",
        description="Penetrating, expressive tone",
    ),
    "clarinet": InstrumentInfo(
        name="Clarinet in Bb",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="D3",  # Concert pitch
        highest_pitch="Bb6",
        comfortable_low="G3",
        comfortable_high="C6",
        transposition=-2,  # Sounds M2 lower than written
        clef="treble",
        description="Wide range, versatile, smooth registers",
    ),
    "clarinet_a": InstrumentInfo(
        name="Clarinet in A",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="C#3",
        highest_pitch="A6",
        comfortable_low="F#3",
        comfortable_high="B5",
        transposition=-3,  # Sounds m3 lower than written
        clef="treble",
        description="Warmer than Bb clarinet, used in sharp keys",
    ),
    "bass_clarinet": InstrumentInfo(
        name="Bass Clarinet",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="Bb1",
        highest_pitch="Bb5",
        comfortable_low="Eb2",
        comfortable_high="F5",
        transposition=-14,  # Sounds M9 lower than written
        clef="treble",
        description="Deep, rich woodwind bass",
    ),
    "bassoon": InstrumentInfo(
        name="Bassoon",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="Bb1",
        highest_pitch="Eb5",
        comfortable_low="C2",
        comfortable_high="G4",
        transposition=0,
        clef="bass",
        description="Versatile bass woodwind, can be humorous or solemn",
    ),
    "contrabassoon": InstrumentInfo(
        name="Contrabassoon",
        family=InstrumentFamily.WOODWIND,
        lowest_pitch="Bb0",
        highest_pitch="Bb3",
        comfortable_low="C1",
        comfortable_high="F3",
        transposition=0,  # Sounds octave lower than written
        clef="bass",
        description="Lowest woodwind, powerful bass",
    ),
    # Brass
    "horn": InstrumentInfo(
        name="Horn in F",
        family=InstrumentFamily.BRASS,
        lowest_pitch="B1",  # Concert pitch
        highest_pitch="F5",
        comfortable_low="C3",
        comfortable_high="G5",
        transposition=-7,  # Sounds P5 lower than written
        clef="treble",
        description="Noble, warm tone, blends well",
    ),
    "trumpet": InstrumentInfo(
        name="Trumpet in Bb",
        family=InstrumentFamily.BRASS,
        lowest_pitch="E3",  # Concert pitch
        highest_pitch="Bb5",
        comfortable_low="G3",
        comfortable_high="G5",
        transposition=-2,  # Sounds M2 lower than written
        clef="treble",
        description="Bright, brilliant, heroic",
    ),
    "trumpet_c": InstrumentInfo(
        name="Trumpet in C",
        family=InstrumentFamily.BRASS,
        lowest_pitch="F#3",
        highest_pitch="C6",
        comfortable_low="A3",
        comfortable_high="A5",
        transposition=0,
        clef="treble",
        description="Brighter than Bb trumpet, orchestral standard",
    ),
    "trombone": InstrumentInfo(
        name="Trombone",
        family=InstrumentFamily.BRASS,
        lowest_pitch="E2",
        highest_pitch="Bb4",
        comfortable_low="A2",
        comfortable_high="F4",
        transposition=0,
        clef="bass",
        description="Powerful, noble, smooth legato with slide",
    ),
    "bass_trombone": InstrumentInfo(
        name="Bass Trombone",
        family=InstrumentFamily.BRASS,
        lowest_pitch="Bb0",
        highest_pitch="Bb4",
        comfortable_low="Eb1",
        comfortable_high="F4",
        transposition=0,
        clef="bass",
        description="Deep brass, anchors low brass section",
    ),
    "tuba": InstrumentInfo(
        name="Tuba",
        family=InstrumentFamily.BRASS,
        lowest_pitch="D1",
        highest_pitch="F4",
        comfortable_low="F1",
        comfortable_high="Bb3",
        transposition=0,
        clef="bass",
        description="Lowest brass, foundation of brass section",
    ),
    # Strings
    "violin": InstrumentInfo(
        name="Violin",
        family=InstrumentFamily.STRING,
        lowest_pitch="G3",
        highest_pitch="E7",
        comfortable_low="G3",
        comfortable_high="B6",
        transposition=0,
        clef="treble",
        description="Most versatile string, wide range of expression",
    ),
    "viola": InstrumentInfo(
        name="Viola",
        family=InstrumentFamily.STRING,
        lowest_pitch="C3",
        highest_pitch="E6",
        comfortable_low="C3",
        comfortable_high="C6",
        transposition=0,
        clef="alto",
        description="Warm, dark tone, inner voice of strings",
    ),
    "cello": InstrumentInfo(
        name="Cello",
        family=InstrumentFamily.STRING,
        lowest_pitch="C2",
        highest_pitch="A5",
        comfortable_low="C2",
        comfortable_high="G4",
        transposition=0,
        clef="bass",
        description="Rich, expressive, wide range",
    ),
    "double_bass": InstrumentInfo(
        name="Double Bass",
        family=InstrumentFamily.STRING,
        lowest_pitch="E1",  # With extension: C1
        highest_pitch="G4",
        comfortable_low="E1",
        comfortable_high="D3",
        transposition=0,  # Sounds octave lower than written
        clef="bass",
        description="Foundation of orchestral bass, pizzicato important",
    ),
    "harp": InstrumentInfo(
        name="Harp",
        family=InstrumentFamily.STRING,
        lowest_pitch="Cb1",
        highest_pitch="G#7",
        comfortable_low="D1",
        comfortable_high="F7",
        transposition=0,
        clef="treble",  # Uses grand staff
        description="Ethereal, arpeggios and glissandos, pedal changes",
    ),
    # Percussion
    "timpani": InstrumentInfo(
        name="Timpani",
        family=InstrumentFamily.PERCUSSION,
        lowest_pitch="D2",
        highest_pitch="C4",
        comfortable_low="F2",
        comfortable_high="A3",
        transposition=0,
        clef="bass",
        description="Tuned drums, rolls and accents, 4-5 drums typical",
    ),
    "xylophone": InstrumentInfo(
        name="Xylophone",
        family=InstrumentFamily.PERCUSSION,
        lowest_pitch="F4",
        highest_pitch="C8",
        comfortable_low="F4",
        comfortable_high="C7",
        transposition=0,  # Sounds octave higher than written
        clef="treble",
        description="Bright, penetrating, sounds octave higher",
    ),
    "marimba": InstrumentInfo(
        name="Marimba",
        family=InstrumentFamily.PERCUSSION,
        lowest_pitch="C2",  # 5-octave instrument
        highest_pitch="C7",
        comfortable_low="C2",
        comfortable_high="C7",
        transposition=0,
        clef="treble",
        description="Warm, mellow, wide range",
    ),
    "vibraphone": InstrumentInfo(
        name="Vibraphone",
        family=InstrumentFamily.PERCUSSION,
        lowest_pitch="F3",
        highest_pitch="F6",
        comfortable_low="F3",
        comfortable_high="F6",
        transposition=0,
        clef="treble",
        description="Jazz standard, motor creates vibrato",
    ),
    "glockenspiel": InstrumentInfo(
        name="Glockenspiel",
        family=InstrumentFamily.PERCUSSION,
        lowest_pitch="G5",  # Sounds 2 octaves higher
        highest_pitch="C8",
        comfortable_low="G5",
        comfortable_high="C8",
        transposition=0,
        clef="treble",
        description="Celestial, bell-like, written 2 octaves lower",
    ),
    # Keyboard
    "piano": InstrumentInfo(
        name="Piano",
        family=InstrumentFamily.KEYBOARD,
        lowest_pitch="A0",
        highest_pitch="C8",
        comfortable_low="C1",
        comfortable_high="C7",
        transposition=0,
        clef="treble",  # Uses grand staff
        description="Full range, dynamic versatility, sustain pedal",
    ),
    "celesta": InstrumentInfo(
        name="Celesta",
        family=InstrumentFamily.KEYBOARD,
        lowest_pitch="C4",  # Sounds octave higher
        highest_pitch="C8",
        comfortable_low="C4",
        comfortable_high="C7",
        transposition=0,
        clef="treble",
        description="Bell-like, magical quality, written octave lower",
    ),
    # Voice
    "soprano": InstrumentInfo(
        name="Soprano",
        family=InstrumentFamily.VOICE,
        lowest_pitch="C4",
        highest_pitch="C6",
        comfortable_low="E4",
        comfortable_high="A5",
        transposition=0,
        clef="treble",
        description="Highest female voice",
    ),
    "alto": InstrumentInfo(
        name="Alto",
        family=InstrumentFamily.VOICE,
        lowest_pitch="F3",
        highest_pitch="F5",
        comfortable_low="A3",
        comfortable_high="D5",
        transposition=0,
        clef="treble",
        description="Lower female voice, rich and warm",
    ),
    "tenor": InstrumentInfo(
        name="Tenor",
        family=InstrumentFamily.VOICE,
        lowest_pitch="C3",
        highest_pitch="C5",
        comfortable_low="E3",
        comfortable_high="A4",
        transposition=0,
        clef="treble",  # Octave lower than written
        description="High male voice",
    ),
    "bass": InstrumentInfo(
        name="Bass",
        family=InstrumentFamily.VOICE,
        lowest_pitch="E2",
        highest_pitch="E4",
        comfortable_low="A2",
        comfortable_high="D4",
        transposition=0,
        clef="bass",
        description="Lowest male voice",
    ),
}


def get_instrument(name: str) -> InstrumentInfo | None:
    """Get instrument info by name (case-insensitive)."""
    key = name.lower().replace(" ", "_").replace("-", "_")
    return INSTRUMENTS.get(key)


def check_range(instrument_name: str, pitch: str) -> dict[str, any]:
    """
    Check if a pitch is within an instrument's range.

    Args:
        instrument_name: Name of the instrument
        pitch: Pitch to check (e.g., "C4", "G#5")

    Returns:
        Dictionary with range check results
    """
    instrument = get_instrument(instrument_name)
    if not instrument:
        return {"error": f"Unknown instrument: {instrument_name}"}

    try:
        # Simple pitch comparison using MIDI numbers
        pitch_midi = _pitch_to_midi(pitch)
        low_midi = _pitch_to_midi(instrument.lowest_pitch)
        high_midi = _pitch_to_midi(instrument.highest_pitch)
        comfort_low_midi = _pitch_to_midi(instrument.comfortable_low)
        comfort_high_midi = _pitch_to_midi(instrument.comfortable_high)

        in_range = low_midi <= pitch_midi <= high_midi
        in_comfortable = comfort_low_midi <= pitch_midi <= comfort_high_midi

        result = {
            "instrument": instrument.name,
            "pitch": pitch,
            "in_range": in_range,
            "in_comfortable_range": in_comfortable,
            "full_range": f"{instrument.lowest_pitch} - {instrument.highest_pitch}",
            "comfortable_range": f"{instrument.comfortable_low} - {instrument.comfortable_high}",
        }

        if not in_range:
            if pitch_midi < low_midi:
                result["issue"] = f"Pitch is too low (below {instrument.lowest_pitch})"
            else:
                result["issue"] = f"Pitch is too high (above {instrument.highest_pitch})"
        elif not in_comfortable:
            if pitch_midi < comfort_low_midi:
                result["warning"] = "Pitch is in low extreme range"
            else:
                result["warning"] = "Pitch is in high extreme range"

        return result

    except Exception as e:
        return {"error": str(e)}


def _pitch_to_midi(pitch: str) -> int:
    """Convert pitch name to MIDI number."""
    note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

    # Parse pitch
    name = pitch[0].upper()
    base = note_map.get(name, 0)

    # Handle accidentals
    accidental = 0
    remaining = pitch[1:]
    if remaining.startswith("#") or remaining.startswith("s"):
        accidental = 1
        remaining = remaining[1:]
    elif remaining.startswith("b"):
        accidental = -1
        remaining = remaining[1:]

    # Get octave
    octave = int(remaining) if remaining else 4

    return (octave + 1) * 12 + base + accidental


def get_transposition_interval(instrument_name: str) -> dict[str, any]:
    """Get the transposition interval for an instrument."""
    instrument = get_instrument(instrument_name)
    if not instrument:
        return {"error": f"Unknown instrument: {instrument_name}"}

    semitones = instrument.transposition
    if semitones == 0:
        return {
            "instrument": instrument.name,
            "transposition": "None (C instrument)",
            "semitones": 0,
        }

    direction = "down" if semitones < 0 else "up"
    return {
        "instrument": instrument.name,
        "semitones": semitones,
        "direction": direction,
        "description": f"Sounds {abs(semitones)} semitones {direction} from written pitch",
    }
