"""Tests for input validation utilities.

This module tests all validation functions with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import pytest

from memorygraph.utils.validation import (
    validate_memory_input,
    validate_search_input,
    validate_relationship_input,
    ValidationError,
    MAX_TITLE_LENGTH,
    MAX_CONTENT_LENGTH,
    MAX_SUMMARY_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    MAX_QUERY_LENGTH,
    MAX_CONTEXT_LENGTH,
)


class TestValidateMemoryInput:
    """Tests for validate_memory_input function."""

    def test_valid_memory_input(self):
        """Test that valid input passes validation."""
        arguments = {
            "title": "Test Memory",
            "content": "This is a test memory content",
            "summary": "Test summary",
            "tags": ["test", "validation"],
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_empty_arguments(self):
        """Test that empty arguments pass validation."""
        # Should not raise any exception
        validate_memory_input({})

    def test_title_exceeds_max_length(self):
        """Test that overly long title raises ValidationError."""
        arguments = {
            "title": "x" * (MAX_TITLE_LENGTH + 1),
        }
        with pytest.raises(ValidationError, match=f"Title exceeds {MAX_TITLE_LENGTH} characters"):
            validate_memory_input(arguments)

    def test_title_at_max_length(self):
        """Test that title at exactly max length passes."""
        arguments = {
            "title": "x" * MAX_TITLE_LENGTH,
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_content_exceeds_max_length(self):
        """Test that overly long content raises ValidationError."""
        arguments = {
            "content": "x" * (MAX_CONTENT_LENGTH + 1),
        }
        with pytest.raises(ValidationError, match=f"Content exceeds {MAX_CONTENT_LENGTH} characters"):
            validate_memory_input(arguments)

    def test_content_at_max_length(self):
        """Test that content at exactly max length passes."""
        arguments = {
            "content": "x" * MAX_CONTENT_LENGTH,
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_summary_exceeds_max_length(self):
        """Test that overly long summary raises ValidationError."""
        arguments = {
            "summary": "x" * (MAX_SUMMARY_LENGTH + 1),
        }
        with pytest.raises(ValidationError, match=f"Summary exceeds {MAX_SUMMARY_LENGTH} characters"):
            validate_memory_input(arguments)

    def test_summary_at_max_length(self):
        """Test that summary at exactly max length passes."""
        arguments = {
            "summary": "x" * MAX_SUMMARY_LENGTH,
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_too_many_tags(self):
        """Test that too many tags raises ValidationError."""
        arguments = {
            "tags": [f"tag{i}" for i in range(MAX_TAGS_COUNT + 1)],
        }
        with pytest.raises(ValidationError, match=f"Too many tags \\(max {MAX_TAGS_COUNT}"):
            validate_memory_input(arguments)

    def test_max_tags_count(self):
        """Test that exactly max tags count passes."""
        arguments = {
            "tags": [f"tag{i}" for i in range(MAX_TAGS_COUNT)],
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_tag_exceeds_max_length(self):
        """Test that overly long tag raises ValidationError."""
        arguments = {
            "tags": ["x" * (MAX_TAG_LENGTH + 1)],
        }
        with pytest.raises(ValidationError, match=f"exceeds {MAX_TAG_LENGTH} characters"):
            validate_memory_input(arguments)

    def test_tag_at_max_length(self):
        """Test that tag at exactly max length passes."""
        arguments = {
            "tags": ["x" * MAX_TAG_LENGTH],
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_non_string_tag(self):
        """Test that non-string tag raises ValidationError."""
        arguments = {
            "tags": ["valid_tag", 123, "another_tag"],
        }
        with pytest.raises(ValidationError, match="Tag must be string"):
            validate_memory_input(arguments)

    def test_none_values_ignored(self):
        """Test that None values are ignored during validation."""
        arguments = {
            "title": None,
            "content": None,
            "summary": None,
            "tags": None,
        }
        # Should not raise any exception
        validate_memory_input(arguments)

    def test_empty_string_values_ignored(self):
        """Test that empty string values are ignored during validation."""
        arguments = {
            "title": "",
            "content": "",
            "summary": "",
        }
        # Should not raise any exception
        validate_memory_input(arguments)


class TestValidateSearchInput:
    """Tests for validate_search_input function."""

    def test_valid_search_input(self):
        """Test that valid search input passes validation."""
        arguments = {
            "query": "test search query",
        }
        # Should not raise any exception
        validate_search_input(arguments)

    def test_empty_arguments(self):
        """Test that empty arguments pass validation."""
        # Should not raise any exception
        validate_search_input({})

    def test_query_exceeds_max_length(self):
        """Test that overly long query raises ValidationError."""
        arguments = {
            "query": "x" * (MAX_QUERY_LENGTH + 1),
        }
        with pytest.raises(ValidationError, match=f"Query exceeds {MAX_QUERY_LENGTH} characters"):
            validate_search_input(arguments)

    def test_query_at_max_length(self):
        """Test that query at exactly max length passes."""
        arguments = {
            "query": "x" * MAX_QUERY_LENGTH,
        }
        # Should not raise any exception
        validate_search_input(arguments)

    def test_none_query_ignored(self):
        """Test that None query value is ignored."""
        arguments = {
            "query": None,
        }
        # Should not raise any exception
        validate_search_input(arguments)

    def test_empty_query_ignored(self):
        """Test that empty query string is ignored."""
        arguments = {
            "query": "",
        }
        # Should not raise any exception
        validate_search_input(arguments)


class TestValidateRelationshipInput:
    """Tests for validate_relationship_input function."""

    def test_valid_relationship_input(self):
        """Test that valid relationship input passes validation."""
        arguments = {
            "context": "This is a relationship context",
        }
        # Should not raise any exception
        validate_relationship_input(arguments)

    def test_empty_arguments(self):
        """Test that empty arguments pass validation."""
        # Should not raise any exception
        validate_relationship_input({})

    def test_context_exceeds_max_length(self):
        """Test that overly long context raises ValidationError."""
        arguments = {
            "context": "x" * (MAX_CONTEXT_LENGTH + 1),
        }
        with pytest.raises(ValidationError, match=f"Context exceeds {MAX_CONTEXT_LENGTH} characters"):
            validate_relationship_input(arguments)

    def test_context_at_max_length(self):
        """Test that context at exactly max length passes."""
        arguments = {
            "context": "x" * MAX_CONTEXT_LENGTH,
        }
        # Should not raise any exception
        validate_relationship_input(arguments)

    def test_none_context_ignored(self):
        """Test that None context value is ignored."""
        arguments = {
            "context": None,
        }
        # Should not raise any exception
        validate_relationship_input(arguments)

    def test_empty_context_ignored(self):
        """Test that empty context string is ignored."""
        arguments = {
            "context": "",
        }
        # Should not raise any exception
        validate_relationship_input(arguments)


class TestValidationErrorMessage:
    """Tests for ValidationError error messages."""

    def test_validation_error_is_value_error(self):
        """Test that ValidationError is a subclass of ValueError."""
        assert issubclass(ValidationError, ValueError)

    def test_validation_error_message(self):
        """Test that ValidationError preserves error messages."""
        message = "Test error message"
        error = ValidationError(message)
        assert str(error) == message
