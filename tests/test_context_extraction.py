"""
Tests for context extraction functionality.

This module tests the pattern-based extraction of structured information
from natural language relationship contexts.
"""

import json
import pytest
from memorygraph.utils.context_extractor import (
    extract_context_structure,
    parse_context,
    _extract_scope,
    _extract_conditions,
    _extract_evidence,
    _extract_temporal,
    _extract_exceptions,
    _extract_components,
)


class TestScopeExtraction:
    """Test scope pattern detection."""

    def test_extract_partial_scope(self):
        """Test detection of 'partial' scope."""
        result = extract_context_structure("partially implements auth module")
        assert result["scope"] == "partial"
        assert result["text"] == "partially implements auth module"

    def test_extract_full_scope(self):
        """Test detection of 'full' scope."""
        result = extract_context_structure("fully supports payment processing")
        assert result["scope"] == "full"

    def test_extract_complete_scope(self):
        """Test detection of 'complete' scope."""
        result = extract_context_structure("complete implementation of OAuth")
        assert result["scope"] == "full"

    def test_extract_conditional_scope(self):
        """Test detection of 'conditional' scope."""
        result = extract_context_structure("conditional support for legacy mode")
        assert result["scope"] == "conditional"

    def test_extract_only_scope(self):
        """Test detection of 'only' as conditional scope."""
        result = extract_context_structure("only works in production")
        assert result["scope"] == "conditional"

    def test_extract_limited_scope(self):
        """Test detection of 'limited' as partial scope."""
        result = extract_context_structure("limited support for API v1")
        assert result["scope"] == "partial"

    def test_no_scope_pattern(self):
        """Test text with no scope pattern."""
        result = extract_context_structure("works with database layer")
        assert result["scope"] is None


class TestConditionsExtraction:
    """Test condition pattern detection."""

    def test_extract_when_condition(self):
        """Test 'when' condition pattern."""
        result = extract_context_structure("works when database is available")
        assert len(result["conditions"]) > 0
        assert "database is available" in result["conditions"][0].lower()

    def test_extract_if_condition(self):
        """Test 'if' condition pattern."""
        result = extract_context_structure("only if Redis is configured")
        assert len(result["conditions"]) > 0
        assert "redis is configured" in result["conditions"][0].lower()

    def test_extract_in_environment_condition(self):
        """Test 'in X environment' pattern."""
        result = extract_context_structure("only works in production environment")
        assert len(result["conditions"]) > 0
        assert "production" in result["conditions"][0].lower()

    def test_extract_requires_condition(self):
        """Test 'requires' pattern."""
        result = extract_context_structure("requires PostgreSQL 12+")
        assert len(result["conditions"]) > 0
        assert "postgresql 12+" in result["conditions"][0].lower()

    def test_multiple_conditions(self):
        """Test extraction of multiple conditions."""
        result = extract_context_structure(
            "works when auth is enabled and requires Redis in production"
        )
        assert len(result["conditions"]) >= 2

    def test_no_conditions(self):
        """Test text with no conditions."""
        result = extract_context_structure("implements user authentication")
        assert result["conditions"] == []


class TestEvidenceExtraction:
    """Test evidence pattern detection."""

    def test_extract_verified_by(self):
        """Test 'verified by' pattern."""
        result = extract_context_structure("verified by integration tests")
        assert len(result["evidence"]) > 0
        assert "integration tests" in result["evidence"][0].lower()

    def test_extract_tested_by(self):
        """Test 'tested by' pattern."""
        result = extract_context_structure("tested by E2E test suite")
        assert len(result["evidence"]) > 0
        assert "e2e test suite" in result["evidence"][0].lower()

    def test_extract_proven_by(self):
        """Test 'proven by' pattern."""
        result = extract_context_structure("proven by load testing results")
        assert len(result["evidence"]) > 0
        assert "load testing results" in result["evidence"][0].lower()

    def test_extract_observed_in(self):
        """Test 'observed in' pattern."""
        result = extract_context_structure("observed in production monitoring")
        assert len(result["evidence"]) > 0
        assert "production monitoring" in result["evidence"][0].lower()

    def test_no_evidence(self):
        """Test text with no evidence."""
        result = extract_context_structure("implements authentication flow")
        assert result["evidence"] == []


