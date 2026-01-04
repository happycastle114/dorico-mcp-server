"""
Mock Dorico WebSocket Server for E2E Testing.

This module provides a fake Dorico server that simulates the Dorico Remote Control API
for testing purposes without requiring actual Dorico installation.
"""

import asyncio
import json
import logging
import uuid
from typing import Any

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class MockDoricoServer:
    """
    Mock Dorico WebSocket server for testing.

    Simulates Dorico's Remote Control API behavior including:
    - Connection handshake with session token
    - Command processing and responses
    - State management (current score, selection, etc.)
    """

    def __init__(self, host: str = "localhost", port: int = 4560):
        self.host = host
        self.port = port
        self._server = None
        self._clients: set[WebSocketServerProtocol] = set()

        # Mock state
        self._state = {
            "connected": False,
            "session_token": None,
            "current_score": None,
            "scores": [],
            "instruments": [],
            "selection": None,
            "caret_position": {"bar": 1, "beat": 1},
            "mode": "write",
            "playback_state": "stopped",
        }

        # Command history for verification
        self._command_history: list[dict[str, Any]] = []

        # Registered commands and their handlers
        self._handlers = self._register_handlers()

    def _register_handlers(self) -> dict[str, callable]:
        """Register command handlers."""
        return {
            # File commands
            "File.New": self._handle_file_new,
            "File.Open": self._handle_file_open,
            "File.Save": self._handle_file_save,
            "File.SaveAs": self._handle_file_save_as,
            "File.Close": self._handle_file_close,
            "File.ExportPDF": self._handle_file_export,
            "File.ExportMusicXML": self._handle_file_export,
            # Edit commands
            "Edit.Undo": self._handle_simple_success,
            "Edit.Redo": self._handle_simple_success,
            "Edit.Copy": self._handle_simple_success,
            "Edit.Cut": self._handle_simple_success,
            "Edit.Paste": self._handle_simple_success,
            "Edit.Delete": self._handle_simple_success,
            "Edit.SelectAll": self._handle_simple_success,
            "Edit.AddKeySignature": self._handle_add_key_signature,
            "Edit.AddTimeSignature": self._handle_add_time_signature,
            "Edit.AddDynamic": self._handle_add_dynamic,
            "Edit.AddArticulation": self._handle_simple_success,
            "Edit.AddSlur": self._handle_simple_success,
            "Edit.AddTempo": self._handle_add_tempo,
            "Edit.AddText": self._handle_simple_success,
            "Edit.AddInstrument": self._handle_add_instrument,
            "Edit.RemoveInstrument": self._handle_remove_instrument,
            "Edit.TransposeUpOctave": self._handle_simple_success,
            "Edit.TransposeDownOctave": self._handle_simple_success,
            "Edit.TransposeChromatic": self._handle_simple_success,
            # Note input commands
            "NoteInput.Enter": self._handle_note_input_enter,
            "NoteInput.Exit": self._handle_note_input_exit,
            "NoteInput.SetDuration": self._handle_simple_success,
            "NoteInput.Pitch": self._handle_note_input_pitch,
            "NoteInput.Rest": self._handle_note_input_rest,
            "NoteInput.Tie": self._handle_simple_success,
            "NoteInput.Dot": self._handle_simple_success,
            "NoteInput.ChordModeOn": self._handle_simple_success,
            "NoteInput.ChordModeOff": self._handle_simple_success,
            # Navigation commands
            "Navigate.NextBar": self._handle_navigate_next_bar,
            "Navigate.PreviousBar": self._handle_navigate_previous_bar,
            "Navigate.GoToBar": self._handle_navigate_go_to_bar,
            "Navigate.Start": self._handle_navigate_start,
            "Navigate.End": self._handle_simple_success,
            # View commands
            "View.WriteMode": self._handle_view_mode,
            "View.EngraveMode": self._handle_view_mode,
            "View.PlayMode": self._handle_view_mode,
            "View.PrintMode": self._handle_view_mode,
            # Playback commands
            "Playback.Play": self._handle_playback_play,
            "Playback.Stop": self._handle_playback_stop,
            "Playback.Rewind": self._handle_playback_rewind,
            # Application commands
            "Application.Status": self._handle_application_status,
            "Application.GetCommands": self._handle_get_commands,
            "Edit.GetSelection": self._handle_get_selection,
        }

    async def start(self) -> None:
        """Start the mock server."""
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        logger.info(f"Mock Dorico server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the mock server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Mock Dorico server stopped")

    async def __aenter__(self) -> "MockDoricoServer":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    def get_command_history(self) -> list[dict[str, Any]]:
        """Get list of all commands received."""
        return self._command_history.copy()

    def clear_command_history(self) -> None:
        """Clear command history."""
        self._command_history.clear()

    def get_state(self) -> dict[str, Any]:
        """Get current mock state."""
        return self._state.copy()

    def reset_state(self) -> None:
        """Reset mock state to initial values."""
        self._state = {
            "connected": False,
            "session_token": None,
            "current_score": None,
            "scores": [],
            "instruments": [],
            "selection": None,
            "caret_position": {"bar": 1, "beat": 1},
            "mode": "write",
            "playback_state": "stopped",
        }
        self._command_history.clear()

    # =========================================================================
    # WebSocket Handlers
    # =========================================================================

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a client connection."""
        self._clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                await self._process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self._clients.discard(websocket)

    async def _process_message(
        self,
        websocket: WebSocketServerProtocol,
        message: str,
    ) -> None:
        """Process incoming message."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {message}")
            return

        msg_type = data.get("message", "")
        logger.debug(f"Received: {msg_type}")

        if msg_type == "connect":
            await self._handle_connect(websocket, data)
        elif msg_type == "acceptsessiontoken":
            await self._handle_accept_token(websocket, data)
        elif msg_type == "command":
            await self._handle_command(websocket, data)
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_connect(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        """Handle connection handshake."""
        client_name = data.get("clientName", "Unknown")
        existing_token = data.get("sessionToken")

        logger.info(f"Client '{client_name}' connecting...")

        # Generate or verify session token
        if existing_token and existing_token == self._state.get("session_token"):
            # Reuse existing token
            token = existing_token
        else:
            # Generate new token
            token = str(uuid.uuid4())

        self._state["session_token"] = token

        # Send session token
        await websocket.send(
            json.dumps(
                {
                    "message": "sessiontoken",
                    "sessionToken": token,
                }
            )
        )

    async def _handle_accept_token(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        """Handle session token acceptance."""
        token = data.get("sessionToken")
        if token == self._state.get("session_token"):
            self._state["connected"] = True
            logger.info("Session established")

    async def _handle_command(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        """Handle command execution."""
        command_str = data.get("command", "")
        request_id = data.get("requestId", str(uuid.uuid4())[:8])

        # Parse command
        command_name, params = self._parse_command(command_str)

        # Record in history
        self._command_history.append(
            {
                "command": command_name,
                "params": params,
                "raw": command_str,
                "request_id": request_id,
            }
        )

        logger.debug(f"Command: {command_name}, Params: {params}")

        # Execute handler
        handler = self._handlers.get(command_name)
        if handler:
            result = await handler(params)
        else:
            # Unknown command - still succeed (Dorico is permissive)
            result = {"success": True, "message": f"Command '{command_name}' executed"}

        # Send response
        response = {
            "message": "response",
            "requestId": request_id,
            "success": result.get("success", True),
        }
        if "data" in result:
            response["data"] = result["data"]
        if "error" in result:
            response["error"] = result["error"]

        await websocket.send(json.dumps(response))

    def _parse_command(self, command_str: str) -> tuple[str, dict[str, str]]:
        """Parse command string into name and parameters."""
        if "?" in command_str:
            name, params_str = command_str.split("?", 1)
            params = {}
            for param in params_str.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = value
            return name, params
        return command_str, {}

    # =========================================================================
    # Command Handlers
    # =========================================================================

    async def _handle_simple_success(self, params: dict) -> dict:
        """Handler for commands that just succeed."""
        return {"success": True}

    async def _handle_file_new(self, params: dict) -> dict:
        """Handle File.New command."""
        score_id = str(uuid.uuid4())[:8]
        score = {
            "id": score_id,
            "title": "Untitled",
            "composer": "",
            "instruments": [],
            "bars": 32,
            "key_signature": "C major",
            "time_signature": "4/4",
            "tempo": 120,
        }
        self._state["scores"].append(score)
        self._state["current_score"] = score_id
        self._state["instruments"] = []
        self._state["caret_position"] = {"bar": 1, "beat": 1}
        return {"success": True, "data": {"scoreId": score_id}}

    async def _handle_file_open(self, params: dict) -> dict:
        """Handle File.Open command."""
        path = params.get("Path", "")
        score_id = str(uuid.uuid4())[:8]
        self._state["current_score"] = score_id
        return {"success": True, "data": {"scoreId": score_id, "path": path}}

    async def _handle_file_save(self, params: dict) -> dict:
        """Handle File.Save command."""
        if not self._state["current_score"]:
            return {"success": False, "error": "No score open"}
        return {"success": True}

    async def _handle_file_save_as(self, params: dict) -> dict:
        """Handle File.SaveAs command."""
        path = params.get("Path", "")
        if not self._state["current_score"]:
            return {"success": False, "error": "No score open"}
        return {"success": True, "data": {"path": path}}

    async def _handle_file_close(self, params: dict) -> dict:
        """Handle File.Close command."""
        self._state["current_score"] = None
        return {"success": True}

    async def _handle_file_export(self, params: dict) -> dict:
        """Handle export commands."""
        path = params.get("Path", "")
        if not self._state["current_score"]:
            return {"success": False, "error": "No score open"}
        return {"success": True, "data": {"path": path}}

    async def _handle_add_key_signature(self, params: dict) -> dict:
        """Handle Edit.AddKeySignature command."""
        tonic = params.get("Tonic", "C")
        mode = params.get("Mode", "Major")
        accidental = params.get("Accidental", "")
        key = f"{tonic}{accidental} {mode.lower()}"

        # Update current score
        for score in self._state["scores"]:
            if score["id"] == self._state["current_score"]:
                score["key_signature"] = key
                break

        return {"success": True, "data": {"key": key}}

    async def _handle_add_time_signature(self, params: dict) -> dict:
        """Handle Edit.AddTimeSignature command."""
        numerator = params.get("Numerator", "4")
        denominator = params.get("Denominator", "4")
        time_sig = f"{numerator}/{denominator}"

        for score in self._state["scores"]:
            if score["id"] == self._state["current_score"]:
                score["time_signature"] = time_sig
                break

        return {"success": True, "data": {"timeSignature": time_sig}}

    async def _handle_add_dynamic(self, params: dict) -> dict:
        """Handle Edit.AddDynamic command."""
        dynamic = params.get("Dynamic", "mf")
        return {"success": True, "data": {"dynamic": dynamic}}

    async def _handle_add_tempo(self, params: dict) -> dict:
        """Handle Edit.AddTempo command."""
        bpm = params.get("BPM", "120")
        text = params.get("Text")

        for score in self._state["scores"]:
            if score["id"] == self._state["current_score"]:
                score["tempo"] = int(bpm)
                break

        return {"success": True, "data": {"bpm": bpm, "text": text}}

    async def _handle_add_instrument(self, params: dict) -> dict:
        """Handle Edit.AddInstrument command."""
        name = params.get("Name", "Piano")
        self._state["instruments"].append(name)
        return {"success": True, "data": {"instrument": name}}

    async def _handle_remove_instrument(self, params: dict) -> dict:
        """Handle Edit.RemoveInstrument command."""
        name = params.get("Name", "")
        if name in self._state["instruments"]:
            self._state["instruments"].remove(name)
            return {"success": True}
        return {"success": False, "error": f"Instrument '{name}' not found"}

    async def _handle_note_input_enter(self, params: dict) -> dict:
        """Handle NoteInput.Enter command."""
        self._state["mode"] = "note_input"
        return {"success": True}

    async def _handle_note_input_exit(self, params: dict) -> dict:
        """Handle NoteInput.Exit command."""
        self._state["mode"] = "write"
        return {"success": True}

    async def _handle_note_input_pitch(self, params: dict) -> dict:
        """Handle NoteInput.Pitch command."""
        note = params.get("Note", "C")
        octave = params.get("Octave", "4")
        accidental = params.get("Accidental", "")
        pitch = f"{note}{accidental}{octave}"
        return {"success": True, "data": {"pitch": pitch}}

    async def _handle_note_input_rest(self, params: dict) -> dict:
        """Handle NoteInput.Rest command."""
        return {"success": True, "data": {"type": "rest"}}

    async def _handle_navigate_next_bar(self, params: dict) -> dict:
        """Handle Navigate.NextBar command."""
        self._state["caret_position"]["bar"] += 1
        return {"success": True, "data": self._state["caret_position"]}

    async def _handle_navigate_previous_bar(self, params: dict) -> dict:
        """Handle Navigate.PreviousBar command."""
        if self._state["caret_position"]["bar"] > 1:
            self._state["caret_position"]["bar"] -= 1
        return {"success": True, "data": self._state["caret_position"]}

    async def _handle_navigate_go_to_bar(self, params: dict) -> dict:
        """Handle Navigate.GoToBar command."""
        bar = int(params.get("Bar", 1))
        self._state["caret_position"]["bar"] = max(1, bar)
        return {"success": True, "data": self._state["caret_position"]}

    async def _handle_navigate_start(self, params: dict) -> dict:
        """Handle Navigate.Start command."""
        self._state["caret_position"] = {"bar": 1, "beat": 1}
        return {"success": True, "data": self._state["caret_position"]}

    async def _handle_view_mode(self, params: dict) -> dict:
        """Handle View mode changes."""
        return {"success": True}

    async def _handle_playback_play(self, params: dict) -> dict:
        """Handle Playback.Play command."""
        self._state["playback_state"] = "playing"
        return {"success": True}

    async def _handle_playback_stop(self, params: dict) -> dict:
        """Handle Playback.Stop command."""
        self._state["playback_state"] = "stopped"
        return {"success": True}

    async def _handle_playback_rewind(self, params: dict) -> dict:
        """Handle Playback.Rewind command."""
        self._state["caret_position"] = {"bar": 1, "beat": 1}
        self._state["playback_state"] = "stopped"
        return {"success": True}

    async def _handle_application_status(self, params: dict) -> dict:
        """Handle Application.Status command."""
        return {
            "success": True,
            "data": {
                "version": "5.1.0 (Mock)",
                "connected": self._state["connected"],
                "currentScore": self._state["current_score"],
                "instruments": self._state["instruments"],
                "mode": self._state["mode"],
                "playbackState": self._state["playback_state"],
                "caretPosition": self._state["caret_position"],
            },
        }

    async def _handle_get_commands(self, params: dict) -> dict:
        """Handle Application.GetCommands command."""
        return {
            "success": True,
            "data": {
                "commands": list(self._handlers.keys()),
            },
        }

    async def _handle_get_selection(self, params: dict) -> dict:
        """Handle Edit.GetSelection command."""
        return {
            "success": True,
            "data": {
                "selection": self._state["selection"],
                "hasSelection": self._state["selection"] is not None,
            },
        }


async def run_mock_server(port: int = 4560) -> None:
    """Run the mock server standalone."""
    logging.basicConfig(level=logging.INFO)
    server = MockDoricoServer(port=port)
    await server.start()

    print(f"Mock Dorico server running on ws://localhost:{port}")
    print("Press Ctrl+C to stop...")

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(run_mock_server())
