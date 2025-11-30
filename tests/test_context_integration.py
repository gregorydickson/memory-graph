"""
Integration tests for context extraction in the full workflow.

This module tests that context extraction works end-to-end with the server
and database layers.
"""

import json
import pytest
from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
)
from memorygraph.utils.context_extractor import parse_context


class TestContextIntegrationWorkflow:
    """Test context extraction in full workflow."""

    def test_relationship_properties_stores_context(self):
        """Test that RelationshipProperties can store structured JSON context."""
        # Simulate what the server does
        user_context = "partially implements auth module, only works in production"

        # Extract structure
        from memorygraph.utils.context_extractor import extract_context_structure
        structure = extract_context_structure(user_context)
        structured_json = json.dumps(structure)

        # Store in RelationshipProperties
        props = RelationshipProperties(
            strength=0.7,
            confidence=0.9,
            context=structured_json
        )

        assert props.context is not None
        assert isinstance(props.context, str)

        # Parse back out
        parsed = parse_context(props.context)
        assert parsed["text"] == user_context
        assert parsed["scope"] == "partial"
        assert "auth module" in parsed["components"]
        assert len(parsed["conditions"]) > 0

    def test_backward_compatible_with_old_contexts(self):
        """Test that old free-text contexts still work."""
        # Old style: plain text
        old_context = "this is just plain text context"

        props = RelationshipProperties(
            strength=0.5,
            confidence=0.8,
            context=old_context
        )

        # Parse it
        parsed = parse_context(props.context)
        assert parsed["text"] == old_context

    def test_null_context_handling(self):
        """Test that null/None contexts are handled gracefully."""
        props = RelationshipProperties(
            strength=0.5,
            confidence=0.8,
            context=None
        )

        assert props.context is None

        # Parse it
        parsed = parse_context(props.context)
        assert parsed == {}

    def test_complex_real_world_context(self):
        """Test complex real-world context extraction."""
        context = """
        This solution partially addresses the authentication flow refactor
        completed in v2.1. It works reliably in staging and production
        environments but requires Redis to be available. Verified by
        integration tests and security audit.
        """

        from memorygraph.utils.context_extractor import extract_context_structure
        structure = extract_context_structure(context)
        structured_json = json.dumps(structure)

        props = RelationshipProperties(context=structured_json)

        # Parse and verify
        parsed = parse_context(props.context)
        assert parsed["scope"] == "partial"
        assert parsed["temporal"] is not None
        assert "v2.1" in parsed["temporal"]
        assert len(parsed["conditions"]) > 0
        assert len(parsed["evidence"]) > 0

    def test_json_serialization_roundtrip(self):
        """Test that structured context survives JSON serialization."""
        context = "verified by E2E tests, only works in production since v2.0"

        from memorygraph.utils.context_extractor import extract_context_structure
        structure = extract_context_structure(context)

        # Serialize to JSON string (what gets stored in DB)
        json_str = json.dumps(structure)

        # Parse back (what happens on retrieval)
        parsed = json.loads(json_str)

        assert parsed["text"] == context
        assert len(parsed["evidence"]) > 0
        assert len(parsed["conditions"]) > 0
        assert parsed["temporal"] is not None


class TestContextExtractionEdgeCases:
    """Test edge cases in context extraction integration."""

    def test_empty_string_context(self):
        """Test that empty string contexts are handled."""
        from memorygraph.utils.context_extractor import extract_context_structure

        structure = extract_context_structure("")
        json_str = json.dumps(structure)

        props = RelationshipProperties(context=json_str)
        parsed = parse_context(props.context)

        assert parsed["text"] == ""
        assert parsed["scope"] is None
        assert parsed["conditions"] == []

    def test_very_long_context(self):
        """Test that very long contexts don't break."""
        long_context = "implements authentication feature " * 50

        from memorygraph.utils.context_extractor import extract_context_structure
        structure = extract_context_structure(long_context)
        json_str = json.dumps(structure)

        props = RelationshipProperties(context=json_str)
        parsed = parse_context(props.context)

        assert parsed["text"] == long_context
        assert len(parsed["components"]) > 0

    def test_special_characters_in_context(self):
        """Test that special characters are preserved."""
        context = "supports UTF-8 & JSON parsing (verified by tests)"

        from memorygraph.utils.context_extractor import extract_context_structure
        structure = extract_context_structure(context)
        json_str = json.dumps(structure)

        props = RelationshipProperties(context=json_str)
        parsed = parse_context(props.context)

        assert parsed["text"] == context
        assert len(parsed["evidence"]) > 0


class TestBackwardCompatibilityScenarios:
    """Test backward compatibility scenarios."""

    def test_old_database_record_with_free_text(self):
        """Simulate reading an old database record with free-text context."""
        # Simulate old DB record with plain text context
        old_db_context = "connects authentication with user management"

        props = RelationshipProperties(context=old_db_context)

        # Parse it (should work without errors)
        parsed = parse_context(props.context)

        # Should extract structure from the free text
        assert parsed["text"] == old_db_context
        assert isinstance(parsed["components"], list)

    def test_new_database_record_with_json(self):
        """Simulate reading a new database record with JSON context."""
        # Simulate new DB record with JSON context
        new_structure = {
            "text": "partial implementation",
            "scope": "partial",
            "components": ["auth"],
            "conditions": [],
            "evidence": [],
            "temporal": None,
            "exceptions": []
        }
        new_db_context = json.dumps(new_structure)

        props = RelationshipProperties(context=new_db_context)

        # Parse it
        parsed = parse_context(props.context)

        assert parsed["scope"] == "partial"
        assert parsed["components"] == ["auth"]

    def test_mixed_database_contexts(self):
        """Test that we can handle both old and new contexts in same session."""
        old_context = "legacy free text"
        new_context = json.dumps({
            "text": "new structured",
            "scope": "full",
            "components": [],
            "conditions": [],
            "evidence": [],
            "temporal": None,
            "exceptions": []
        })

        old_props = RelationshipProperties(context=old_context)
        new_props = RelationshipProperties(context=new_context)

        old_parsed = parse_context(old_props.context)
        new_parsed = parse_context(new_props.context)

        assert old_parsed["text"] == "legacy free text"
        assert new_parsed["scope"] == "full"