class TestTemporalExtraction:
    """Test temporal pattern detection."""

    def test_extract_version_pattern(self):
        """Test version pattern extraction."""
        result = extract_context_structure("implemented in v2.1.0")
        assert result["temporal"] is not None
        assert "v2.1.0" in result["temporal"]

    def test_extract_version_without_v_prefix(self):
        """Test version pattern without 'v' prefix."""
        result = extract_context_structure("added in version 3.0.1")
        assert result["temporal"] is not None
        assert "3.0.1" in result["temporal"]

    def test_extract_since_pattern(self):
        """Test 'since' temporal pattern."""
        result = extract_context_structure("available since June 2024")
        assert result["temporal"] is not None
        assert "june 2024" in result["temporal"].lower()

    def test_extract_after_pattern(self):
        """Test 'after' temporal pattern."""
        result = extract_context_structure("after migration to PostgreSQL")
        assert result["temporal"] is not None
        assert "migration to postgresql" in result["temporal"].lower()

    def test_extract_as_of_pattern(self):
        """Test 'as of' temporal pattern."""
        result = extract_context_structure("as of release 2.0")
        assert result["temporal"] is not None
        assert "release 2.0" in result["temporal"].lower()

    def test_no_temporal_info(self):
        """Test text with no temporal information."""
        result = extract_context_structure("implements caching layer")
        assert result["temporal"] is None


class TestExceptionsExtraction:
    """Test exception pattern detection."""

    def test_extract_except_pattern(self):
        """Test 'except' exception pattern."""
        result = extract_context_structure("supports all formats except XML")
        assert len(result["exceptions"]) > 0
        assert "xml" in result["exceptions"][0].lower()

    def test_extract_excluding_pattern(self):
        """Test 'excluding' exception pattern."""
        result = extract_context_structure("works everywhere excluding Safari")
        assert len(result["exceptions"]) > 0
        assert "safari" in result["exceptions"][0].lower()

    def test_extract_but_not_pattern(self):
        """Test 'but not' exception pattern."""
        result = extract_context_structure("handles all errors but not timeouts")
        assert len(result["exceptions"]) > 0
        assert "timeouts" in result["exceptions"][0].lower()

    def test_extract_without_pattern(self):
        """Test 'without' exception pattern."""
        result = extract_context_structure("operates without transaction support")
        assert len(result["exceptions"]) > 0
        assert "transaction support" in result["exceptions"][0].lower()

    def test_no_exceptions(self):
        """Test text with no exceptions."""
        result = extract_context_structure("fully supports all features")
        assert result["exceptions"] == []


class TestComponentsExtraction:
    """Test component extraction."""

    def test_extract_single_component(self):
        """Test extraction of single component."""
        result = extract_context_structure("implements auth module")
        assert len(result["components"]) > 0
        assert "auth module" in result["components"]

    def test_extract_multiple_components(self):
        """Test extraction of multiple components."""
        result = extract_context_structure(
            "connects auth module with payment service"
        )
        assert len(result["components"]) >= 2

    def test_extract_hyphenated_components(self):
        """Test extraction of hyphenated component names."""
        result = extract_context_structure("uses two-factor authentication")
        components_text = " ".join(result["components"]).lower()
        assert "authentication" in components_text or "two-factor" in components_text

    def test_extract_technical_terms(self):
        """Test extraction of technical terms as components."""
        result = extract_context_structure("integrates with PostgreSQL database")
        components_text = " ".join(result["components"]).lower()
        assert "postgresql" in components_text or "database" in components_text


