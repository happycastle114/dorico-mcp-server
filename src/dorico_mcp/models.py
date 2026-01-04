"""
Pydantic models for Dorico MCP Server.

These models define the data structures used throughout the server,
ensuring type safety and validation.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Enums for Type Safety
# =============================================================================


class ConnectionState(str, Enum):
    """Dorico connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AWAITING_APPROVAL = "awaiting_approval"
    CONNECTED = "connected"
    ERROR = "error"


class NoteDuration(str, Enum):
    """Standard note duration values."""

    WHOLE = "whole"  # 1
    HALF = "half"  # 2
    QUARTER = "quarter"  # 4
    EIGHTH = "eighth"  # 8
    SIXTEENTH = "sixteenth"  # 16
    THIRTY_SECOND = "32nd"  # 32
    SIXTY_FOURTH = "64th"  # 64


class Dynamic(str, Enum):
    """Standard dynamics."""

    PPPP = "pppp"
    PPP = "ppp"
    PP = "pp"
    P = "p"
    MP = "mp"
    MF = "mf"
    F = "f"
    FF = "ff"
    FFF = "fff"
    FFFF = "ffff"
    FP = "fp"
    SF = "sf"
    SFZ = "sfz"
    FZ = "fz"
    RF = "rf"
    RFZ = "rfz"


class Articulation(str, Enum):
    """Standard articulations."""

    STACCATO = "staccato"
    STACCATISSIMO = "staccatissimo"
    TENUTO = "tenuto"
    ACCENT = "accent"
    MARCATO = "marcato"
    FERMATA = "fermata"


class Clef(str, Enum):
    """Standard clefs."""

    TREBLE = "treble"
    BASS = "bass"
    ALTO = "alto"
    TENOR = "tenor"
    PERCUSSION = "percussion"


class KeyMode(str, Enum):
    """Key signature modes."""

    MAJOR = "major"
    MINOR = "minor"


# =============================================================================
# Request/Response Models
# =============================================================================


class DoricoMessage(BaseModel):
    """Base message for Dorico communication."""

    message: str
    command: str | None = None


class DoricoCommand(BaseModel):
    """A Dorico Remote Control command."""

    name: str = Field(..., description="Command name (e.g., 'File.New')")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Command parameters")

    def to_command_string(self) -> str:
        """Convert to Dorico command string format."""
        if not self.parameters:
            return self.name
        params = "&".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.name}?{params}"


class DoricoResponse(BaseModel):
    """Response from Dorico."""

    success: bool
    message: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None


# =============================================================================
# Score Models
# =============================================================================


class Note(BaseModel):
    """Represents a musical note."""

    pitch: str = Field(..., description="Pitch name (e.g., 'C4', 'F#5', 'Bb3')")
    duration: NoteDuration = Field(default=NoteDuration.QUARTER, description="Note duration")
    velocity: int = Field(default=80, ge=1, le=127, description="MIDI velocity")
    tied: bool = Field(default=False, description="Whether note is tied to next")
    dotted: bool = Field(default=False, description="Whether note is dotted")

    @property
    def midi_pitch(self) -> int:
        """Convert pitch name to MIDI number."""
        # Parse pitch name (e.g., "C4" -> 60)
        note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        name = self.pitch[0].upper()
        octave = int(self.pitch[-1])
        accidental = 0
        if "#" in self.pitch or "s" in self.pitch.lower():
            accidental = 1
        elif "b" in self.pitch:
            accidental = -1
        return (octave + 1) * 12 + note_map.get(name, 0) + accidental


class Chord(BaseModel):
    """Represents a chord (multiple simultaneous notes)."""

    notes: list[Note] = Field(..., min_length=1, description="Notes in the chord")
    duration: NoteDuration = Field(default=NoteDuration.QUARTER)


class TimeSignature(BaseModel):
    """Time signature."""

    numerator: int = Field(..., ge=1, le=32, description="Beats per measure")
    denominator: int = Field(..., description="Beat unit (4=quarter, 8=eighth, etc.)")

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


class KeySignature(BaseModel):
    """Key signature."""

    root: str = Field(..., description="Root note (e.g., 'C', 'F#', 'Bb')")
    mode: KeyMode = Field(default=KeyMode.MAJOR)

    def __str__(self) -> str:
        return f"{self.root} {self.mode.value}"


class Tempo(BaseModel):
    """Tempo marking."""

    bpm: int = Field(..., ge=20, le=400, description="Beats per minute")
    text: str | None = Field(default=None, description="Tempo text (e.g., 'Allegro')")


# =============================================================================
# Instrument Models
# =============================================================================


