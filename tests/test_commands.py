"""Tests for Dorico command builders."""

from dorico_mcp.commands import (
    add_dynamic,
    add_key_signature,
    add_tempo,
    add_time_signature,
    file_new,
    file_open,
    file_save,
    get_flows,
    get_layouts,
    get_note_commands,
    get_options,
    get_selection_properties,
    get_status,
    navigate_go_to_bar,
    note_input_pitch,
    note_input_set_accidental,
    note_input_set_duration,
    transpose_chromatic,
    view_engrave_mode,
    view_write_mode,
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
        assert result == "File.Open?File=/path/to/score.dorico"


class TestNoteInputCommands:
    """Tests for note input commands."""

    def test_note_input_pitch_simple(self):
        result = note_input_pitch("C4")
        assert "NoteInput.Pitch" in result
        assert "Pitch=C" in result
        assert "OctaveValue=4" in result

    def test_note_input_set_accidental(self):
        result = note_input_set_accidental("Sharp")
        assert result == "NoteInput.SetAccidental?Type=Sharp"

    def test_get_note_commands_simple(self):
        commands = get_note_commands("C4")
        assert len(commands) == 1
        assert "NoteInput.Pitch" in commands[0]

    def test_get_note_commands_sharp(self):
        commands = get_note_commands("F#5")
        assert len(commands) == 2
        assert "SetAccidental" in commands[0]
        assert "Sharp" in commands[0]
        assert "Pitch=F" in commands[1]
        assert "OctaveValue=5" in commands[1]

    def test_get_note_commands_flat(self):
        commands = get_note_commands("Bb3")
        assert len(commands) == 2
        assert "SetAccidental" in commands[0]
        assert "Flat" in commands[0]
        assert "Pitch=B" in commands[1]
        assert "OctaveValue=3" in commands[1]

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


class TestQueryCommands:

    def test_get_status(self):
        assert get_status() == "Application.Status"

    def test_get_flows(self):
        assert get_flows() == "Application.GetFlows"

    def test_get_layouts(self):
        assert get_layouts() == "Application.GetLayouts"

    def test_get_selection_properties(self):
        assert get_selection_properties() == "Edit.GetProperties"

    def test_get_options_engraving(self):
        result = get_options("engraving")
        assert result == "Application.GetEngravingOptions"

    def test_get_options_layout(self):
        result = get_options("layout", 1)
        assert "GetLayoutOptions" in result
        assert "LayoutID=1" in result

    def test_get_options_notation(self):
        result = get_options("notation", 2)
        assert "GetNotationOptions" in result
        assert "FlowID=2" in result


class TestViewCommands:

    def test_view_write_mode(self):
        result = view_write_mode()
        assert "Window.SwitchMode" in result
        assert "kWriteMode" in result

    def test_view_engrave_mode(self):
        result = view_engrave_mode()
        assert "Window.SwitchMode" in result
        assert "kEngraveMode" in result
