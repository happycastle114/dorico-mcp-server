# Dorico MCP Server - Setup Guide

Complete guide to setting up and using the Dorico MCP Server with Claude Desktop and ChatGPT Desktop.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| Steinberg Dorico | 5.0+ | Music notation software |
| Claude Desktop or ChatGPT Desktop | Latest | AI interface |
| Git | Latest | Version control (for development) |

### System Requirements

- **OS**: Windows 10/11, macOS 12+, or Linux
- **RAM**: 8GB minimum (16GB recommended for Dorico)
- **Disk**: 500MB for the MCP server

---

## Installation

### Option 1: Install from PyPI (Recommended)

The easiest way to install:

```bash
pip install dorico-mcp-server
```

Or with a specific version:

```bash
pip install dorico-mcp-server==0.1.0
```

### Option 2: Install from Source (Development)

#### Step 1: Clone the Repository

```bash
git clone https://github.com/happycastle114/dorico-mcp-server.git
cd dorico-mcp-server
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
# Install in development mode
pip install -e ".[dev]"
```

This installs:
- `mcp` - Model Context Protocol SDK
- `websockets` - WebSocket client/server
- `pydantic` - Data validation
- `music21` - Music theory analysis
- `pytest` - Testing framework

### Verify Installation

```bash
# Check the package is installed
python -c "import dorico_mcp; print('OK')"

# Run tests to verify everything works (if installed from source)
pytest tests/ -v
```

---

## Configuration

### Enable Dorico Remote Control

1. Open **Steinberg Dorico**
2. Go to **Edit** → **Preferences** (Windows) or **Dorico** → **Preferences** (macOS)
3. Navigate to **General** tab
4. Find **Remote Control** section
5. Check **Allow remote control connections**
6. Note the **Port number** (default: 4560)
7. Click **Apply** and **OK**

---

### Configure Claude Desktop

Add the Dorico MCP server to your Claude Desktop configuration:

#### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "C:\\path\\to\\dorico-mcp-server\\src",
      "env": {
        "PYTHONPATH": "C:\\path\\to\\dorico-mcp-server\\src"
      }
    }
  }
}
```

#### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python3",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python3",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "/Users/yourname/dorico-mcp-server/src",
      "env": {
        "PYTHONPATH": "/Users/yourname/dorico-mcp-server/src"
      }
    }
  }
}
```

#### Linux

Edit `~/.config/Claude/claude_desktop_config.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "/home/yourname/dorico-mcp-server/src",
      "env": {
        "PYTHONPATH": "/home/yourname/dorico-mcp-server/src"
      }
    }
  }
}
```

**Restart Claude Desktop** after updating the configuration.

---

### Configure ChatGPT Desktop App

ChatGPT Desktop also supports MCP servers. Add the Dorico MCP server to your configuration:

#### Windows

Edit `%LOCALAPPDATA%\com.openai.chat\mcp.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "C:\\path\\to\\dorico-mcp-server\\src",
      "env": {
        "PYTHONPATH": "C:\\path\\to\\dorico-mcp-server\\src"
      }
    }
  }
}
```

#### macOS

Edit `~/Library/Application Support/com.openai.chat/mcp.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python3",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python3",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "/Users/yourname/dorico-mcp-server/src",
      "env": {
        "PYTHONPATH": "/Users/yourname/dorico-mcp-server/src"
      }
    }
  }
}
```

#### Linux

Edit `~/.config/com.openai.chat/mcp.json`:

