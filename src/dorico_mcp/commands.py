"""
Dorico Command Builders.

This module provides pure functions that build Dorico Remote Control API
command strings. These are kept separate from the client for easy testing.

Command Format: "CommandName?Param1=Value1&Param2=Value2"
"""

from dorico_mcp.models import (
    Articulation,
    Clef,
    Dynamic,
    KeyMode,
    NoteDuration,
)


# =============================================================================
# File Commands
# =============================================================================


def file_new() -> str:
    """Create a new score."""
    return "File.New"


def file_open(path: str) -> str:
    """Open an existing score."""
    return f"File.Open?Path={path}"


def file_save() -> str:
    """Save the current score."""
    return "File.Save"


def file_save_as(path: str) -> str:
    """Save the current score to a new path."""
    return f"File.SaveAs?Path={path}"


def file_close() -> str:
    """Close the current score."""
    return "File.Close"


def file_export_pdf(path: str) -> str:
    """Export score as PDF."""
    return f"File.ExportPDF?Path={path}"


def file_export_musicxml(path: str) -> str:
    """Export score as MusicXML."""
    return f"File.ExportMusicXML?Path={path}"


# =============================================================================
# Edit Commands
# =============================================================================


def edit_undo() -> str:
    """Undo last action."""
    return "Edit.Undo"


def edit_redo() -> str:
    """Redo last undone action."""
    return "Edit.Redo"


def edit_copy() -> str:
    """Copy selection."""
    return "Edit.Copy"


def edit_cut() -> str:
    """Cut selection."""
    return "Edit.Cut"


def edit_paste() -> str:
    """Paste clipboard."""
    return "Edit.Paste"


def edit_delete() -> str:
    """Delete selection."""
    return "Edit.Delete"


def edit_select_all() -> str:
    """Select all."""
    return "Edit.SelectAll"


# =============================================================================
# Note Input Commands
# =============================================================================


def note_input_start() -> str:
    """Start note input mode."""
    return "NoteInput.Enter"


def note_input_exit() -> str:
    """Exit note input mode."""
    return "NoteInput.Exit"


def note_input_set_duration(duration: NoteDuration) -> str:
    """Set note input duration."""
    duration_map = {
        NoteDuration.WHOLE: "1",
        NoteDuration.HALF: "2",
        NoteDuration.QUARTER: "4",
        NoteDuration.EIGHTH: "8",
        NoteDuration.SIXTEENTH: "16",
        NoteDuration.THIRTY_SECOND: "32",
        NoteDuration.SIXTY_FOURTH: "64",
    }
    return f"NoteInput.SetDuration?Duration={duration_map[duration]}"


def note_input_pitch(pitch: str) -> str:
    """
    Input a note at current position.

    Args:
        pitch: Note name with octave (e.g., "C4", "F#5", "Bb3")
    """
    # Parse pitch to Dorico format
    # Dorico uses: C, D, E, F, G, A, B with # for sharp, b for flat
    # Octave is specified separately
    note = pitch[0].upper()
    octave = pitch[-1]

    accidental = ""
    if "#" in pitch:
        accidental = "Sharp"
    elif "b" in pitch.lower() and pitch.lower() != "b":
        accidental = "Flat"

    cmd = f"NoteInput.Pitch?Note={note}&Octave={octave}"
    if accidental:
        cmd += f"&Accidental={accidental}"

    return cmd


def note_input_rest() -> str:
    """Input a rest."""
    return "NoteInput.Rest"


def note_input_tie() -> str:
    """Toggle tie on current note."""
    return "NoteInput.Tie"


def note_input_dot() -> str:
    """Toggle dot on current note."""
    return "NoteInput.Dot"


def note_input_chord_mode_on() -> str:
    """Enable chord input mode."""
    return "NoteInput.ChordModeOn"


def note_input_chord_mode_off() -> str:
    """Disable chord input mode."""
    return "NoteInput.ChordModeOff"


# =============================================================================
# Navigation Commands
# =============================================================================


def navigate_next_bar() -> str:
    """Move to next bar."""
    return "Navigate.NextBar"


def navigate_previous_bar() -> str:
    """Move to previous bar."""
    return "Navigate.PreviousBar"


def navigate_go_to_bar(bar_number: int) -> str:
    """Go to specific bar."""
    return f"Navigate.GoToBar?Bar={bar_number}"


