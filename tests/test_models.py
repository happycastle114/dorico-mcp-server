"""
Tests for Pydantic models.
"""


from dorico_mcp.models import (
    DoricoCommand,
    KeyMode,
    KeySignature,
    Note,
    NoteDuration,
    Tempo,
    TimeSignature,
)


class TestNote:
    """Tests for Note model."""

    def test_note_creation(self):
        note = Note(pitch="C4")
        assert note.pitch == "C4"
        assert note.duration == NoteDuration.QUARTER
        assert note.velocity == 80

    def test_note_midi_pitch_c4(self):
        note = Note(pitch="C4")
        assert note.midi_pitch == 60

    def test_note_midi_pitch_a4(self):
        note = Note(pitch="A4")
        assert note.midi_pitch == 69

    def test_note_midi_pitch_c5(self):
        note = Note(pitch="C5")
        assert note.midi_pitch == 72

    def test_note_midi_pitch_sharp(self):
        note = Note(pitch="F#4")
        assert note.midi_pitch == 66

    def test_note_midi_pitch_flat(self):
        note = Note(pitch="Bb3")
        assert note.midi_pitch == 58


class TestDoricoCommand:
    """Tests for DoricoCommand model."""

    def test_simple_command(self):
        cmd = DoricoCommand(name="File.New")
        assert cmd.to_command_string() == "File.New"

    def test_command_with_one_param(self):
        cmd = DoricoCommand(name="File.Open", parameters={"Path": "/test/file.dorico"})
        assert cmd.to_command_string() == "File.Open?Path=/test/file.dorico"

    def test_command_with_multiple_params(self):
        cmd = DoricoCommand(
            name="Edit.AddKeySignature",
            parameters={"Tonic": "C", "Mode": "Major"},
        )
        result = cmd.to_command_string()
        assert "Edit.AddKeySignature?" in result
        assert "Tonic=C" in result
        assert "Mode=Major" in result


class TestTimeSignature:
    """Tests for TimeSignature model."""

    def test_time_signature_str(self):
        ts = TimeSignature(numerator=4, denominator=4)
        assert str(ts) == "4/4"

    def test_time_signature_waltz(self):
        ts = TimeSignature(numerator=3, denominator=4)
        assert str(ts) == "3/4"


class TestKeySignature:
    """Tests for KeySignature model."""

    def test_key_signature_str_major(self):
        ks = KeySignature(root="C", mode=KeyMode.MAJOR)
        assert str(ks) == "C major"

    def test_key_signature_str_minor(self):
        ks = KeySignature(root="A", mode=KeyMode.MINOR)
        assert str(ks) == "A minor"


class TestTempo:
    """Tests for Tempo model."""

    def test_tempo_bpm_range(self):
        # Should work within range
        tempo = Tempo(bpm=120)
        assert tempo.bpm == 120

        tempo = Tempo(bpm=20)
        assert tempo.bpm == 20

        tempo = Tempo(bpm=400)
        assert tempo.bpm == 400

    def test_tempo_with_text(self):
        tempo = Tempo(bpm=120, text="Allegro")
        assert tempo.text == "Allegro"
