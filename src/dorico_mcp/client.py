"""
Dorico WebSocket Client.

Handles communication with Dorico via its Remote Control API.
Implements connection management, command sending, and error handling.
"""

import asyncio
import json
import logging
import os
import platform
import uuid
from pathlib import Path
from typing import Any

import websockets
from websockets import ClientConnection

from dorico_mcp.models import ConnectionState, DoricoCommand, DoricoResponse

logger = logging.getLogger(__name__)


class DoricoConnectionError(Exception):
    """Raised when connection to Dorico fails."""

    pass


class DoricoCommandError(Exception):
    """Raised when a command execution fails."""

    pass


class DoricoClient:
    """
    WebSocket client for Dorico Remote Control API.

    This client handles:
    - Connection lifecycle (connect, reconnect, disconnect)
    - Session token management for persistent connections
    - Command serialization and sending
    - Response parsing and error handling

    Usage:
        async with DoricoClient() as client:
            response = await client.send_command("File.New")
    """

    # Default ports that Dorico might use
    DEFAULT_PORTS = [4560, 4561, 4562, 4563, 4564, 4565]

    # Connection timeouts
    CONNECT_TIMEOUT = 10.0
    COMMAND_TIMEOUT = 30.0
    KEEPALIVE_INTERVAL = 30.0

    def __init__(
        self,
        host: str = "localhost",
        port: int | None = None,
        client_name: str = "Dorico MCP Server",
        auto_reconnect: bool = True,
    ):
        """
        Initialize Dorico client.

        Args:
            host: Dorico host (usually localhost)
            port: WebSocket port (None = auto-detect)
            client_name: Name shown in Dorico's connection dialog
            auto_reconnect: Automatically reconnect on disconnection
        """
        self.host = host
        self.port = port
        self.client_name = client_name
        self.auto_reconnect = auto_reconnect

        self._websocket: ClientConnection | None = None
        self._state = ConnectionState.DISCONNECTED
        self._session_token: str | None = None
        self._handshake_id: str | None = None
        self._request_queue: asyncio.Queue[tuple[str, asyncio.Future[DoricoResponse]]] = (
            asyncio.Queue()
        )
        self._pending_requests: dict[str, asyncio.Future[DoricoResponse]] = {}
        self._receive_task: asyncio.Task[None] | None = None
        self._keepalive_task: asyncio.Task[None] | None = None
        self._event_handlers: dict[str, list[Any]] = {
            "status": [],
            "selectionchanged": [],
            "documentchanged": [],
        }

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Whether client is connected to Dorico."""
        return self._state == ConnectionState.CONNECTED

    @property
    def token_file_path(self) -> Path:
        """Path to saved session token file."""
        if platform.system() == "Windows":
            base = Path(os.environ.get("APPDATA", "~"))
        else:
            base = Path.home() / ".config"
        return base / "dorico-mcp" / "session_token.json"

    # =========================================================================
    # Connection Lifecycle
    # =========================================================================

    async def connect(self) -> bool:
        """
        Connect to Dorico.

        This performs the full handshake:
        1. Find Dorico's WebSocket port
        2. Send connect message
        3. Wait for user approval (if first time)
        4. Exchange session token

        Returns:
            True if connected successfully
        """
        if self.is_connected:
            return True

        self._state = ConnectionState.CONNECTING

        # Try to find Dorico's port
        port = await self._find_dorico_port()
        if port is None:
            self._state = ConnectionState.ERROR
            raise DoricoConnectionError(
                "Could not find Dorico. Make sure Dorico is running and Remote Control is enabled."
            )

        self.port = port
        logger.info(f"Found Dorico on port {port}")

        # Connect WebSocket
        uri = f"ws://{self.host}:{self.port}"
        try:
            self._websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=self.CONNECT_TIMEOUT,
            )
        except TimeoutError as e:
            self._state = ConnectionState.ERROR
            raise DoricoConnectionError(f"Connection to {uri} timed out") from e
        except Exception as e:
            self._state = ConnectionState.ERROR
            raise DoricoConnectionError(f"Failed to connect to Dorico: {e}") from e

        # Start receive loop
        self._receive_task = asyncio.create_task(self._receive_loop())

        # Perform handshake
        try:
            await self._handshake()
        except Exception as e:
            await self.disconnect()
            raise DoricoConnectionError(f"Handshake failed: {e}") from e

        # Start keepalive
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())

        self._state = ConnectionState.CONNECTED
        logger.info("Connected to Dorico successfully")
        return True

    async def disconnect(self) -> None:
        """Disconnect from Dorico."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        self._state = ConnectionState.DISCONNECTED
        logger.info("Disconnected from Dorico")

    async def __aenter__(self) -> "DoricoClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    # =========================================================================
    # Command Sending
    # =========================================================================

    async def send_command(
        self,
        command: str | DoricoCommand,
        timeout: float | None = None,
    ) -> DoricoResponse:
        """
        Send a command to Dorico.

        Args:
            command: Command string (e.g., "File.New") or DoricoCommand object
            timeout: Command timeout in seconds (None = default)

        Returns:
            DoricoResponse with success status and data
        """
        if not self.is_connected:
            if self.auto_reconnect:
                await self.connect()
            else:
                raise DoricoConnectionError("Not connected to Dorico")

        # Build command string
        command_str = command.to_command_string() if isinstance(command, DoricoCommand) else command

        # Create request
        request_id = str(uuid.uuid4())[:8]
        message = json.dumps(
            {
                "message": "command",
                "command": command_str,
                "requestId": request_id,
            }
        )

        # Send and wait for response
        future: asyncio.Future[DoricoResponse] = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            if self._websocket is None:
                raise DoricoConnectionError("WebSocket not connected")

            await self._websocket.send(message)
            logger.debug(f"Sent command: {command_str}")

            response = await asyncio.wait_for(
                future,
                timeout=timeout or self.COMMAND_TIMEOUT,
            )
            return response

        except TimeoutError as e:
            self._pending_requests.pop(request_id, None)
            raise DoricoCommandError(f"Command '{command_str}' timed out") from e

        except Exception as e:
            self._pending_requests.pop(request_id, None)
            raise DoricoCommandError(f"Command failed: {e}") from e

    async def send_commands(
        self,
        commands: list[str | DoricoCommand],
    ) -> list[DoricoResponse]:
        """
        Send multiple commands in sequence.

        Args:
            commands: List of commands to execute

        Returns:
            List of responses
        """
        responses = []
        for cmd in commands:
            response = await self.send_command(cmd)
            responses.append(response)
            if not response.success:
                break  # Stop on first error
        return responses

    # =========================================================================
    # Status Queries
    # =========================================================================

    async def get_status(self) -> dict[str, Any]:
        """Get Dorico application status."""
        response = await self.send_command("Application.Status")
        return response.data or {}

    async def get_commands(self) -> list[str]:
        response = await self.send_command("Application.GetCommands")
        if response.data and "commands" in response.data:
            commands = response.data["commands"]
            return list(commands) if isinstance(commands, list) else []
        return []

    async def get_selection(self) -> dict[str, Any]:
        """Get current selection in Dorico."""
        response = await self.send_command("Edit.GetSelection")
        return response.data or {}

    async def get_score_info(self) -> dict[str, Any]:
        """Get current score information."""
        response = await self.send_command("Document.GetInfo")
        return response.data or {}

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _find_dorico_port(self) -> int | None:
        """Find which port Dorico is listening on."""
        if self.port:
            return self.port

        for port in self.DEFAULT_PORTS:
            try:
                uri = f"ws://{self.host}:{port}"
                ws = await asyncio.wait_for(
                    websockets.connect(uri),
                    timeout=1.0,
                )
                await ws.close()
                return port
            except Exception:
                continue

        return None

    async def _handshake(self) -> None:
        """Perform Dorico connection handshake."""
        if self._websocket is None:
            raise DoricoConnectionError("WebSocket not initialized")

        # Check for saved token
        saved_token = self._load_session_token()

        # Send connect message
        self._handshake_id = str(uuid.uuid4())
        connect_msg = {
            "message": "connect",
            "clientName": self.client_name,
            "handshakeId": self._handshake_id,
        }
        if saved_token:
            connect_msg["sessionToken"] = saved_token

        await self._websocket.send(json.dumps(connect_msg))
        logger.debug("Sent connect message")

        # Wait for session token response (will be handled by receive loop)
        self._state = ConnectionState.AWAITING_APPROVAL

        # The response will be handled in _handle_message
        # Wait up to 60 seconds for user approval
        for _ in range(60):
            if self._session_token:
                break
            await asyncio.sleep(1.0)
        else:
            raise DoricoConnectionError("Timeout waiting for session approval")

    async def _receive_loop(self) -> None:
        """Background loop to receive messages from Dorico."""
        if self._websocket is None:
            return

        try:
            async for message in self._websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to Dorico closed")
            self._state = ConnectionState.DISCONNECTED
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            self._state = ConnectionState.ERROR

    async def _handle_message(self, message: str | bytes) -> None:
        """Handle incoming message from Dorico."""
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Dorico: {message}")
            return

        msg_type = data.get("message", "")
        logger.debug(f"Received message type: {msg_type}")

        if msg_type == "sessiontoken":
            # Store session token
            self._session_token = data.get("sessionToken")
            if self._session_token:
                self._save_session_token(self._session_token)

            # Accept the token
            if self._websocket:
                await self._websocket.send(
                    json.dumps(
                        {
                            "message": "acceptsessiontoken",
                            "sessionToken": self._session_token,
                        }
                    )
                )

        elif msg_type == "response":
            # Match to pending request
            request_id = data.get("requestId")
            if request_id and request_id in self._pending_requests:
                future = self._pending_requests.pop(request_id)
                response = DoricoResponse(
                    success=data.get("success", False),
                    message=data.get("message"),
                    data=data.get("data"),
                    error=data.get("error"),
                )
                future.set_result(response)

        elif msg_type == "status":
            logger.debug(f"Status update: {data}")
            await self._dispatch_event("status", data)

        elif msg_type == "selectionchanged":
            logger.debug(f"Selection changed: {data}")
            await self._dispatch_event("selectionchanged", data)

        elif msg_type == "documentchanged":
            logger.debug(f"Document changed: {data}")
            await self._dispatch_event("documentchanged", data)

    def on_event(self, event_type: str, handler: Any) -> None:
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)

    def off_event(self, event_type: str, handler: Any) -> None:
        if event_type in self._event_handlers and handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)

    async def _dispatch_event(self, event_type: str, data: dict[str, Any]) -> None:
        for handler in self._event_handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")

    async def _keepalive_loop(self) -> None:
        """Send periodic keepalive messages."""
        while self.is_connected and self._websocket:
            try:
                await asyncio.sleep(self.KEEPALIVE_INTERVAL)
                if self._websocket:
                    await self._websocket.ping()
            except Exception:
                break

    def _load_session_token(self) -> str | None:
        try:
            if self.token_file_path.exists():
                data = json.loads(self.token_file_path.read_text())
                token = data.get("token")
                return str(token) if token is not None else None
        except Exception:
            pass
        return None

    def _save_session_token(self, token: str) -> None:
        """Save session token to file."""
        try:
            self.token_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_file_path.write_text(json.dumps({"token": token}))
        except Exception as e:
            logger.warning(f"Failed to save session token: {e}")
