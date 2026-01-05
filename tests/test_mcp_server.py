"""Tests for MCP server configuration and tool definitions."""

import pytest

from dorico_mcp.server import create_server


class TestMCPServerConfiguration:
    """Tests for MCP server setup."""

    def test_server_creation(self):
        mcp = create_server()
        assert mcp is not None
        assert mcp.name == "dorico-mcp-server"

    def test_server_has_instructions(self):
        mcp = create_server()
        assert mcp.instructions is not None
        assert "Dorico" in mcp.instructions
        assert "API LIMITATIONS" in mcp.instructions


class TestMCPToolDefinitions:
    """Tests for MCP tool definitions and descriptions."""

    @pytest.fixture
    def mcp(self):
        return create_server()

    def test_connection_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "connect_to_dorico" in tool_names
        assert "get_dorico_status" in tool_names

    def test_score_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "create_score" in tool_names
        assert "save_score" in tool_names
        assert "export_score" in tool_names

    def test_note_input_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "add_notes" in tool_names
        assert "add_rest" in tool_names

    def test_notation_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "set_key_signature" in tool_names
        assert "set_time_signature" in tool_names
        assert "add_dynamics" in tool_names
        assert "add_tempo" in tool_names

    def test_new_query_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "get_flows" in tool_names
        assert "get_layouts" in tool_names
        assert "get_selection_properties" in tool_names

    def test_options_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "get_engraving_options" in tool_names
        assert "get_layout_options" in tool_names
        assert "get_notation_options" in tool_names

    def test_harmony_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "analyze_chord" in tool_names
        assert "suggest_next_chord" in tool_names
        assert "check_voice_leading" in tool_names
        assert "generate_chord_progression" in tool_names

    def test_orchestration_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "check_instrument_range" in tool_names
        assert "get_instrument_info" in tool_names

    def test_counterpoint_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "check_species_rules" in tool_names
        assert "generate_counterpoint" in tool_names

    def test_validation_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "validate_voice_leading" in tool_names
        assert "check_enharmonic" in tool_names
        assert "analyze_intervals" in tool_names
        assert "check_playability" in tool_names
        assert "validate_score" in tool_names

    def test_harmony_advanced_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "detect_parallel_motion" in tool_names
        assert "transpose_for_instrument" in tool_names
        assert "realize_figured_bass" in tool_names

    def test_new_medium_priority_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "suggest_cadence" in tool_names
        assert "suggest_doubling" in tool_names
        assert "find_dissonances" in tool_names
        assert "suggest_instrumentation" in tool_names

    def test_low_priority_tools_exist(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "balance_dynamics" in tool_names
        assert "check_beaming" in tool_names
        assert "check_spacing" in tool_names

    def test_score_tools_complete(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "open_score" in tool_names
        assert "create_score" in tool_names
        assert "save_score" in tool_names
        assert "export_score" in tool_names

    def test_notation_tools_complete(self, mcp):
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "add_articulation" in tool_names
        assert "add_text" in tool_names
        assert "add_slur" in tool_names
        assert "delete_notes" in tool_names
        assert "remove_instrument" in tool_names


class TestMCPPromptDefinitions:
    """Tests for MCP prompt definitions."""

    @pytest.fixture
    def mcp(self):
        return create_server()

    def test_prompts_exist(self, mcp):
        prompt_names = list(mcp._prompt_manager._prompts.keys())
        assert "harmonize_melody" in prompt_names
        assert "orchestration_basics" in prompt_names
        assert "species_counterpoint" in prompt_names
        assert "chord_progression_workshop" in prompt_names
        assert "score_review" in prompt_names

    def test_harmonize_melody_content(self, mcp):
        prompt = mcp._prompt_manager._prompts["harmonize_melody"]
        result = prompt.fn()
        assert "Voice Leading" in result
        assert "parallel 5ths" in result

    def test_orchestration_basics_content(self, mcp):
        prompt = mcp._prompt_manager._prompts["orchestration_basics"]
        result = prompt.fn()
        assert "Woodwinds" in result or "Strings" in result
        assert "dorico://instruments/ranges" in result

    def test_species_counterpoint_content(self, mcp):
        prompt = mcp._prompt_manager._prompts["species_counterpoint"]
        result = prompt.fn()
        assert "First Species" in result
        assert "consonance" in result.lower()

    def test_chord_progression_workshop_content(self, mcp):
        prompt = mcp._prompt_manager._prompts["chord_progression_workshop"]
        result = prompt.fn()
        assert "Chord Progression" in result
        assert "suggest_cadence" in result

    def test_score_review_content(self, mcp):
        prompt = mcp._prompt_manager._prompts["score_review"]
        result = prompt.fn()
        assert "Range Check" in result
        assert "find_dissonances" in result


class TestMCPResourceDefinitions:
    """Tests for MCP resource definitions."""

    @pytest.fixture
    def mcp(self):
        return create_server()

    def test_resources_exist(self, mcp):
        resources = list(mcp._resource_manager._resources.keys())
        assert "dorico://status" in resources
        assert "dorico://instruments/list" in resources
        assert "dorico://instruments/ranges" in resources
        assert "dorico://score/info" in resources
        assert "dorico://score/selection" in resources

    def test_instrument_list_resource(self, mcp):
        resource = mcp._resource_manager._resources["dorico://instruments/list"]
        result = resource.fn()
        assert "Violin" in result or "violin" in result.lower()

    def test_instrument_ranges_resource(self, mcp):
        resource = mcp._resource_manager._resources["dorico://instruments/ranges"]
        result = resource.fn()
        assert "Woodwinds" in result
        assert "Brass" in result
        assert "Strings" in result


class TestCachingFunctions:

    def test_instrument_info_cached(self):
        from dorico_mcp.server import _get_instrument_info_cached

        result1 = _get_instrument_info_cached("violin")
        result2 = _get_instrument_info_cached("violin")
        assert result1 == result2
        assert result1["found"] is True

    def test_instrument_info_not_found_cached(self):
        from dorico_mcp.server import _get_instrument_info_cached

        result = _get_instrument_info_cached("unknown_instrument_xyz")
        assert result["found"] is False

    def test_cache_utilities(self):
        from dorico_mcp.server import _clear_cache, _get_cached, _set_cached

        _clear_cache()
        assert _get_cached("test_key") is None

        _set_cached("test_key", {"value": 42})
        result = _get_cached("test_key")
        assert result == {"value": 42}

        _clear_cache()
        assert _get_cached("test_key") is None