class TestComplexPatterns:
    """Test extraction of complex multi-pattern contexts."""

    def test_complex_multi_pattern(self):
        """Test complex context with multiple patterns."""
        text = "partially implements auth module, only works in production, verified by E2E tests"
        result = extract_context_structure(text)

        assert result["scope"] == "partial"
        assert "auth module" in result["components"]
        assert len(result["conditions"]) > 0
        assert "production" in result["conditions"][0].lower()
        assert len(result["evidence"]) > 0
        assert "e2e tests" in result["evidence"][0].lower()

    def test_very_complex_pattern(self):
        """Test very complex context with all pattern types."""
        text = """
        This solution partially addresses the authentication flow refactor
        completed in v2.1. It works reliably in staging and production
        environments but requires Redis to be available. Testing shows
        it handles edge cases well, except for SSO logout scenarios
        which are tracked separately.
        """
        result = extract_context_structure(text)

        assert result["scope"] == "partial"
        assert result["temporal"] is not None
        assert "v2.1" in result["temporal"]
        assert len(result["conditions"]) > 0
        assert len(result["exceptions"]) > 0

    def test_technical_context(self):
        """Test technical context with specific details."""
        text = "implements JWT token validation, requires openssl 1.1+, tested by security audit"
        result = extract_context_structure(text)

        assert len(result["conditions"]) > 0
        assert len(result["evidence"]) > 0
        assert len(result["components"]) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_context(self):
        """Test extraction from empty string."""
        result = extract_context_structure("")
        assert result["text"] == ""
        assert result["scope"] is None
        assert result["conditions"] == []
        assert result["evidence"] == []
        assert result["temporal"] is None
        assert result["exceptions"] == []

    def test_none_context(self):
        """Test extraction from None value."""
        result = extract_context_structure(None)
        assert result == {}

    def test_whitespace_only_context(self):
        """Test extraction from whitespace-only string."""
        result = extract_context_structure("   \n\t   ")
        assert result["text"].strip() == ""

    def test_very_long_context(self):
        """Test extraction from very long context (>500 chars)."""
        long_text = "implements feature " * 100  # ~1800 chars
        result = extract_context_structure(long_text)
        assert result["text"] == long_text
        assert len(result["components"]) > 0

    def test_special_characters(self):
        """Test extraction with special characters."""
        text = "supports UTF-8 encoding & JSON parsing (verified by tests)"
        result = extract_context_structure(text)
        assert result["text"] == text
        assert len(result["evidence"]) > 0

    def test_no_extractable_patterns(self):
        """Test context with no extractable patterns."""
        result = extract_context_structure("this is just some random text")
        assert result["text"] == "this is just some random text"
        assert result["scope"] is None
        assert result["conditions"] == []
        assert result["evidence"] == []
        assert result["temporal"] is None
        assert result["exceptions"] == []
        assert isinstance(result["components"], list)


class TestBackwardCompatibility:
    """Test backward compatibility with existing contexts."""

    def test_parse_old_free_text_context(self):
        """Test parsing of old free-text contexts."""
        old_context = "this is legacy free text"
        parsed = parse_context(old_context)
        assert parsed["text"] == old_context

    def test_parse_new_json_context(self):
        """Test parsing of new JSON contexts."""
        new_context = '{"text": "partial impl", "scope": "partial"}'
        parsed = parse_context(new_context)
        assert parsed["scope"] == "partial"
        assert parsed["text"] == "partial impl"

    def test_parse_json_with_all_fields(self):
        """Test parsing of JSON context with all fields."""
        json_context = {
            "text": "test context",
            "scope": "partial",
            "components": ["auth"],
            "conditions": ["production"],
            "evidence": ["tests"],
            "temporal": "v2.0",
            "exceptions": ["SSO"]
        }
        json_str = json.dumps(json_context)
        parsed = parse_context(json_str)
        assert parsed["scope"] == "partial"
        assert parsed["components"] == ["auth"]
        assert parsed["conditions"] == ["production"]

    def test_parse_malformed_json_fallback(self):
        """Test that malformed JSON falls back to extraction."""
        malformed = '{"text": "incomplete'
        parsed = parse_context(malformed)
        # Should fall back to extraction
        assert "text" in parsed
        assert parsed["text"] == malformed

    def test_parse_none_context(self):
        """Test parsing of None context."""
        parsed = parse_context(None)
        assert parsed == {}

    def test_parse_empty_string_context(self):
        """Test parsing of empty string context."""
        parsed = parse_context("")
        assert parsed == {}


