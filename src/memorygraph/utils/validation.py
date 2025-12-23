"""Input validation utilities for tool handlers."""
from typing import Any, Dict

# Size limits
MAX_TITLE_LENGTH = 500
MAX_CONTENT_LENGTH = 50_000  # 50KB
MAX_SUMMARY_LENGTH = 1_000
MAX_TAG_LENGTH = 100
MAX_TAGS_COUNT = 50
MAX_QUERY_LENGTH = 1_000
MAX_CONTEXT_LENGTH = 10_000  # 10KB

class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass

def validate_memory_input(arguments: Dict[str, Any]) -> None:
    """Validate memory input arguments. Raises ValidationError on failure."""
    if "title" in arguments and arguments["title"]:
        if len(arguments["title"]) > MAX_TITLE_LENGTH:
            raise ValidationError(f"Title exceeds {MAX_TITLE_LENGTH} characters (got {len(arguments['title'])})")

    if "content" in arguments and arguments["content"]:
        if len(arguments["content"]) > MAX_CONTENT_LENGTH:
            raise ValidationError(f"Content exceeds {MAX_CONTENT_LENGTH} characters (got {len(arguments['content'])})")

    if "summary" in arguments and arguments["summary"]:
        if len(arguments["summary"]) > MAX_SUMMARY_LENGTH:
            raise ValidationError(f"Summary exceeds {MAX_SUMMARY_LENGTH} characters")

    if "tags" in arguments and arguments["tags"]:
        tags = arguments["tags"]
        if len(tags) > MAX_TAGS_COUNT:
            raise ValidationError(f"Too many tags (max {MAX_TAGS_COUNT}, got {len(tags)})")
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError(f"Tag must be string, got {type(tag).__name__}")
            if len(tag) > MAX_TAG_LENGTH:
                raise ValidationError(f"Tag '{tag[:20]}...' exceeds {MAX_TAG_LENGTH} characters")

def validate_search_input(arguments: Dict[str, Any]) -> None:
    """Validate search input arguments."""
    if "query" in arguments and arguments["query"]:
        if len(arguments["query"]) > MAX_QUERY_LENGTH:
            raise ValidationError(f"Query exceeds {MAX_QUERY_LENGTH} characters")

def validate_relationship_input(arguments: Dict[str, Any]) -> None:
    """Validate relationship input arguments."""
    if "context" in arguments and arguments["context"]:
        if len(arguments["context"]) > MAX_CONTEXT_LENGTH:
            raise ValidationError(f"Context exceeds {MAX_CONTEXT_LENGTH} characters")