**If installed via pip:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"]
    }
  }
}
```

**If installed from source:**
```json
{
  "mcpServers": {
    "dorico": {
      "command": "python",
      "args": ["-m", "dorico_mcp.server", "--stdio"],
      "cwd": "/home/yourname/dorico-mcp-server/src",
      "env": {
        "PYTHONPATH": "/home/yourname/dorico-mcp-server/src"
      }
    }
  }
}
```

**Restart ChatGPT Desktop** after updating the configuration.

---

## Usage

### First Connection

1. **Start Dorico** and ensure Remote Control is enabled
2. **Open Claude Desktop** or **ChatGPT Desktop**
3. Ask the AI to connect:

```
Connect to Dorico
```

4. **Approve the connection** in Dorico (first time only)
   - A dialog will appear asking to allow the connection
   - Click "Allow" to permit the MCP server

### Example Commands

#### Create a Score

```
Create a new score for string quartet in G major, 3/4 time, tempo 120
```

#### Add Notes

```
Add a C major chord (C4, E4, G4) as quarter notes
```

```
Add a melody: C4, D4, E4, F4, G4 as eighth notes
```

#### Set Key Signature

```
Change the key to D minor
```

#### Add Dynamics

```
Add a forte marking
```

#### Orchestration Help

```
Is B1 playable on the cello?
```

```
What's the comfortable range for trumpet?
```

#### Harmony Suggestions

```
What chord would work well after I-IV-V?
```

```
Generate an 8-bar progression in A minor ending with an authentic cadence
```

### Available Tools

| Tool | Description |
|------|-------------|
| `connect_to_dorico` | Establish connection |
| `get_dorico_status` | Check current state |
| `create_score` | Create new score |
| `save_score` | Save current score |
| `export_score` | Export to PDF/MusicXML |
| `add_notes` | Add notes/chords |
| `add_rest` | Add rests |
| `set_key_signature` | Set key |
| `set_time_signature` | Set meter |
| `add_dynamics` | Add dynamics |
| `add_tempo` | Add tempo marking |
| `add_slur` | Add slur |
| `transpose` | Transpose selection |
| `go_to_bar` | Navigate to bar |
| `add_instrument` | Add instrument |
| `playback_control` | Play/stop/rewind |

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only (no dependencies needed)
pytest tests/test_commands.py tests/test_models.py -v

# Harmony analysis tests
pytest tests/test_harmony.py -v

# Instrument database tests
pytest tests/test_instruments.py -v

# E2E tests (uses mock Dorico server)
pytest tests/test_e2e.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=dorico_mcp --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Mock Server Standalone

For manual testing or debugging:

```bash
python -m tests.mock_dorico
```

This starts a mock Dorico server on `ws://localhost:4560`.

---

## Troubleshooting

### Connection Issues

#### "Could not find Dorico"

1. Ensure Dorico is running
2. Check that Remote Control is enabled in Dorico Preferences
3. Verify firewall isn't blocking port 4560

#### "Connection refused"

1. Dorico may be using a different port
2. Try ports 4560-4565
3. Check Dorico's application.log for the actual port

#### "Session approval required"

1. First connection requires manual approval in Dorico
2. Look for the approval dialog in Dorico
3. Click "Allow" to permit the connection

### Command Errors

#### "No score open"

Some commands require an open score. Create or open a score first:
```
Create a new piano score
```

#### "Invalid pitch format"

Use standard notation: Note name + octave
- Correct: `C4`, `F#5`, `Bb3`
- Wrong: `C`, `middle C`, `C-4`

### Python Environment Issues

#### "Module not found"

If installed via pip:
```bash
pip install dorico-mcp-server
```

If installed from source, ensure the virtual environment is activated:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### "Import error: mcp"

Reinstall dependencies:
```bash
pip install dorico-mcp-server
# Or if from source:
pip install -e ".[dev]"
```

### Claude Desktop Issues

#### "MCP server not found"

1. Check the path in `claude_desktop_config.json`
2. Use absolute paths, not relative (for source install)
3. Ensure Python is in your PATH
4. Try using the full path to python executable

#### "Server crashed"

Check the logs:
- macOS: `~/Library/Logs/Claude/`
- Windows: `%APPDATA%\Claude\logs\`
- Linux: `~/.config/Claude/logs/`

### ChatGPT Desktop Issues

#### "MCP server not found"

1. Check the path in `mcp.json`
2. Use absolute paths, not relative (for source install)
3. Ensure Python is in your PATH

#### "Server not responding"

1. Try restarting ChatGPT Desktop
2. Check that no other process is using the same port
3. Verify Dorico is running and Remote Control is enabled

---

## Development

### Project Structure

```
dorico-mcp-server/
├── src/dorico_mcp/
│   ├── __init__.py         # Package exports
│   ├── server.py           # MCP server with tools
│   ├── client.py           # Dorico WebSocket client
│   ├── commands.py         # Command builders
│   ├── models.py           # Data models
│   └── tools/
│       ├── __init__.py     # Harmony analysis
│       └── instruments.py  # Instrument database
├── tests/
│   ├── mock_dorico.py      # Mock Dorico server
│   ├── test_e2e.py         # E2E tests
│   ├── test_commands.py    # Command tests
│   ├── test_models.py      # Model tests
│   ├── test_harmony.py     # Harmony tests
│   └── test_instruments.py # Instrument tests
├── docs/
│   ├── FEATURE_SPEC.md     # Feature specification
│   └── SETUP_GUIDE.md      # This file
└── examples/
    └── claude_desktop_config.json
```

### Adding New Tools

1. Add command builder in `commands.py`
2. Add tool in `server.py` using `@mcp.tool()`
3. Add tests in appropriate test file
4. Update documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## Support

- **Issues**: [GitHub Issues](https://github.com/happycastle114/dorico-mcp-server/issues)
- **PyPI**: [dorico-mcp-server](https://pypi.org/project/dorico-mcp-server/)

---

Made with ❤️ for composition majors everywhere