class TestHelperFunctions:
    """Test individual helper functions."""

    def test_extract_scope_helper(self):
        """Test _extract_scope helper function."""
        assert _extract_scope("partially implements") == "partial"
        assert _extract_scope("fully supports") == "full"
        assert _extract_scope("complete implementation") == "full"
        assert _extract_scope("conditional support") == "conditional"
        assert _extract_scope("no scope here") is None

    def test_extract_conditions_helper(self):
        """Test _extract_conditions helper function."""
        conditions = _extract_conditions("when X and if Y")
        assert len(conditions) >= 1

        conditions = _extract_conditions("no conditions")
        assert conditions == []

    def test_extract_evidence_helper(self):
        """Test _extract_evidence helper function."""
        evidence = _extract_evidence("verified by tests")
        assert len(evidence) > 0

        evidence = _extract_evidence("no evidence")
        assert evidence == []

    def test_extract_temporal_helper(self):
        """Test _extract_temporal helper function."""
        assert _extract_temporal("in v2.1.0") is not None
        assert _extract_temporal("since 2024") is not None
        assert _extract_temporal("no temporal info") is None

    def test_extract_exceptions_helper(self):
        """Test _extract_exceptions helper function."""
        exceptions = _extract_exceptions("except XML")
        assert len(exceptions) > 0

        exceptions = _extract_exceptions("no exceptions")
        assert exceptions == []

    def test_extract_components_helper(self):
        """Test _extract_components helper function."""
        components = _extract_components("auth module and payment service")
        assert len(components) > 0
        # Components list should contain noun phrases


class TestStructureFormat:
    """Test the structure format of extracted data."""

    def test_result_has_all_required_fields(self):
        """Test that result contains all required fields."""
        result = extract_context_structure("test context")
        assert "text" in result
        assert "scope" in result
        assert "components" in result
        assert "conditions" in result
        assert "evidence" in result
        assert "temporal" in result
        assert "exceptions" in result

    def test_result_field_types(self):
        """Test that result fields have correct types."""
        result = extract_context_structure("partial impl in v2.0 verified by tests")
        assert isinstance(result["text"], str)
        assert result["scope"] is None or isinstance(result["scope"], str)
        assert isinstance(result["components"], list)
        assert isinstance(result["conditions"], list)
        assert isinstance(result["evidence"], list)
        assert result["temporal"] is None or isinstance(result["temporal"], str)
        assert isinstance(result["exceptions"], list)

    def test_json_serializable(self):
        """Test that extracted structure is JSON serializable."""
        result = extract_context_structure("partial impl verified by tests")
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            # Should be able to parse it back
            parsed = json.loads(json_str)
            assert parsed["text"] == result["text"]
        except (TypeError, ValueError):
            pytest.fail("Extracted structure is not JSON serializable")


class TestTokenEfficiency:
    """Test token efficiency considerations."""

    def test_structured_storage_size(self):
        """Test that structured format is reasonable in size."""
        text = "partially implements auth module, only works in production"
        result = extract_context_structure(text)
        json_str = json.dumps(result)

        # JSON should be larger than original but not excessively so
        # Expected: ~8-13 tokens overhead (roughly 2-4x character size due to JSON structure)
        assert len(json_str) < len(text) * 5  # Sanity check: not more than 5x

    def test_minimal_structure_for_simple_text(self):
        """Test that simple text produces minimal structure."""
        text = "simple context"
        result = extract_context_structure(text)

        # Should have text and empty/None fields
        assert result["text"] == text
        assert result["scope"] is None
        assert result["conditions"] == []
        assert result["evidence"] == []
        assert result["temporal"] is None
        assert result["exceptions"] == []


class TestRealWorldExamples:
    """Test with real-world example contexts."""

    def test_example_auth_implementation(self):
        """Test realistic auth implementation context."""
        text = "partially implements OAuth2 flow, requires Redis for session storage, verified by security tests"
        result = extract_context_structure(text)

        assert result["scope"] == "partial"
        assert any("oauth" in c.lower() for c in result["components"])
        assert len(result["conditions"]) > 0
        assert len(result["evidence"]) > 0

    def test_example_bug_fix(self):
        """Test realistic bug fix context."""
        text = "fixes memory leak in worker threads, tested in production since v2.3.1"
        result = extract_context_structure(text)

        assert len(result["components"]) > 0
        assert result["temporal"] is not None
        assert "v2.3.1" in result["temporal"]

    def test_example_feature_limitation(self):
        """Test realistic feature limitation context."""
        text = "supports all database types except MongoDB, conditional on connection pooling"
        result = extract_context_structure(text)

        assert len(result["exceptions"]) > 0
        assert "mongodb" in result["exceptions"][0].lower()
        assert result["scope"] == "conditional"

    def test_example_minimal_context(self):
        """Test minimal real-world context."""
        text = "works with caching layer"
        result = extract_context_structure(text)

        assert result["text"] == text
        assert len(result["components"]) > 0
