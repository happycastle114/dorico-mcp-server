"""
Dorico MCP Server - Main Server Entry Point.

This is the FastMCP server that Claude Desktop connects to.
It exposes tools, resources, and prompts for controlling Dorico.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from dorico_mcp import commands as cmd
from dorico_mcp.client import DoricoClient, DoricoConnectionError
from dorico_mcp.models import (
    Articulation,
    Dynamic,
    KeyMode,
    NoteDuration,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_dorico_client: DoricoClient | None = None

_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL = 60.0


def _get_cached(key: str) -> Any | None:
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return value
        del _cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    _cache[key] = (value, time.time())


def _clear_cache() -> None:
    _cache.clear()


@lru_cache(maxsize=128)
def _get_instrument_info_cached(instrument: str) -> dict[str, Any]:
    from dorico_mcp.tools.instruments import get_instrument

    info = get_instrument(instrument)
    if info:
        return {
            "found": True,
            "name": info.name,
            "family": info.family.value,
            "range": f"{info.lowest_pitch} - {info.highest_pitch}",
            "comfortable_range": f"{info.comfortable_low} - {info.comfortable_high}",
            "transposition": info.transposition,
            "clef": info.clef,
        }
    return {"found": False, "error": f"Instrument '{instrument}' not found in database"}


@asynccontextmanager
async def get_client() -> AsyncIterator[DoricoClient]:
    global _dorico_client

    if _dorico_client is None:
        _dorico_client = DoricoClient()

    if not _dorico_client.is_connected:
        await _dorico_client.connect()

    yield _dorico_client


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="dorico-mcp-server",
        instructions="""Control Dorico music notation software via natural language.
Designed for composition majors (작곡 전공자) to streamline their workflow.

API LIMITATIONS (Dorico Remote Control):
- Selection-based only: Can only query/modify currently selected items
- No arbitrary score navigation: Cannot programmatically read specific bars/measures
- File.New may be disabled in some Dorico versions
- kOK response does not guarantee operation success