def navigate_start() -> str:
    """Go to start of score."""
    return "Navigate.Start"


def navigate_end() -> str:
    """Go to end of score."""
    return "Navigate.End"


# =============================================================================
# Notation Commands
# =============================================================================


def add_key_signature(root: str, mode: KeyMode) -> str:
    """
    Add key signature.

    Args:
        root: Root note (C, D, E, F, G, A, B with optional # or b)
        mode: Major or Minor
    """
    # Convert to Dorico format
    tonic = root[0].upper()
    accidental = ""
    if "#" in root:
        accidental = "Sharp"
    elif "b" in root.lower():
        accidental = "Flat"

    mode_str = "Major" if mode == KeyMode.MAJOR else "Minor"

    cmd = f"Edit.AddKeySignature?Tonic={tonic}&Mode={mode_str}"
    if accidental:
        cmd += f"&Accidental={accidental}"

    return cmd


def add_time_signature(numerator: int, denominator: int) -> str:
    """Add time signature."""
    return f"Edit.AddTimeSignature?Numerator={numerator}&Denominator={denominator}"


def add_clef(clef: Clef) -> str:
    """Add clef."""
    clef_map = {
        Clef.TREBLE: "G",
        Clef.BASS: "F",
        Clef.ALTO: "C3",
        Clef.TENOR: "C4",
        Clef.PERCUSSION: "Percussion",
    }
    return f"Edit.AddClef?Clef={clef_map[clef]}"


def add_dynamic(dynamic: Dynamic) -> str:
    """Add dynamic marking."""
    return f"Edit.AddDynamic?Dynamic={dynamic.value}"


def add_articulation(articulation: Articulation) -> str:
    """Add articulation."""
    return f"Edit.AddArticulation?Articulation={articulation.value}"


def add_slur() -> str:
    """Add slur to selection."""
    return "Edit.AddSlur"


def add_hairpin_crescendo() -> str:
    """Add crescendo hairpin."""
    return "Edit.AddHairpin?Type=Crescendo"


def add_hairpin_diminuendo() -> str:
    """Add diminuendo hairpin."""
    return "Edit.AddHairpin?Type=Diminuendo"


def add_tempo(bpm: int, text: str | None = None) -> str:
    """Add tempo marking."""
    cmd = f"Edit.AddTempo?BPM={bpm}"
    if text:
        cmd += f"&Text={text}"
    return cmd


def add_text(text: str) -> str:
    """Add text annotation."""
    return f"Edit.AddText?Text={text}"


# =============================================================================
# Transpose Commands
# =============================================================================


def transpose_up_octave() -> str:
    """Transpose selection up one octave."""
    return "Edit.TransposeUpOctave"


def transpose_down_octave() -> str:
    """Transpose selection down one octave."""
    return "Edit.TransposeDownOctave"


def transpose_up_step() -> str:
    """Transpose selection up one step."""
    return "Edit.TransposeUpStep"


def transpose_down_step() -> str:
    """Transpose selection down one step."""
    return "Edit.TransposeDownStep"


def transpose_chromatic(semitones: int) -> str:
    """Transpose chromatically by semitones."""
    return f"Edit.TransposeChromatic?Semitones={semitones}"


# =============================================================================
# Instrument Commands
# =============================================================================


def add_instrument(instrument_name: str) -> str:
    """Add instrument to score."""
    return f"Edit.AddInstrument?Name={instrument_name}"


def remove_instrument(instrument_name: str) -> str:
    """Remove instrument from score."""
    return f"Edit.RemoveInstrument?Name={instrument_name}"


# =============================================================================
# View Commands
# =============================================================================


def view_write_mode() -> str:
    """Switch to Write mode."""
    return "View.WriteMode"


def view_engrave_mode() -> str:
    """Switch to Engrave mode."""
    return "View.EngraveMode"


def view_play_mode() -> str:
    """Switch to Play mode."""
    return "View.PlayMode"


def view_print_mode() -> str:
    """Switch to Print mode."""
    return "View.PrintMode"


# =============================================================================
# Playback Commands
# =============================================================================


def playback_play() -> str:
    """Start playback."""
    return "Playback.Play"


def playback_stop() -> str:
    """Stop playback."""
    return "Playback.Stop"


def playback_rewind() -> str:
    """Rewind to start."""
    return "Playback.Rewind"
