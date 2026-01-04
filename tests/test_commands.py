"""
Tests for Dorico command builders.
"""

from dorico_mcp.commands import (
    add_dynamic,
    add_key_signature,
    add_tempo,
    add_time_signature,
    file_new,
    file_open,
    file_save,
    navigate_go_to_bar,
    note_input_pitch,
    note_input_set_duration,
    transpose_chromatic,
)
from dorico_mcp.models import Dynamic, KeyMode, NoteDuration


class TestFileCommands:
    """Tests for file-related commands."""

    def test_file_new(self):
        assert file_new() == "File.New"

    def test_file_save(self):
        assert file_save() == "File.Save"

    def test_file_open(self):
        result = file_open("/path/to/score.dorico")
        assert result == "File.Open?Path=/path/to/score.dorico"


class TestNoteInputCommands:
    """Tests for note input commands."""

    def test_note_input_pitch_simple(self):
        result = note_input_pitch("C4")
        assert "NoteInput.Pitch" in result
        assert "Note=C" in result
        assert "Octave=4" in result

    def test_note_input_pitch_sharp(self):
        result = note_input_pitch("F#5")
        assert "Note=F" in result
        assert "Octave=5" in result
        assert "Accidental=Sharp" in result

    def test_note_input_pitch_flat(self):
        result = note_input_pitch("Bb3")
        assert "Note=B" in result
        assert "Octave=3" in result
        assert "Accidental=Flat" in result

    def test_note_input_set_duration_quarter(self):
        result = note_input_set_duration(NoteDuration.QUARTER)
        assert result == "NoteInput.SetDuration?Duration=4"

    def test_note_input_set_duration_half(self):
        result = note_input_set_duration(NoteDuration.HALF)
        assert result == "NoteInput.SetDuration?Duration=2"

    def test_note_input_set_duration_eighth(self):
        result = note_input_set_duration(NoteDuration.EIGHTH)
        assert result == "NoteInput.SetDuration?Duration=8"


class TestNotationCommands:
    """Tests for notation commands."""

    def test_add_key_signature_c_major(self):
        result = add_key_signature("C", KeyMode.MAJOR)
        assert "Edit.AddKeySignature" in result
        assert "Tonic=C" in result
        assert "Mode=Major" in result

    def test_add_key_signature_g_major(self):
        result = add_key_signature("G", KeyMode.MAJOR)
        assert "Tonic=G" in result
        assert "Mode=Major" in result

    def test_add_key_signature_a_minor(self):
        result = add_key_signature("A", KeyMode.MINOR)
        assert "Tonic=A" in result
        assert "Mode=Minor" in result

    def test_add_key_signature_sharp(self):
        result = add_key_signature("F#", KeyMode.MINOR)
        assert "Tonic=F" in result
        assert "Accidental=Sharp" in result
        assert "Mode=Minor" in result

    def test_add_key_signature_flat(self):
        result = add_key_signature("Bb", KeyMode.MAJOR)
        assert "Tonic=B" in result
        assert "Accidental=Flat" in result
        assert "Mode=Major" in result

    def test_add_time_signature(self):
        result = add_time_signature(4, 4)
        assert result == "Edit.AddTimeSignature?Numerator=4&Denominator=4"

    def test_add_time_signature_waltz(self):
        result = add_time_signature(3, 4)
        assert result == "Edit.AddTimeSignature?Numerator=3&Denominator=4"

    def test_add_time_signature_compound(self):
        result = add_time_signature(6, 8)
        assert result == "Edit.AddTimeSignature?Numerator=6&Denominator=8"

    def test_add_dynamic_piano(self):
        result = add_dynamic(Dynamic.P)
        assert result == "Edit.AddDynamic?Dynamic=p"

    def test_add_dynamic_forte(self):
        result = add_dynamic(Dynamic.F)
        assert result == "Edit.AddDynamic?Dynamic=f"

    def test_add_dynamic_sfz(self):
        result = add_dynamic(Dynamic.SFZ)
        assert result == "Edit.AddDynamic?Dynamic=sfz"

    def test_add_tempo_simple(self):
        result = add_tempo(120)
        assert result == "Edit.AddTempo?BPM=120"

    def test_add_tempo_with_text(self):
        result = add_tempo(120, "Allegro")
        assert "BPM=120" in result
        assert "Text=Allegro" in result


class TestNavigationCommands:
    """Tests for navigation commands."""

    def test_navigate_go_to_bar(self):
        result = navigate_go_to_bar(10)
        assert result == "Navigate.GoToBar?Bar=10"


class TestTransposeCommands:
    """Tests for transpose commands."""

    def test_transpose_chromatic_up(self):
        result = transpose_chromatic(5)
        assert result == "Edit.TransposeChromatic?Semitones=5"

    def test_transpose_chromatic_down(self):
        result = transpose_chromatic(-7)
        assert result == "Edit.TransposeChromatic?Semitones=-7"

    def test_transpose_chromatic_octave(self):
        result = transpose_chromatic(12)
        assert result == "Edit.TransposeChromatic?Semitones=12"