class InstrumentRange(BaseModel):
    """Instrument pitch range."""

    lowest: str = Field(..., description="Lowest playable pitch")
    highest: str = Field(..., description="Highest playable pitch")
    comfortable_low: str | None = Field(default=None, description="Comfortable low range")
    comfortable_high: str | None = Field(default=None, description="Comfortable high range")


class Instrument(BaseModel):
    """Musical instrument definition."""

    name: str = Field(..., description="Instrument name")
    family: str = Field(..., description="Instrument family (woodwind, brass, strings, etc.)")
    range: InstrumentRange
    transposition: int = Field(default=0, description="Transposition in semitones (0=C)")
    clef: Clef = Field(default=Clef.TREBLE)


# =============================================================================
# Analysis Models
# =============================================================================


class ChordAnalysis(BaseModel):
    """Result of chord analysis."""

    root: str = Field(..., description="Chord root")
    quality: str = Field(..., description="Chord quality (major, minor, dim, aug, etc.)")
    roman_numeral: str | None = Field(default=None, description="Roman numeral analysis")
    function: str | None = Field(default=None, description="Harmonic function (T, S, D)")
    inversion: int = Field(default=0, ge=0, le=3, description="Inversion (0=root position)")


class VoiceLeadingIssue(BaseModel):
    """Voice leading problem detected."""

    issue_type: str = Field(
        ..., description="Type of issue (parallel_fifths, parallel_octaves, etc.)"
    )
    description: str = Field(..., description="Human-readable description")
    location: str = Field(..., description="Location in score (bar, beat)")
    severity: str = Field(default="warning", description="Severity: error, warning, info")
    voices: list[str] = Field(default_factory=list, description="Affected voices/instruments")


class RangeViolation(BaseModel):
    """Instrument range violation."""

    instrument: str
    pitch: str
    location: str
    message: str


# =============================================================================
# Tool Input/Output Models
# =============================================================================


class CreateScoreInput(BaseModel):
    """Input for create_score tool."""

    title: str = Field(default="Untitled", description="Score title")
    composer: str = Field(default="", description="Composer name")
    instruments: list[str] = Field(
        default_factory=lambda: ["Piano"],
        description="List of instrument names",
    )
    time_signature: str = Field(default="4/4", description="Time signature (e.g., '4/4', '3/4')")
    key_signature: str = Field(
        default="C major", description="Key signature (e.g., 'C major', 'G minor')"
    )
    tempo: int = Field(default=120, ge=20, le=400, description="Tempo in BPM")


class AddNotesInput(BaseModel):
    """Input for add_notes tool."""

    notes: list[str] = Field(..., description="Notes to add (e.g., ['C4', 'E4', 'G4'])")
    duration: NoteDuration = Field(default=NoteDuration.QUARTER)
    as_chord: bool = Field(default=False, description="Add notes as chord (simultaneous)")


class SetKeySignatureInput(BaseModel):
    """Input for set_key_signature tool."""

    root: str = Field(..., description="Root note (C, D, E, F, G, A, B with optional # or b)")
    mode: KeyMode = Field(default=KeyMode.MAJOR)
    bar: int | None = Field(default=None, description="Bar number (None=current position)")


class SetTimeSignatureInput(BaseModel):
    """Input for set_time_signature tool."""

    numerator: int = Field(..., ge=1, le=32)
    denominator: int = Field(..., description="2, 4, 8, 16, or 32")
    bar: int | None = Field(default=None, description="Bar number (None=current position)")


class AddDynamicsInput(BaseModel):
    """Input for add_dynamics tool."""

    dynamic: Dynamic = Field(..., description="Dynamic marking")


class TransposeInput(BaseModel):
    """Input for transpose tool."""

    semitones: int = Field(..., ge=-48, le=48, description="Semitones to transpose")
    selection_only: bool = Field(default=True, description="Transpose only selection")


class CheckRangeInput(BaseModel):
    """Input for check_instrument_range tool."""

    instrument: str = Field(..., description="Instrument name to check")


class AnalyzeHarmonyInput(BaseModel):
    """Input for analyze_harmony tool."""

    include_roman_numerals: bool = Field(default=True)
    include_functions: bool = Field(default=True)


class SuggestChordInput(BaseModel):
    """Input for suggest_chord tool."""

    context: list[str] = Field(
        default_factory=list,
        description="Previous chords for context (e.g., ['C', 'Am', 'F'])",
    )
    key: str = Field(default="C major", description="Current key")
    style: str = Field(default="common_practice", description="Style: common_practice, jazz, pop")
