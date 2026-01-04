"""
End-to-end tests for Dorico MCP Server.

These tests use a mock Dorico server to verify the complete flow
from MCP tool invocation to Dorico command execution.
"""

import asyncio
import pytest
import pytest_asyncio

from tests.mock_dorico import MockDoricoServer
from dorico_mcp.client import DoricoClient
from dorico_mcp.models import KeyMode, NoteDuration
from dorico_mcp import commands as cmd


# Test configuration
MOCK_PORT = 4599  # Use non-standard port to avoid conflicts


@pytest_asyncio.fixture
async def mock_server():
    """Fixture that provides a running mock Dorico server."""
    server = MockDoricoServer(port=MOCK_PORT)
    await server.start()
    yield server
    await server.stop()


@pytest_asyncio.fixture
async def client(mock_server):
    """Fixture that provides a connected Dorico client."""
    client = DoricoClient(port=MOCK_PORT)
    await client.connect()
    yield client
    await client.disconnect()


class TestConnectionE2E:
    """End-to-end tests for connection handling."""

    @pytest.mark.asyncio
    async def test_connect_to_mock_server(self, mock_server):
        """Test connecting to mock Dorico server."""
        client = DoricoClient(port=MOCK_PORT)
        await client.connect()

        assert client.is_connected
        assert mock_server.get_state()["connected"]

        await client.disconnect()
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_reconnect_with_saved_token(self, mock_server):
        """Test reconnecting with saved session token."""
        # First connection
        client1 = DoricoClient(port=MOCK_PORT)
        await client1.connect()
        assert client1.is_connected
        await client1.disconnect()

        # Second connection should reuse token
        client2 = DoricoClient(port=MOCK_PORT)
        await client2.connect()
        assert client2.is_connected
        await client2.disconnect()


class TestFileOperationsE2E:
    """End-to-end tests for file operations."""

    @pytest.mark.asyncio
    async def test_create_new_score(self, client, mock_server):
        """Test creating a new score."""
        response = await client.send_command(cmd.file_new())

        assert response.success
        assert mock_server.get_state()["current_score"] is not None

    @pytest.mark.asyncio
    async def test_save_score(self, client, mock_server):
        """Test saving a score."""
        # First create a score
        await client.send_command(cmd.file_new())

        # Then save it
        response = await client.send_command(cmd.file_save())
        assert response.success

    @pytest.mark.asyncio
    async def test_save_without_score_fails(self, client, mock_server):
        """Test that saving without an open score fails."""
        # Don't create a score, just try to save
        mock_server.reset_state()
        # Need to reconnect after reset
        await client.disconnect()
        await client.connect()

        response = await client.send_command(cmd.file_save())
        assert not response.success

    @pytest.mark.asyncio
    async def test_close_score(self, client, mock_server):
        """Test closing a score."""
        await client.send_command(cmd.file_new())
        assert mock_server.get_state()["current_score"] is not None

        response = await client.send_command(cmd.file_close())
        assert response.success
        assert mock_server.get_state()["current_score"] is None


