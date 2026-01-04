"""
Dorico MCP Server - Main Server Entry Point.

This is the FastMCP server that Claude Desktop connects to.
It exposes tools, resources, and prompts for controlling Dorico.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP

from dorico_mcp.client import DoricoClient, DoricoConnectionError
from dorico_mcp.models import (
    AddDynamicsInput,
    AddNotesInput,
    CreateScoreInput,
    Dynamic,
    KeyMode,
    NoteDuration,
    SetKeySignatureInput,
    SetTimeSignatureInput,
    TransposeInput,
)
from dorico_mcp import commands as cmd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
_dorico_client: DoricoClient | None = None


@asynccontextmanager
async def get_client() -> AsyncIterator[DoricoClient]:
    """Get or create Dorico client connection."""
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
        version="0.1.0",
        description="Control Dorico music notation software via natural language. "
        "Designed for composition majors (작곡 전공자) to streamline their workflow.",
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

    # -------------------------------------------------------------------------
    # Score Management Tools
    # -------------------------------------------------------------------------

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
                    await client.send_command(
                        cmd.add_time_signature(int(num), int(denom))
                    )

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

                response = await client.send_command(
                    cmd.add_time_signature(numerator, denominator)
                )
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
