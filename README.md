# Dorico MCP Server

🎵 **Control Dorico via Claude Desktop or ChatGPT** - A gift for composition majors

[![PyPI version](https://badge.fury.io/py/dorico-mcp-server.svg)](https://badge.fury.io/py/dorico-mcp-server)
[![CI](https://github.com/happycastle114/dorico-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/happycastle114/dorico-mcp-server/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This MCP (Model Context Protocol) server enables natural language control of Steinberg Dorico music notation software through Claude Desktop or ChatGPT Desktop.

## Features

### 🎹 Core Score Tools
- Create new scores with custom instruments
- Save and export scores (PDF, MusicXML)
- Navigate through the score

### 🎼 Note Input
- Add notes with pitch, duration, and articulation
- Create chords
- Add rests and ties

### 📝 Notation
- Set key signatures (all major and minor keys)
- Set time signatures
- Add dynamics (pp, p, mp, mf, f, ff, etc.)
- Add tempo markings
- Add slurs and articulations

### 🎵 Harmony Tools (화성학)
- Analyze chord quality and Roman numerals
- Suggest next chords based on context
- Generate chord progressions
- Check voice leading rules (parallel 5ths/8ves)

### 🎻 Orchestration Tools (오케스트레이션)
- Complete instrument database with ranges
- Check playability (instrument range validation)
- Transposition for transposing instruments
- Get detailed instrument information

### 🔍 Query Tools
- Get flows, layouts, and selection properties
- Access engraving, layout, and notation options

### 📋 Guided Workflows (Prompts)
- Harmonize a melody
- Orchestrate piano scores
- Species counterpoint exercises

## Installation

### Prerequisites
- Python 3.11+
- Steinberg Dorico (with Remote Control enabled)
- Claude Desktop or ChatGPT Desktop

### Install from PyPI (Recommended)

```bash
pip install dorico-mcp-server
```

### Install from Source (Development)

```bash
git clone https://github.com/happycastle114/dorico-mcp-server.git
cd dorico-mcp-server
pip install -e ".[dev]"
```

### Enable Dorico Remote Control

1. Open Dorico
2. Go to **Preferences** → **General**
3. Enable **Allow remote control**
4. Note the port number (usually 4560)

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

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

### ChatGPT Desktop

Add to your ChatGPT Desktop configuration:

**macOS**: `~/Library/Application Support/com.openai.chat/mcp.json`
**Windows**: `%LOCALAPPDATA%\com.openai.chat\mcp.json`
**Linux**: `~/.config/com.openai.chat/mcp.json`

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

> **Note**: Restart the app after updating the configuration.

## Usage Examples

### Creating a Score

```
"Create a new score for string quartet in G major, 3/4 time, tempo 120"
```

### Adding Notes

```
"Add a C major chord (C4, E4, G4) as quarter notes"
"Add a melody: C4, D4, E4, F4, G4 as eighth notes"
```

### Harmony Analysis

```
"What chord would work well after I-IV-V?"
"Generate a 8-bar chord progression in A minor with an authentic cadence"
```

### Orchestration Help

```
"Is F2 playable on the violin?"
"What's the comfortable range for French horn?"
"What transposition does the Bb clarinet use?"
```

### Counterpoint

```
"Check if this counterpoint follows first species rules: 
  Cantus: C4, D4, E4, F4, E4, D4, C4
  Counterpoint: G4, A4, B4, C5, B4, A4, G4"
"Generate a counterpoint melody above this cantus firmus: D4, E4, F4, G4, F4, E4, D4"
```

### Voice Leading Validation

```
"Check this four-part harmony for parallel fifths:
  Soprano: C5, D5, E5
  Alto: E4, F4, G4
  Tenor: G3, A3, B3
  Bass: C3, D3, E3"
```

## Available Tools (51)

| Category | Tools |
|----------|-------|
| **Connection** | `connect_to_dorico`, `get_dorico_status` |
| **Score** | `create_score`, `open_score`, `save_score`, `export_score` |
| **Notes** | `add_notes`, `add_rest`, `add_slur`, `delete_notes` |
| **Notation** | `set_key_signature`, `set_time_signature`, `add_dynamics`, `add_tempo`, `add_articulation`, `add_text` |
| **Navigation** | `go_to_bar`, `add_instrument`, `remove_instrument` |
| **Transpose** | `transpose`, `transpose_octave`, `transpose_for_instrument` |
| **Playback** | `playback_control` |
| **Harmony** | `analyze_chord`, `suggest_next_chord`, `check_voice_leading`, `generate_chord_progression`, `realize_figured_bass`, `suggest_cadence` |
| **Orchestration** | `check_instrument_range`, `get_instrument_info`, `suggest_doubling`, `suggest_instrumentation`, `balance_dynamics` |
| **Counterpoint** | `check_species_rules`, `generate_counterpoint` |
| **Analysis** | `analyze_intervals`, `check_playability`, `validate_score`, `detect_parallel_motion`, `find_dissonances` |
| **Validation** | `validate_voice_leading`, `check_enharmonic` |
| **Proofreading** | `check_beaming`, `check_spacing` |
| **Query** | `get_flows`, `get_layouts`, `get_selection_properties`, `get_engraving_options`, `get_layout_options`, `get_notation_options` |

## Development

### Run tests

```bash
pytest
```

### Type checking

```bash
mypy src/dorico_mcp
```

### Linting

```bash
ruff check src/dorico_mcp
```

## Architecture

```
dorico-mcp-server/
├── src/dorico_mcp/
│   ├── __init__.py         # Package exports
│   ├── server.py           # FastMCP server with tools/resources/prompts
│   ├── client.py           # Dorico WebSocket client
│   ├── commands.py         # Dorico command builders (pure functions)
│   ├── models.py           # Pydantic models
│   └── tools/
│       ├── __init__.py     # Harmony analysis
│       └── instruments.py  # Instrument database
├── tests/                  # Pytest tests
├── docs/                   # Documentation
└── examples/               # Usage examples
```

## Dorico Remote Control API

This server communicates with Dorico via its WebSocket-based Remote Control API:

- **Protocol**: WebSocket (JSON messages)
- **Port**: Dynamic (usually 4560-4565)
- **Authentication**: Session token (stored locally after first approval)

### Key Limitations

- **Read access is limited**: Can only read currently selected items
- **Write-focused**: Best for sending commands/input
- **Full score reading**: Requires MusicXML export

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License

## Acknowledgments

- [AbletonMCP](https://github.com/ahujasid/ableton-mcp) - Inspiration for MCP structure
- [MuseScore-MCP](https://github.com/JordanSucher/musescore-mcp) - Notation MCP reference
- [Dorico.Net](https://github.com/scott-janssens/Dorico.Net) - Dorico API documentation
- [music21](https://web.mit.edu/music21/) - Music theory analysis

---

Made with ❤️ for composition majors everywhere