class TestNoteInputE2E:
    """End-to-end tests for note input."""

    @pytest.mark.asyncio
    async def test_enter_note_input_mode(self, client, mock_server):
        """Test entering note input mode."""
        await client.send_command(cmd.file_new())
        response = await client.send_command(cmd.note_input_start())

        assert response.success
        assert mock_server.get_state()["mode"] == "note_input"

    @pytest.mark.asyncio
    async def test_exit_note_input_mode(self, client, mock_server):
        """Test exiting note input mode."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())
        response = await client.send_command(cmd.note_input_exit())

        assert response.success
        assert mock_server.get_state()["mode"] == "write"

    @pytest.mark.asyncio
    async def test_input_single_note(self, client, mock_server):
        """Test inputting a single note."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())
        await client.send_command(cmd.note_input_set_duration(NoteDuration.QUARTER))

        response = await client.send_command(cmd.note_input_pitch("C4"))

        assert response.success
        assert response.data["pitch"] == "C4"

    @pytest.mark.asyncio
    async def test_input_sharp_note(self, client, mock_server):
        """Test inputting a sharp note."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())

        response = await client.send_command(cmd.note_input_pitch("F#5"))

        assert response.success
        # Check command was recorded correctly
        history = mock_server.get_command_history()
        pitch_cmd = [c for c in history if c["command"] == "NoteInput.Pitch"][-1]
        assert pitch_cmd["params"]["Note"] == "F"
        assert pitch_cmd["params"]["Accidental"] == "Sharp"
        assert pitch_cmd["params"]["Octave"] == "5"

    @pytest.mark.asyncio
    async def test_input_flat_note(self, client, mock_server):
        """Test inputting a flat note."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())

        response = await client.send_command(cmd.note_input_pitch("Bb3"))

        assert response.success
        history = mock_server.get_command_history()
        pitch_cmd = [c for c in history if c["command"] == "NoteInput.Pitch"][-1]
        assert pitch_cmd["params"]["Note"] == "B"
        assert pitch_cmd["params"]["Accidental"] == "Flat"

    @pytest.mark.asyncio
    async def test_input_rest(self, client, mock_server):
        """Test inputting a rest."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())

        response = await client.send_command(cmd.note_input_rest())

        assert response.success
        assert response.data["type"] == "rest"

    @pytest.mark.asyncio
    async def test_input_melody_sequence(self, client, mock_server):
        """Test inputting a sequence of notes (melody)."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())
        await client.send_command(cmd.note_input_set_duration(NoteDuration.EIGHTH))

        # Input a C major scale
        notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
        for note in notes:
            response = await client.send_command(cmd.note_input_pitch(note))
            assert response.success

        # Verify all notes were recorded
        history = mock_server.get_command_history()
        pitch_commands = [c for c in history if c["command"] == "NoteInput.Pitch"]
        assert len(pitch_commands) == 8

    @pytest.mark.asyncio
    async def test_input_chord(self, client, mock_server):
        """Test inputting a chord."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.note_input_start())
        await client.send_command(cmd.note_input_chord_mode_on())

        # Input C major chord
        for note in ["C4", "E4", "G4"]:
            response = await client.send_command(cmd.note_input_pitch(note))
            assert response.success

        await client.send_command(cmd.note_input_chord_mode_off())

        history = mock_server.get_command_history()
        assert any(c["command"] == "NoteInput.ChordModeOn" for c in history)
        assert any(c["command"] == "NoteInput.ChordModeOff" for c in history)


class TestNotationE2E:
    """End-to-end tests for notation commands."""

    @pytest.mark.asyncio
    async def test_set_key_signature_major(self, client, mock_server):
        """Test setting a major key signature."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_key_signature("G", KeyMode.MAJOR))

        assert response.success
        state = mock_server.get_state()
        # Find current score and check key
        for score in state["scores"]:
            if score["id"] == state["current_score"]:
                assert "G" in score["key_signature"]
                assert "major" in score["key_signature"].lower()

    @pytest.mark.asyncio
    async def test_set_key_signature_minor(self, client, mock_server):
        """Test setting a minor key signature."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_key_signature("A", KeyMode.MINOR))

        assert response.success

    @pytest.mark.asyncio
    async def test_set_key_signature_with_accidental(self, client, mock_server):
        """Test setting a key signature with accidental."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_key_signature("F#", KeyMode.MINOR))

        assert response.success
        history = mock_server.get_command_history()
        key_cmd = [c for c in history if c["command"] == "Edit.AddKeySignature"][-1]
        assert key_cmd["params"]["Tonic"] == "F"
        assert key_cmd["params"]["Accidental"] == "Sharp"

    @pytest.mark.asyncio
    async def test_set_time_signature_common(self, client, mock_server):
        """Test setting common time (4/4)."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_time_signature(4, 4))

        assert response.success
        assert response.data["timeSignature"] == "4/4"

    @pytest.mark.asyncio
    async def test_set_time_signature_waltz(self, client, mock_server):
        """Test setting waltz time (3/4)."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_time_signature(3, 4))

        assert response.success
        assert response.data["timeSignature"] == "3/4"

    @pytest.mark.asyncio
    async def test_set_time_signature_compound(self, client, mock_server):
        """Test setting compound time (6/8)."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_time_signature(6, 8))

        assert response.success
        assert response.data["timeSignature"] == "6/8"

    @pytest.mark.asyncio
    async def test_add_dynamics(self, client, mock_server):
        """Test adding dynamics."""
        await client.send_command(cmd.file_new())

        from dorico_mcp.models import Dynamic

        for dyn in [Dynamic.PP, Dynamic.P, Dynamic.MP, Dynamic.MF, Dynamic.F, Dynamic.FF]:
            response = await client.send_command(cmd.add_dynamic(dyn))
            assert response.success

    @pytest.mark.asyncio
    async def test_add_tempo(self, client, mock_server):
        """Test adding tempo marking."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_tempo(120, "Allegro"))

        assert response.success
        assert response.data["bpm"] == "120"
        assert response.data["text"] == "Allegro"