WORKFLOW: Always connect first with connect_to_dorico() before other operations.""",
    )

    # =========================================================================
    # TOOLS - Actions that modify Dorico
    # =========================================================================

    # -------------------------------------------------------------------------
    # Connection Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def connect_to_dorico() -> dict[str, Any]:
        """
        Connect to Dorico.

        Establishes a WebSocket connection to Dorico's Remote Control API.
        Must be called before using other Dorico tools.

        Returns:
            Connection status and Dorico information
        """
        try:
            async with get_client() as client:
                status = await client.get_status()
                return {
                    "success": True,
                    "message": "Connected to Dorico successfully",
                    "status": status,
                }
        except DoricoConnectionError as e:
            return {
                "success": False,
                "error": str(e),
                "hint": "Make sure Dorico is running and Remote Control is enabled in Preferences",
            }

    @mcp.tool()
    async def get_dorico_status() -> dict[str, Any]:
        """
        Get current Dorico status.

        Returns information about the current score, selection, and application state.
        """
        try:
            async with get_client() as client:
                status = await client.get_status()
                return {"success": True, "status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def open_score(path: str) -> dict[str, Any]:
        """
        Open an existing score file.

        Args:
            path: File path to the Dorico project file (.dorico)

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.file_open(path))
                return {
                    "success": response.success,
                    "message": f"Opened: {path}" if response.success else "Failed to open",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def create_score(
        title: str = "Untitled",
        composer: str = "",
        instruments: list[str] | None = None,
        time_signature: str = "4/4",
        key_signature: str = "C major",
        tempo_bpm: int = 120,
    ) -> dict[str, Any]:
        """
        Create a new score in Dorico.

        Creates a new score with the specified settings. This is the starting point
        for any new composition.

        Args:
            title: Score title (shown on first page)
            composer: Composer name
            instruments: List of instruments to add (e.g., ["Piano", "Violin", "Cello"])
            time_signature: Time signature (e.g., "4/4", "3/4", "6/8")
            key_signature: Key signature (e.g., "C major", "G minor", "Bb major")
            tempo_bpm: Tempo in beats per minute (20-400)

        Returns:
            Success status and score information

        Examples:
            - Simple piano piece: create_score(title="Prelude", instruments=["Piano"])
            - String quartet: create_score(instruments=["Violin", "Violin", "Viola", "Cello"])
            - Orchestra: create_score(instruments=["Flute", "Oboe", "Clarinet", "Horn", "Violin", "Viola", "Cello", "Double Bass"])
        """
        if instruments is None:
            instruments = ["Piano"]

        try:
            async with get_client() as client:
                # Create new score
                response = await client.send_command(cmd.file_new())
                if not response.success:
                    return {"success": False, "error": "Failed to create new score"}

                # Add instruments
                for instrument in instruments:
                    await client.send_command(cmd.add_instrument(instrument))

                # Parse and set time signature
                if "/" in time_signature:
                    num, denom = time_signature.split("/")
                    await client.send_command(cmd.add_time_signature(int(num), int(denom)))

                # Parse and set key signature
                parts = key_signature.lower().split()
                root = parts[0].capitalize()
                mode = KeyMode.MINOR if "minor" in key_signature.lower() else KeyMode.MAJOR
                await client.send_command(cmd.add_key_signature(root, mode))

                # Set tempo
                await client.send_command(cmd.add_tempo(tempo_bpm))

                return {
                    "success": True,
                    "message": f"Created new score: {title}",
                    "details": {
                        "title": title,
                        "composer": composer,
                        "instruments": instruments,
                        "time_signature": time_signature,
                        "key_signature": key_signature,
                        "tempo": tempo_bpm,
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def save_score(path: str | None = None) -> dict[str, Any]:
        """
        Save the current score.

        Args:
            path: File path to save to. If None, saves to current location.

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                if path:
                    response = await client.send_command(cmd.file_save_as(path))
                else:
                    response = await client.send_command(cmd.file_save())
                return {
                    "success": response.success,
                    "message": "Score saved" if response.success else "Failed to save",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def export_score(
        path: str,
        format: str = "pdf",
    ) -> dict[str, Any]:
        """
        Export the score to PDF or MusicXML.

        Args:
            path: Export file path
            format: Export format ("pdf" or "musicxml")

        Returns:
            Success status and export path
        """
        try:
            async with get_client() as client:
                if format.lower() == "pdf":
                    response = await client.send_command(cmd.file_export_pdf(path))
                elif format.lower() in ("musicxml", "xml"):
                    response = await client.send_command(cmd.file_export_musicxml(path))
                else:
                    return {"success": False, "error": f"Unknown format: {format}"}

                return {
                    "success": response.success,
                    "path": path,
                    "format": format,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Note Input Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def add_notes(
        notes: list[str],
        duration: str = "quarter",
        as_chord: bool = False,
    ) -> dict[str, Any]:
        """
        Add notes to the score at the current position.

        Args:
            notes: List of notes to add (e.g., ["C4", "E4", "G4"])
                   Format: Note name + octave, with optional # or b
                   Examples: "C4", "F#5", "Bb3", "G#4"
            duration: Note duration - one of:
                      "whole", "half", "quarter", "eighth", "sixteenth", "32nd", "64th"
            as_chord: If True, add all notes simultaneously as a chord.
                      If False, add notes sequentially.

        Returns:
            Success status and notes added

        Examples:
            - Single note: add_notes(["C4"])
            - Melody: add_notes(["C4", "D4", "E4", "F4", "G4"])
            - C major chord: add_notes(["C4", "E4", "G4"], as_chord=True)
            - Half notes: add_notes(["C4", "E4"], duration="half")
        """
        try:
            duration_enum = NoteDuration(duration.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid duration: {duration}. Use: whole, half, quarter, eighth, sixteenth, 32nd, 64th",
            }

        try:
            async with get_client() as client:
                # Enter note input mode
                await client.send_command(cmd.note_input_start())

                # Set duration
                await client.send_command(cmd.note_input_set_duration(duration_enum))

                if as_chord and len(notes) > 1:
                    # Chord mode
                    await client.send_command(cmd.note_input_chord_mode_on())
                    for note in notes:
                        await client.send_command(cmd.note_input_pitch(note))
                    await client.send_command(cmd.note_input_chord_mode_off())
                else:
                    # Sequential notes
                    for note in notes:
                        await client.send_command(cmd.note_input_pitch(note))

                return {
                    "success": True,
                    "message": f"Added {len(notes)} note(s)",
                    "notes": notes,
                    "duration": duration,
                    "as_chord": as_chord,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_rest(duration: str = "quarter") -> dict[str, Any]:
        """
        Add a rest at the current position.

        Args:
            duration: Rest duration (whole, half, quarter, eighth, sixteenth, 32nd, 64th)

        Returns:
            Success status
        """
        try:
            duration_enum = NoteDuration(duration.lower())
        except ValueError:
            return {"success": False, "error": f"Invalid duration: {duration}"}

        try:
            async with get_client() as client:
                await client.send_command(cmd.note_input_start())
                await client.send_command(cmd.note_input_set_duration(duration_enum))
                await client.send_command(cmd.note_input_rest())
                return {"success": True, "message": f"Added {duration} rest"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Notation Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def set_key_signature(
        root: str,
        mode: str = "major",
        bar: int | None = None,
    ) -> dict[str, Any]:
        """
        Set the key signature.

        Args:
            root: Root note of the key (C, D, E, F, G, A, B with optional # or b)
                  Examples: "C", "G", "F#", "Bb", "Eb"
            mode: "major" or "minor"
            bar: Bar number to insert at. None = current position.

        Returns:
            Success status

        Examples:
            - C major: set_key_signature("C", "major")
            - G major: set_key_signature("G", "major")
            - A minor: set_key_signature("A", "minor")
            - Bb major: set_key_signature("Bb", "major")
            - F# minor: set_key_signature("F#", "minor")
        """
        try:
            mode_enum = KeyMode(mode.lower())
        except ValueError:
            return {"success": False, "error": f"Invalid mode: {mode}. Use 'major' or 'minor'"}

        try:
            async with get_client() as client:
                if bar is not None:
                    await client.send_command(cmd.navigate_go_to_bar(bar))

                response = await client.send_command(cmd.add_key_signature(root, mode_enum))
                return {
                    "success": response.success,
                    "key": f"{root} {mode}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def set_time_signature(
        numerator: int,
        denominator: int,
        bar: int | None = None,
    ) -> dict[str, Any]:
        """
        Set the time signature.

        Args:
            numerator: Top number (beats per measure). Range: 1-32
            denominator: Bottom number (beat unit). Common values: 2, 4, 8, 16
            bar: Bar number to insert at. None = current position.

        Returns:
            Success status

        Examples:
            - Common time: set_time_signature(4, 4)
            - Waltz: set_time_signature(3, 4)
            - Compound duple: set_time_signature(6, 8)
            - Cut time: set_time_signature(2, 2)
        """
        if not 1 <= numerator <= 32:
            return {"success": False, "error": "Numerator must be between 1 and 32"}
        if denominator not in [1, 2, 4, 8, 16, 32]:
            return {"success": False, "error": "Denominator must be 1, 2, 4, 8, 16, or 32"}

        try:
            async with get_client() as client:
                if bar is not None:
                    await client.send_command(cmd.navigate_go_to_bar(bar))

                response = await client.send_command(cmd.add_time_signature(numerator, denominator))
                return {
                    "success": response.success,
                    "time_signature": f"{numerator}/{denominator}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_dynamics(dynamic: str) -> dict[str, Any]:
        """
        Add a dynamic marking to the selection.

        Args:
            dynamic: Dynamic marking. Options:
                     - pppp, ppp, pp, p (soft)
                     - mp, mf (medium)
                     - f, ff, fff, ffff (loud)
                     - fp, sf, sfz, fz, rf, rfz (accented)

        Returns:
            Success status

        Examples:
            - Piano: add_dynamics("p")
            - Forte: add_dynamics("f")
            - Sforzando: add_dynamics("sfz")
        """
        try:
            dynamic_enum = Dynamic(dynamic.lower())
        except ValueError:
            valid = ", ".join([d.value for d in Dynamic])
            return {"success": False, "error": f"Invalid dynamic: {dynamic}. Use: {valid}"}

        try:
            async with get_client() as client:
                response = await client.send_command(cmd.add_dynamic(dynamic_enum))
                return {
                    "success": response.success,
                    "dynamic": dynamic,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_tempo(
        bpm: int,
        text: str | None = None,
    ) -> dict[str, Any]:
        """
        Add a tempo marking.

        Args:
            bpm: Beats per minute (20-400)
            text: Optional tempo text (e.g., "Allegro", "Andante", "Presto")

        Returns:
            Success status

        Examples:
            - add_tempo(120)  # Just BPM
            - add_tempo(120, "Allegro")  # BPM with text
            - add_tempo(60, "Adagio")
        """
        if not 20 <= bpm <= 400:
            return {"success": False, "error": "BPM must be between 20 and 400"}

        try:
            async with get_client() as client:
                response = await client.send_command(cmd.add_tempo(bpm, text))
                return {
                    "success": response.success,
                    "bpm": bpm,
                    "text": text,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_articulation(articulation: str) -> dict[str, Any]:
        """
        Add an articulation to the current selection.

        Args:
            articulation: Articulation type (staccato, accent, tenuto, marcato,
                         staccatissimo, fermata)

        Returns:
            Success status
        """
        valid_articulations = [
            "staccato",
            "accent",
            "tenuto",
            "marcato",
            "staccatissimo",
            "fermata",
        ]
        if articulation.lower() not in valid_articulations:
            return {
                "success": False,
                "error": f"Unknown articulation. Use: {', '.join(valid_articulations)}",
            }

        try:
            artic_enum = Articulation(articulation.lower())
            async with get_client() as client:
                response = await client.send_command(cmd.add_articulation(artic_enum))
                return {"success": response.success, "articulation": articulation}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_text(
        text: str,
        text_type: str = "expression",
    ) -> dict[str, Any]:
        """
        Add text to the score at the current position.

        Args:
            text: Text content to add
            text_type: Type of text (expression, technique, tempo, staff)

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.add_text(text))
                return {"success": response.success, "text": text, "type": text_type}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def delete_notes() -> dict[str, Any]:
        """
        Delete the currently selected notes.

        Select the notes to delete first, then call this tool.

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.edit_delete())
                return {"success": response.success, "message": "Selection deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def remove_instrument(instrument_name: str) -> dict[str, Any]:
        """
        Remove an instrument from the score.

        Args:
            instrument_name: Name of the instrument to remove

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.remove_instrument(instrument_name))
                return {"success": response.success, "removed": instrument_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def add_slur() -> dict[str, Any]:
        """
        Add a slur to the current selection.

        Select the notes you want to slur first, then call this tool.

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.add_slur())
                return {"success": response.success, "message": "Slur added"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Transpose Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def transpose(
        semitones: int,
    ) -> dict[str, Any]:
        """
        Transpose the current selection by semitones.

        Args:
            semitones: Number of semitones to transpose.
                       Positive = up, Negative = down.
                       Examples: 12 = up one octave, -12 = down one octave,
                                 7 = up a perfect fifth, -5 = down a perfect fourth

        Returns:
            Success status and transposition amount
        """
        if not -48 <= semitones <= 48:
            return {"success": False, "error": "Semitones must be between -48 and 48"}

        try:
            async with get_client() as client:
                response = await client.send_command(cmd.transpose_chromatic(semitones))
                direction = "up" if semitones > 0 else "down"
                return {
                    "success": response.success,
                    "semitones": semitones,
                    "direction": direction,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def transpose_octave(direction: str = "up") -> dict[str, Any]:
        """
        Transpose the current selection by one octave.

        Args:
            direction: "up" or "down"

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                if direction.lower() == "up":
                    response = await client.send_command(cmd.transpose_up_octave())
                elif direction.lower() == "down":
                    response = await client.send_command(cmd.transpose_down_octave())
                else:
                    return {"success": False, "error": "Direction must be 'up' or 'down'"}

                return {
                    "success": response.success,
                    "direction": direction,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Navigation Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def go_to_bar(bar_number: int) -> dict[str, Any]:
        """
        Navigate to a specific bar in the score.

        Args:
            bar_number: Bar number to go to (1-based)

        Returns:
            Success status
        """
        if bar_number < 1:
            return {"success": False, "error": "Bar number must be at least 1"}

        try:
            async with get_client() as client:
                response = await client.send_command(cmd.navigate_go_to_bar(bar_number))
                return {
                    "success": response.success,
                    "bar": bar_number,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Instrument Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def add_instrument(instrument_name: str) -> dict[str, Any]:
        """
        Add an instrument to the score.

        Args:
            instrument_name: Name of the instrument to add.
                Common names: Piano, Violin, Viola, Cello, Double Bass,
                Flute, Oboe, Clarinet, Bassoon, Horn, Trumpet, Trombone, Tuba,
                Timpani, Harp, Voice

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.add_instrument(instrument_name))
                return {
                    "success": response.success,
                    "instrument": instrument_name,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Playback Tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    async def playback_control(action: str) -> dict[str, Any]:
        """
        Control playback.

        Args:
            action: One of "play", "stop", "rewind"

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                if action == "play":
                    response = await client.send_command(cmd.playback_play())
                elif action == "stop":
                    response = await client.send_command(cmd.playback_stop())
                elif action == "rewind":
                    response = await client.send_command(cmd.playback_rewind())
                else:
                    return {"success": False, "error": "Action must be 'play', 'stop', or 'rewind'"}

                return {"success": response.success, "action": action}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_flows() -> dict[str, Any]:
        """
        Get list of flows in the current project.

        Flows are separate musical sections within a Dorico project.

        Returns:
            List of flows with IDs and names
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_flows())
                return {"success": response.success, "flows": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_layouts() -> dict[str, Any]:
        """
        Get list of layouts in the current project.

        Layouts define how music is presented (full score, parts, etc.).

        Returns:
            List of layouts with IDs and names
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_layouts())
                return {"success": response.success, "layouts": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_selection_properties() -> dict[str, Any]:
        """
        Get properties of the current selection.

        Returns detailed information about whatever is currently selected in Dorico.
        NOTE: This is selection-based only - cannot query arbitrary score positions.

        Returns:
            Properties of current selection
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_selection_properties())
                return {"success": response.success, "properties": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_engraving_options() -> dict[str, Any]:
        """
        Get current engraving options.

        Engraving options control the visual appearance of notation.

        Returns:
            Current engraving options
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_options("engraving"))
                return {"success": response.success, "options": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_layout_options(layout_id: int) -> dict[str, Any]:
        """
        Get layout options for a specific layout.

        Args:
            layout_id: ID of the layout (get from get_layouts())

        Returns:
            Layout options for the specified layout
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_options("layout", layout_id))
                return {"success": response.success, "options": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_notation_options(flow_id: int) -> dict[str, Any]:
        """
        Get notation options for a specific flow.

        Args:
            flow_id: ID of the flow (get from get_flows())

        Returns:
            Notation options for the specified flow
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.get_options("notation", flow_id))
                return {"success": response.success, "options": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def set_engraving_options(options: dict[str, Any]) -> dict[str, Any]:
        """
        Set engraving options for the document.

        Engraving options control the visual appearance of notation elements.

        Args:
            options: Dictionary of option names and values to set

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.set_options("engraving", options))
                return {"success": response.success, "message": "Engraving options updated"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def set_layout_options(layout_id: int, options: dict[str, Any]) -> dict[str, Any]:
        """
        Set layout options for a specific layout.

        Args:
            layout_id: ID of the layout (get from get_layouts())
            options: Dictionary of option names and values to set

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.set_options("layout", options, layout_id))
                return {
                    "success": response.success,
                    "message": f"Layout {layout_id} options updated",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def set_notation_options(flow_id: int, options: dict[str, Any]) -> dict[str, Any]:
        """
        Set notation options for a specific flow.

        Args:
            flow_id: ID of the flow (get from get_flows())
            options: Dictionary of option names and values to set

        Returns:
            Success status
        """
        try:
            async with get_client() as client:
                response = await client.send_command(cmd.set_options("notation", options, flow_id))
                return {
                    "success": response.success,
                    "message": f"Flow {flow_id} notation options updated",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Harmony Tools (화성학 도구)
    # -------------------------------------------------------------------------

    @mcp.tool()
    def analyze_chord(pitches: list[str], key: str = "C major") -> dict[str, Any]:
        """
        Analyze a chord and get its Roman numeral analysis.

        Args:
            pitches: List of pitch names (e.g., ["C4", "E4", "G4"])
            key: Key for Roman numeral analysis (e.g., "C major", "A minor")

        Returns:
            Chord analysis with root, quality, and Roman numeral
        """
        from dorico_mcp.tools import analyze_chord_quality, analyze_roman_numeral

        quality = analyze_chord_quality(pitches)
        roman = analyze_roman_numeral(pitches, key)

        return {
            "pitches": pitches,
            "quality": quality,
            "roman_numeral": roman,
        }

    @mcp.tool()
    def suggest_next_chord(
        previous_chords: list[str],
        key: str = "C major",
        style: str = "classical",
    ) -> dict[str, Any]:
        """
        Suggest possible next chords based on harmonic context.

        Args:
            previous_chords: List of previous chord Roman numerals (e.g., ["I", "IV"])
            key: Current key (e.g., "C major")
            style: Style of suggestions (classical, pop, jazz)

        Returns:
            List of suggested chords with explanations
        """
        from dorico_mcp.tools import suggest_next_chord as suggest

        suggestions = suggest(previous_chords, key, style)
        return {
            "previous": previous_chords,
            "key": key,
            "suggestions": suggestions,
        }

    @mcp.tool()
    def check_voice_leading(voice1: list[str], voice2: list[str]) -> dict[str, Any]:
        """
        Check for voice leading issues between two voice parts.

        Detects parallel fifths, parallel octaves, voice crossing, etc.

        Args:
            voice1: List of pitches for first voice (e.g., ["C4", "D4", "E4"])
            voice2: List of pitches for second voice (e.g., ["G3", "A3", "B3"])

        Returns:
            List of voice leading issues found
        """
        from dorico_mcp.tools import check_voice_leading as check_vl

        issues = check_vl(voice1, voice2)
        return {
            "voice1": voice1,
            "voice2": voice2,
            "issues": issues,
            "has_errors": any(i.get("severity") == "error" for i in issues),
        }

    @mcp.tool()
    def generate_chord_progression(
        key: str = "C major",
        length: int = 4,
        style: str = "classical",
        ending: str = "authentic",
    ) -> dict[str, Any]:
        """
        Generate a chord progression.

        Args:
            key: Key for the progression (e.g., "C major", "A minor")
            length: Number of chords (default 4)
            style: Style (classical, pop, jazz)
            ending: Cadence type (authentic, half, plagal, deceptive)

        Returns:
            Generated chord progression with Roman numerals
        """
        from dorico_mcp.tools import generate_progression

        progression = generate_progression(key, length, style, ending)
        return {
            "key": key,
            "style": style,
            "ending": ending,
            "progression": progression,
        }

    # -------------------------------------------------------------------------
    # Orchestration Tools (오케스트레이션 도구)
    # -------------------------------------------------------------------------

    @mcp.tool()
    def check_instrument_range(instrument: str, pitch: str) -> dict[str, Any]:
        """
        Check if a pitch is playable on an instrument.

        Args:
            instrument: Instrument name (e.g., "violin", "flute", "clarinet")
            pitch: Pitch to check (e.g., "C4", "G3")

        Returns:
            Playability status and range information
        """
        from dorico_mcp.tools.instruments import check_range, get_instrument

        result = check_range(instrument, pitch)
        inst_info = get_instrument(instrument)

        range_str = None
        if inst_info:
            range_str = f"{inst_info.lowest_pitch} - {inst_info.highest_pitch}"

        return {
            "instrument": instrument,
            "pitch": pitch,
            "playable": result.get("in_range", False),
            "comfortable": result.get("in_comfortable_range", False),
            "range": range_str,
            "message": result.get("issue", result.get("warning", "")),
        }

    @mcp.tool()
    def get_instrument_info(instrument: str) -> dict[str, Any]:
        """
        Get detailed information about an instrument.

        Args:
            instrument: Instrument name (e.g., "violin", "horn", "clarinet")

        Returns:
            Instrument details including range, transposition, family
        """
        return _get_instrument_info_cached(instrument.lower())

    # -------------------------------------------------------------------------
    # Counterpoint Tools (대위법 도구)
    # -------------------------------------------------------------------------

    @mcp.tool()
    def check_species_rules(
        cantus_firmus: list[str],
        counterpoint: list[str],
        species: int = 1,
    ) -> dict[str, Any]:
        """
        Check species counterpoint rules.

        Analyzes a counterpoint line against a cantus firmus for rule violations.

        Args:
            cantus_firmus: List of pitches for the cantus firmus (e.g., ["C4", "D4", "E4"])
            counterpoint: List of pitches for the counterpoint line
            species: Species number (1-5):
                     1 = Note against note
                     2 = Two notes against one
                     3 = Four notes against one
                     4 = Syncopation/suspensions
                     5 = Florid (free)

        Returns:
            Analysis with intervals and rule violations

        Examples:
            - First species: check_species_rules(["C4", "D4", "E4"], ["G4", "A4", "C5"], species=1)
        """
        from dorico_mcp.tools import check_species_rules as check_rules

        return check_rules(cantus_firmus, counterpoint, species)

    @mcp.tool()
    def generate_counterpoint(
        cantus_firmus: list[str],
        species: int = 1,
        above: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a counterpoint line for a cantus firmus.

        Creates a counterpoint melody following species rules.

        Args:
            cantus_firmus: List of pitches (e.g., ["C4", "D4", "E4", "F4", "E4", "D4", "C4"])
            species: Species number (1-5)
            above: If True, generate counterpoint above CF; if False, below

        Returns:
            Generated counterpoint with validation results

        Examples:
            - Above CF: generate_counterpoint(["C4", "D4", "E4", "D4", "C4"], species=1, above=True)
            - Below CF: generate_counterpoint(["C4", "D4", "E4", "D4", "C4"], species=1, above=False)
        """
        from dorico_mcp.tools import generate_counterpoint as gen_cp

        return gen_cp(cantus_firmus, species, above)

    # -------------------------------------------------------------------------
    # Score Validation Tools (악보 검증 도구)
    # -------------------------------------------------------------------------

    @mcp.tool()
    def validate_voice_leading(
        voices: dict[str, list[str]],
        key: str = "C major",
    ) -> dict[str, Any]:
        """
        Validate voice leading in a multi-voice passage.

        Checks for parallel fifths/octaves, voice crossing, and range issues.

        Args:
            voices: Dictionary mapping voice names to pitch lists
                    Example: {"soprano": ["C5", "D5"], "alto": ["E4", "F4"],
                              "tenor": ["G3", "A3"], "bass": ["C3", "D3"]}
            key: Key for analysis (e.g., "C major", "A minor")

        Returns:
            Validation results with errors and warnings

        Examples:
            - Four-part: validate_voice_leading({
                  "soprano": ["C5", "D5", "E5"],
                  "alto": ["E4", "F4", "G4"],
                  "tenor": ["G3", "A3", "B3"],
                  "bass": ["C3", "D3", "E3"]
              })
        """
        from dorico_mcp.tools import validate_score_section

        return validate_score_section(voices, key)

    @mcp.tool()
    def check_enharmonic(
        pitches: list[str],
        key: str = "C major",
    ) -> dict[str, Any]:
        """
        Check for potentially incorrect enharmonic spellings.

        Suggests alternative spellings based on key context.

        Args:
            pitches: List of pitches to check (e.g., ["C#4", "Db4", "F#4"])
            key: Key context (e.g., "Db major" - suggests Db instead of C#)

        Returns:
            List of spelling suggestions

        Examples:
            - check_enharmonic(["C#4", "F#4"], key="Db major")
              -> Suggests using Db and Gb instead
        """
        from dorico_mcp.tools import check_enharmonic_spelling

        suggestions = check_enharmonic_spelling(pitches, key)
        return {
            "pitches": pitches,
            "key": key,
            "suggestions": suggestions,
            "has_issues": len([s for s in suggestions if "error" not in s]) > 0,
        }

    @mcp.tool()
    def analyze_intervals(pitches: list[str]) -> dict[str, Any]:
        """
        Analyze intervals between consecutive pitches.

        Args:
            pitches: List of pitches (e.g., ["C4", "E4", "G4", "C5"])

        Returns:
            List of intervals with names, semitones, and consonance info
        """
        from dorico_mcp.tools import analyze_intervals as analyze_int

        intervals = analyze_int(pitches)
        return {
            "pitches": pitches,
            "intervals": intervals,
            "count": len(intervals),
        }

    @mcp.tool()
    def check_playability(instrument: str, pitches: list[str]) -> dict[str, Any]:
        """
        Check if a passage is playable on an instrument.

        Args:
            instrument: Instrument name (e.g., "violin", "flute")
            pitches: List of pitches to check

        Returns:
            Playability analysis with range and technique issues
        """
        from dorico_mcp.tools import check_playability as check_play

        return check_play(instrument, pitches)

    @mcp.tool()
    def validate_score(
        voices: dict[str, list[str]],
        key: str = "C major",
    ) -> dict[str, Any]:
        """
        Comprehensive score validation.

        Checks voice leading, ranges, parallel motion, and more.

        Args:
            voices: Dictionary mapping voice names to pitch lists
            key: Key for analysis

        Returns:
            Complete validation report with score and issues
        """
        from dorico_mcp.tools import validate_score as validate_sc

        return validate_sc(voices, key)

    @mcp.tool()
    def detect_parallel_motion(voice1: list[str], voice2: list[str]) -> dict[str, Any]:
        """
        Detect parallel fifths and octaves between two voices.

        Args:
            voice1: List of pitches for first voice
            voice2: List of pitches for second voice

        Returns:
            Detection results with parallel motion instances
        """
        from dorico_mcp.tools import detect_parallel_motion as detect_pm

        return detect_pm(voice1, voice2)

    @mcp.tool()
    def transpose_for_instrument(
        pitch: str,
        instrument: str,
        to_concert: bool = True,
    ) -> dict[str, Any]:
        """
        Transpose a pitch for a transposing instrument.

        Args:
            pitch: Pitch to transpose (e.g., "C4")
            instrument: Instrument name (e.g., "clarinet", "horn", "trumpet")
            to_concert: If True, written to concert pitch; if False, concert to written

        Returns:
            Transposed pitch with interval info
        """
        from dorico_mcp.tools import transpose_for_instrument as transpose_inst

        return transpose_inst(pitch, instrument, to_concert)

    @mcp.tool()
    def realize_figured_bass(
        bass_pitch: str,
        figures: str = "",
        key: str = "C major",
    ) -> dict[str, Any]:
        """
        Realize figured bass notation into chord pitches.

        Args:
            bass_pitch: Bass note (e.g., "C3", "G2")
            figures: Figured bass notation (e.g., "6", "64", "7", "65", "43", "42")
            key: Key context for accidentals

        Returns:
            Realized chord with all pitches
        """
        from dorico_mcp.tools import realize_figured_bass as realize_fb

        return realize_fb(bass_pitch, figures, key)

    @mcp.tool()
    def suggest_cadence(
        current_chord: str,
        key: str = "C major",
        phrase_position: str = "end",
    ) -> dict[str, Any]:
        """
        Suggest appropriate cadence types based on context.

        Args:
            current_chord: Current chord (e.g., "V", "IV", "I")
            key: Key context (e.g., "C major", "A minor")
            phrase_position: Position in phrase ("end", "middle", "beginning")

        Returns:
            Cadence suggestions with explanations
        """
        from dorico_mcp.tools import suggest_cadence as suggest_cad

        return suggest_cad(current_chord, key, phrase_position)

    @mcp.tool()
    def suggest_doubling(
        instrument: str,
        purpose: str = "reinforcement",
        register: str = "middle",
    ) -> dict[str, Any]:
        """
        Suggest instruments for doubling a given instrument.

        Args:
            instrument: Primary instrument to double (e.g., "violin", "flute")
            purpose: Purpose (reinforcement, octave_above, octave_below, color)
            register: Register of the passage (low, middle, high)

        Returns:
            Doubling suggestions with rationale
        """
        from dorico_mcp.tools import suggest_doubling as suggest_dbl

        return suggest_dbl(instrument, purpose, register)

    @mcp.tool()
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
            List of dissonances found with resolution advice
        """
        from dorico_mcp.tools import find_dissonances as find_diss

        return find_diss(pitches, context)

    @mcp.tool()
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
        from dorico_mcp.tools import suggest_instrumentation as suggest_inst

        return suggest_inst(style, size, character)

    @mcp.tool()
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
        from dorico_mcp.tools import balance_dynamics as balance_dyn

        return balance_dyn(instruments, target_dynamic, melody_instrument)

    @mcp.tool()
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
        from dorico_mcp.tools import check_beaming as check_beam

        return check_beam(time_signature, note_values)

    @mcp.tool()
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
        from dorico_mcp.tools import check_spacing as check_space

        return check_space(note_count, bar_width_mm, shortest_note)

    # =========================================================================
    # RESOURCES - Read-only data from Dorico
    # =========================================================================

    @mcp.resource("dorico://status")
    async def resource_status() -> str:
        """Current Dorico connection status and application state."""
        try:
            async with get_client() as client:
                status = await client.get_status()
                return f"Dorico Status:\n{status}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.resource("dorico://score/info")
    async def resource_score_info() -> str:
        """Current score information including title, composer, and instruments."""
        try:
            async with get_client() as client:
                info = await client.get_score_info()
                return f"Score Info:\n{info}"
        except Exception as e:
            return f"Not connected to Dorico or no score open: {e}"

    @mcp.resource("dorico://score/selection")
    async def resource_score_selection() -> str:
        """Current selection information including selected notes and bars."""
        try:
            async with get_client() as client:
                selection = await client.get_selection()
                return f"Selection:\n{selection}"
        except Exception as e:
            return f"Not connected to Dorico or no selection: {e}"

    @mcp.resource("dorico://instruments/list")
    def resource_instrument_list() -> str:
        """List of available instruments with basic info."""
        from dorico_mcp.tools.instruments import INSTRUMENTS

        lines = ["# Available Instruments\n"]
        families: dict[str, list[str]] = {}

        for _name, info in INSTRUMENTS.items():
            family = info.family.value
            if family not in families:
                families[family] = []
            families[family].append(f"- {info.name} ({info.lowest_pitch} - {info.highest_pitch})")

        for family, instruments in sorted(families.items()):
            lines.append(f"\n## {family.title()}\n")
            lines.extend(instruments)

        return "\n".join(lines)

    @mcp.resource("dorico://instruments/ranges")
    def resource_instrument_ranges() -> str:
        """Standard instrument ranges for orchestration reference."""
        ranges = """
# Instrument Ranges (Concert Pitch)

## Woodwinds
| Instrument | Low | High | Comfortable Range |
|------------|-----|------|-------------------|
| Piccolo | D5 | C8 | G5 - G7 |
| Flute | C4 | D7 | G4 - D6 |
| Oboe | Bb3 | G6 | D4 - D6 |
| Clarinet (Bb) | D3 | Bb6 | G3 - C6 |
| Bassoon | Bb1 | Eb5 | C2 - G4 |

## Brass
| Instrument | Low | High | Comfortable Range |
|------------|-----|------|-------------------|
| Horn (F) | F#2 | C6 | C3 - G5 |
| Trumpet (Bb) | F#3 | D6 | G3 - G5 |
| Trombone | E2 | Bb4 | A2 - F4 |
| Tuba | D1 | F4 | F1 - Bb3 |

## Strings
| Instrument | Low | High | Comfortable Range |
|------------|-----|------|-------------------|
| Violin | G3 | E7 | G3 - B6 |
| Viola | C3 | E6 | C3 - C6 |
| Cello | C2 | A5 | C2 - G4 |
| Double Bass | E1 | G4 | E1 - D3 |

## Other
| Instrument | Low | High |
|------------|-----|------|
| Piano | A0 | C8 |
| Harp | Cb1 | G#7 |
| Timpani | D2 | C4 |
"""
        return ranges

    # =========================================================================
    # PROMPTS - Guided workflows
    # =========================================================================

    @mcp.prompt()
    def harmonize_melody() -> str:
        """Workflow for harmonizing a melody with four-part harmony."""
        return """
# Harmonize Melody Workflow

You are helping a composition student harmonize a melody. Follow these steps:

## Step 1: Analyze the Melody
- Identify the key (look at starting/ending notes, accidentals)
- Note the phrase structure
- Identify cadence points

## Step 2: Choose Chords
For each melody note, suggest appropriate harmonizations:
- Use primarily I, IV, V, vi chords
- Consider passing tones vs. chord tones
- Plan cadences (authentic: V-I, half: I-V, plagal: IV-I)

## Step 3: Write Bass Line
- Contrary motion to melody when possible
- Approach cadences properly
- Check for parallel 5ths/8ves with melody

## Step 4: Fill Inner Voices (Alto, Tenor)
- Keep common tones
- Move by step when possible
- Avoid voice crossing

## Step 5: Check Voice Leading
- No parallel 5ths or 8ves
- Resolve leading tones up to tonic
- Resolve 7ths down by step

Use the Dorico tools to input notes, set key signatures, and add dynamics.
"""

    @mcp.prompt()
    def orchestration_basics() -> str:
        """Workflow for basic orchestration of a piano piece."""
        return """
# Piano to Orchestra Workflow

You are helping orchestrate a piano piece. Follow these steps:

## Step 1: Analyze the Piano Score
- Identify melody, harmony, bass
- Note the register of each element
- Identify dynamic range and character

## Step 2: Assign Instruments
- Melody: Strings (violin, cello) or winds (flute, oboe, clarinet)
- Harmony: Horns, middle strings (viola), clarinets
- Bass: Cello, double bass, bassoon, tuba

## Step 3: Consider Instrument Characteristics
- Woodwinds: Clear, agile, can be soft
- Brass: Powerful, majestic, can sustain
- Strings: Versatile, expressive, can do everything

## Step 4: Check Ranges
Use the dorico://instruments/ranges resource to verify all notes are playable.

## Step 5: Add Expression
- Dynamics appropriate to each instrument
- Articulations (strings can do more than winds)
- Doublings for important passages

Use add_instrument() to add instruments, then add_notes() for each part.
"""

    @mcp.prompt()
    def species_counterpoint() -> str:
        """Workflow for species counterpoint exercises."""
        return """
# Species Counterpoint Exercise

You are helping with a counterpoint exercise.

## First Species (Note against note)
Rules:
1. Begin and end on perfect consonance (unison, 5th, octave)
2. Use only consonances (3rd, 5th, 6th, octave)
3. No parallel 5ths or 8ves
4. Contrary motion preferred
5. No leaps larger than an octave
6. Stepwise motion preferred

## Second Species (Two notes against one)
Additional rules:
1. First note of each bar must be consonant
2. Second note can be dissonant if passing tone
3. Leaps followed by step in opposite direction

## Third Species (Four notes against one)
1. First note consonant
2. Other notes can be passing or neighbor tones
3. Avoid repeated notes

## Fourth Species (Syncopation)
1. Tied notes create suspensions
2. Dissonance on strong beat, resolve down by step
3. 4-3, 7-6, 9-8 suspensions

## Fifth Species (Florid)
Combines all previous species with free rhythm.

Use add_notes() to input the counterpoint, checking intervals as you go.
"""

    @mcp.prompt()
    def chord_progression_workshop() -> str:
        """Workflow for creating and refining chord progressions."""
        return """
# Chord Progression Workshop

You are helping a composition student create chord progressions.

## Step 1: Set the Context
- Choose a key (major or minor)
- Determine the style (classical, pop, jazz)
- Set the length (4, 8, 16 bars)

## Step 2: Start with Basic Progressions
For classical:
- I-IV-V-I (basic)
- I-vi-IV-V (50s progression)
- I-IV-vii°-iii-vi-ii-V-I (circle of fifths)

For pop:
- I-V-vi-IV (four chord)
- vi-IV-I-V (axis)
- I-vi-IV-V (50s)

For jazz:
- ii7-V7-Imaj7 (basic turnaround)
- Imaj7-vi7-ii7-V7 (rhythm changes)

## Step 3: Add Variations
- Secondary dominants (V/V, V/ii)
- Modal interchange (bVI, bVII in major)
- Passing chords
- Pedal points

## Step 4: Plan Cadences
Use suggest_cadence() to find appropriate cadence types:
- Authentic (V-I) for strong endings
- Half (I-V) for phrase midpoints
- Deceptive (V-vi) for unexpected turns

## Step 5: Voice the Chords
- Use realize_figured_bass() for bass + figures
- Check voice leading with validate_voice_leading()
- Add to Dorico with add_notes()
"""

    @mcp.prompt()
    def score_review() -> str:
        """Workflow for comprehensive score review and proofreading."""
        return """
# Score Review Checklist

You are reviewing a score for errors and improvements.

## Step 1: Range Check
For each instrument part:
- Use check_instrument_range() to verify all notes are playable
- Use check_playability() for technical passages
- Flag notes outside comfortable range

## Step 2: Voice Leading Check
For harmonic passages:
- Use validate_voice_leading() for parallel 5ths/8ves
- Check for proper resolution of dissonances
- Verify leading tone resolutions

## Step 3: Harmony Analysis
- Use analyze_chord() on vertical sonorities
- Verify Roman numeral analysis
- Check for unintended dissonances with find_dissonances()

## Step 4: Orchestration Review
- Verify doublings make sense (suggest_doubling())
- Check dynamic balance between sections
- Ensure transposing instruments are handled correctly

## Step 5: Generate Report
Summarize findings:
- Critical errors (unplayable notes, parallel 5ths)
- Warnings (awkward passages, unusual progressions)
- Suggestions (better voicings, doublings)

Use the Dorico tools to make corrections as needed.
"""

    return mcp


def main() -> None:
    """Run the MCP server."""
    import sys

    mcp = create_server()

    # Run with stdio transport (for Claude Desktop)
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
    else:
        # Default to stdio
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
