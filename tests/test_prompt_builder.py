"""Tests for the PromptBuilder — Phase 7.2 Prompt Engineering Framework.

Verifies that the production prompt contains all required sections,
maintains correct structure, and remains deterministic and
LLM-provider-independent.
"""

from app.planner.prompt_builder import (
    DEFAULT_SECTIONS,
    DefaultPromptBuilder,
    PromptSection,
    REQUIRED_SECTION_NAMES,
)


# ══════════════════════════════════════════════════════════════════
# Section Presence Tests
# ══════════════════════════════════════════════════════════════════


class TestRequiredSections:
    """Every required section must exist in the default prompt."""

    def test_system_role_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[SYSTEM ROLE]" in result

    def test_architecture_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[SENTINELAI ARCHITECTURE]" in result

    def test_available_tools_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[AVAILABLE TOOLS]" in result

    def test_available_intents_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[AVAILABLE INTENTS]" in result

    def test_parameter_rules_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[PARAMETER RULES]" in result

    def test_security_rules_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[SECURITY RULES]" in result

    def test_output_schema_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[OUTPUT JSON SCHEMA]" in result

    def test_positive_examples_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[POSITIVE EXAMPLES]" in result

    def test_negative_examples_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[NEGATIVE EXAMPLES]" in result

    def test_user_request_section_exists(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "[USER REQUEST]" in result

    def test_default_section_count(self):
        """There must be exactly 9 default sections."""
        assert len(DEFAULT_SECTIONS) == 9

    def test_required_section_names_match_defaults(self):
        """REQUIRED_SECTION_NAMES must match DEFAULT_SECTIONS."""
        names = {s.name for s in DEFAULT_SECTIONS}
        assert names == REQUIRED_SECTION_NAMES


# ══════════════════════════════════════════════════════════════════
# Section Content Tests
# ══════════════════════════════════════════════════════════════════


class TestSectionContent:
    """Verify critical content within sections."""

    def test_tools_lists_application(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "application" in result

    def test_tools_lists_filesystem(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "filesystem" in result

    def test_tools_lists_browser(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "browser" in result

    def test_tools_lists_llm(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "llm" in result

    def test_intents_lists_open_application(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "open_application" in result

    def test_intents_lists_read_file(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "read_file" in result

    def test_intents_lists_list_directory(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "list_directory" in result

    def test_intents_lists_open_url(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "open_url" in result

    def test_intents_lists_search_web(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "search_web" in result

    def test_intents_lists_chat(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert "chat" in result


# ══════════════════════════════════════════════════════════════════
# Security Rule Tests
# ══════════════════════════════════════════════════════════════════


class TestSecurityRules:
    """Verify the prompt contains explicit security instructions."""

    def test_never_invent_tools(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        assert "never invent tool" in result

    def test_never_invent_intents(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        assert "never invent intent" in result

    def test_no_explanations(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        assert "never output explanation" in result

    def test_no_code_fences(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        assert "code fences" in result

    def test_single_json_object(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        assert "exactly one json object" in result


# ══════════════════════════════════════════════════════════════════
# Output Schema Tests
# ══════════════════════════════════════════════════════════════════


class TestOutputSchema:
    """Verify the JSON schema section is correct."""

    def test_schema_contains_intent_field(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert '"intent"' in result

    def test_schema_contains_tool_field(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert '"tool"' in result

    def test_schema_contains_parameters_field(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert '"parameters"' in result

    def test_schema_section_appears_exactly_once(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        assert result.count("[OUTPUT JSON SCHEMA]") == 1


# ══════════════════════════════════════════════════════════════════
# Example Tests
# ══════════════════════════════════════════════════════════════════


class TestExamples:
    """Verify examples are present and well-formed."""

    def test_positive_examples_contain_json(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        # Positive examples must contain at least one valid intent
        idx = result.index("[POSITIVE EXAMPLES]")
        section = result[idx:]
        assert '"open_application"' in section

    def test_positive_examples_cover_all_intents(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        idx = result.index("[POSITIVE EXAMPLES]")
        section = result[idx:]
        for intent in [
            "open_application", "read_file", "list_directory",
            "open_url", "search_web", "chat",
        ]:
            assert intent in section, (
                f"Positive examples missing intent: {intent}"
            )

    def test_negative_examples_exist(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        idx = result.index("[NEGATIVE EXAMPLES]")
        section = result[idx:]
        assert "WRONG" in section

    def test_negative_examples_show_invented_intent(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        idx = result.index("[NEGATIVE EXAMPLES]")
        section = result[idx:]
        assert "download_file" in section

    def test_negative_examples_show_invented_tool(self):
        builder = DefaultPromptBuilder()
        result = builder.build("test")
        idx = result.index("[NEGATIVE EXAMPLES]")
        section = result[idx:]
        assert "gpt4" in section


# ══════════════════════════════════════════════════════════════════
# User Input Tests
# ══════════════════════════════════════════════════════════════════


class TestUserInput:
    """Verify user input is appended correctly."""

    def test_user_input_is_present(self):
        builder = DefaultPromptBuilder()
        result = builder.build("open the calculator")
        assert "open the calculator" in result

    def test_user_input_appears_after_all_sections(self):
        builder = DefaultPromptBuilder()
        result = builder.build("my unique request xyz123")
        assert result.endswith("my unique request xyz123")

    def test_user_request_header_appears_before_input(self):
        builder = DefaultPromptBuilder()
        result = builder.build("some input")
        header_idx = result.index("[USER REQUEST]")
        input_idx = result.index("some input")
        assert header_idx < input_idx

    def test_empty_user_input_still_builds(self):
        builder = DefaultPromptBuilder()
        result = builder.build("")
        assert isinstance(result, str)
        assert "[USER REQUEST]" in result


# ══════════════════════════════════════════════════════════════════
# Determinism Tests
# ══════════════════════════════════════════════════════════════════


class TestDeterminism:
    """The prompt must be deterministic and provider-independent."""

    def test_same_input_produces_same_output(self):
        builder = DefaultPromptBuilder()
        r1 = builder.build("test input")
        r2 = builder.build("test input")
        assert r1 == r2

    def test_different_inputs_produce_different_outputs(self):
        builder = DefaultPromptBuilder()
        r1 = builder.build("input A")
        r2 = builder.build("input B")
        assert r1 != r2

    def test_two_builders_produce_same_output(self):
        b1 = DefaultPromptBuilder()
        b2 = DefaultPromptBuilder()
        assert b1.build("test") == b2.build("test")

    def test_prompt_contains_no_provider_references(self):
        """The prompt must not mention specific LLM providers."""
        builder = DefaultPromptBuilder()
        result = builder.build("test").lower()
        for provider in ["ollama", "openai", "gpt-4", "claude", "gemini"]:
            assert provider not in result, (
                f"Prompt should not reference provider: {provider}"
            )


# ══════════════════════════════════════════════════════════════════
# Custom Section Injection Tests
# ══════════════════════════════════════════════════════════════════


class TestCustomSections:
    """Verify that sections can be overridden via DI."""

    def test_custom_sections_replace_defaults(self):
        custom = [
            PromptSection(name="CUSTOM", content="Custom content."),
        ]
        builder = DefaultPromptBuilder(sections=custom)
        result = builder.build("input")

        assert "[CUSTOM]" in result
        assert "Custom content." in result
        assert "[SYSTEM ROLE]" not in result

    def test_sections_property_returns_copy(self):
        builder = DefaultPromptBuilder()
        s1 = builder.sections
        s2 = builder.sections
        assert s1 is not s2
        assert s1 == s2

    def test_sections_count_matches_custom(self):
        custom = [
            PromptSection(name="A", content="aaa"),
            PromptSection(name="B", content="bbb"),
        ]
        builder = DefaultPromptBuilder(sections=custom)
        assert len(builder.sections) == 2


class TestPromptSection:
    """Tests for the PromptSection dataclass."""

    def test_fields_accessible(self):
        section = PromptSection(name="FOO", content="bar")
        assert section.name == "FOO"
        assert section.content == "bar"

    def test_is_frozen(self):
        section = PromptSection(name="FOO", content="bar")
        try:
            section.name = "BAZ"
            assert False, "PromptSection should be frozen"
        except AttributeError:
            pass