class TestNavigationE2E:
    """End-to-end tests for navigation commands."""

    @pytest.mark.asyncio
    async def test_navigate_to_bar(self, client, mock_server):
        """Test navigating to a specific bar."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.navigate_go_to_bar(10))

        assert response.success
        assert mock_server.get_state()["caret_position"]["bar"] == 10

    @pytest.mark.asyncio
    async def test_navigate_next_bar(self, client, mock_server):
        """Test navigating to next bar."""
        await client.send_command(cmd.file_new())
        initial_bar = mock_server.get_state()["caret_position"]["bar"]

        response = await client.send_command(cmd.navigate_next_bar())

        assert response.success
        assert mock_server.get_state()["caret_position"]["bar"] == initial_bar + 1

    @pytest.mark.asyncio
    async def test_navigate_previous_bar(self, client, mock_server):
        """Test navigating to previous bar."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.navigate_go_to_bar(5))

        response = await client.send_command(cmd.navigate_previous_bar())

        assert response.success
        assert mock_server.get_state()["caret_position"]["bar"] == 4

    @pytest.mark.asyncio
    async def test_navigate_start(self, client, mock_server):
        """Test navigating to start."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.navigate_go_to_bar(20))

        response = await client.send_command(cmd.navigate_start())

        assert response.success
        assert mock_server.get_state()["caret_position"]["bar"] == 1


class TestInstrumentsE2E:
    """End-to-end tests for instrument operations."""

    @pytest.mark.asyncio
    async def test_add_instrument(self, client, mock_server):
        """Test adding an instrument."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.add_instrument("Violin"))

        assert response.success
        assert "Violin" in mock_server.get_state()["instruments"]

    @pytest.mark.asyncio
    async def test_add_multiple_instruments(self, client, mock_server):
        """Test adding multiple instruments."""
        await client.send_command(cmd.file_new())

        instruments = ["Violin", "Viola", "Cello", "Double Bass"]
        for inst in instruments:
            response = await client.send_command(cmd.add_instrument(inst))
            assert response.success

        state = mock_server.get_state()
        for inst in instruments:
            assert inst in state["instruments"]

    @pytest.mark.asyncio
    async def test_remove_instrument(self, client, mock_server):
        """Test removing an instrument."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.add_instrument("Piano"))

        response = await client.send_command(cmd.remove_instrument("Piano"))

        assert response.success
        assert "Piano" not in mock_server.get_state()["instruments"]


class TestPlaybackE2E:
    """End-to-end tests for playback commands."""

    @pytest.mark.asyncio
    async def test_playback_play(self, client, mock_server):
        """Test starting playback."""
        await client.send_command(cmd.file_new())

        response = await client.send_command(cmd.playback_play())

        assert response.success
        assert mock_server.get_state()["playback_state"] == "playing"

    @pytest.mark.asyncio
    async def test_playback_stop(self, client, mock_server):
        """Test stopping playback."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.playback_play())

        response = await client.send_command(cmd.playback_stop())

        assert response.success
        assert mock_server.get_state()["playback_state"] == "stopped"

    @pytest.mark.asyncio
    async def test_playback_rewind(self, client, mock_server):
        """Test rewinding."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.navigate_go_to_bar(10))

        response = await client.send_command(cmd.playback_rewind())

        assert response.success
        assert mock_server.get_state()["caret_position"]["bar"] == 1


class TestStatusE2E:
    """End-to-end tests for status queries."""

    @pytest.mark.asyncio
    async def test_get_status(self, client, mock_server):
        """Test getting application status."""
        await client.send_command(cmd.file_new())

        status = await client.get_status()

        assert status is not None
        assert "version" in status
        assert status["connected"]

    @pytest.mark.asyncio
    async def test_get_commands(self, client, mock_server):
        """Test getting available commands."""
        commands = await client.get_commands()

        assert isinstance(commands, list)
        assert len(commands) > 0
        assert "File.New" in commands
        assert "NoteInput.Pitch" in commands


class TestCompleteWorkflowE2E:
    """End-to-end tests for complete composition workflows."""

    @pytest.mark.asyncio
    async def test_create_simple_score_workflow(self, client, mock_server):
        """Test creating a complete simple score."""
        # 1. Create new score
        await client.send_command(cmd.file_new())

        # 2. Add instruments
        await client.send_command(cmd.add_instrument("Piano"))

        # 3. Set key and time signature
        await client.send_command(cmd.add_key_signature("G", KeyMode.MAJOR))
        await client.send_command(cmd.add_time_signature(4, 4))

        # 4. Add tempo
        await client.send_command(cmd.add_tempo(120, "Moderato"))

        # 5. Enter note input and add some notes
        await client.send_command(cmd.note_input_start())
        await client.send_command(cmd.note_input_set_duration(NoteDuration.QUARTER))

        for note in ["G4", "A4", "B4", "C5"]:
            await client.send_command(cmd.note_input_pitch(note))

        await client.send_command(cmd.note_input_exit())

        # 6. Verify state
        state = mock_server.get_state()
        assert "Piano" in state["instruments"]
        assert state["current_score"] is not None

        history = mock_server.get_command_history()
        assert len(history) > 10  # Should have many commands

    @pytest.mark.asyncio
    async def test_string_quartet_setup_workflow(self, client, mock_server):
        """Test setting up a string quartet score."""
        # Create score
        await client.send_command(cmd.file_new())

        # Add string quartet instruments
        quartet = ["Violin", "Violin", "Viola", "Cello"]
        for inst in quartet:
            response = await client.send_command(cmd.add_instrument(inst))
            assert response.success

        # Set key and time
        await client.send_command(cmd.add_key_signature("D", KeyMode.MAJOR))
        await client.send_command(cmd.add_time_signature(3, 4))
        await client.send_command(cmd.add_tempo(108, "Andante"))

        # Verify
        state = mock_server.get_state()
        assert len(state["instruments"]) == 4

    @pytest.mark.asyncio
    async def test_chord_progression_workflow(self, client, mock_server):
        """Test inputting a chord progression."""
        await client.send_command(cmd.file_new())
        await client.send_command(cmd.add_instrument("Piano"))
        await client.send_command(cmd.note_input_start())
        await client.send_command(cmd.note_input_set_duration(NoteDuration.WHOLE))

        # I-IV-V-I progression in C major
        chords = [
            ["C4", "E4", "G4"],  # C major
            ["F4", "A4", "C5"],  # F major
            ["G4", "B4", "D5"],  # G major
            ["C4", "E4", "G4"],  # C major
        ]

        for chord_notes in chords:
            await client.send_command(cmd.note_input_chord_mode_on())
            for note in chord_notes:
                await client.send_command(cmd.note_input_pitch(note))
            await client.send_command(cmd.note_input_chord_mode_off())

        # Verify
        history = mock_server.get_command_history()
        pitch_commands = [c for c in history if c["command"] == "NoteInput.Pitch"]
        assert len(pitch_commands) == 12  # 4 chords * 3 notes
