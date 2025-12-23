"""
Relationship tool handlers for the MCP server.

This module contains handlers for relationship operations:
- create_relationship: Create relationships between memories
- get_related_memories: Find memories related to a specific memory
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolResult, TextContent

from ..database import MemoryDatabase
from ..models import RelationshipType, RelationshipProperties
from ..utils.validation import validate_relationship_input
from .error_handling import handle_tool_errors

logger = logging.getLogger(__name__)


@handle_tool_errors("create relationship")
async def handle_create_relationship(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle create_relationship tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - from_memory_id: ID of source memory
            - to_memory_id: ID of target memory
            - relationship_type: Type of relationship (SOLVES, CAUSES, etc.)
            - strength: Optional relationship strength (0.0-1.0, default: 0.5)
            - confidence: Optional confidence score (0.0-1.0, default: 0.8)
            - context: Optional natural language description

    Returns:
        CallToolResult with relationship ID on success or error message on failure
    """
    # Validate input arguments
    validate_relationship_input(arguments)

    # Get user-provided context (natural language)
    user_context = arguments.get("context")

    # Auto-extract structure if context provided
    structured_context = None
    if user_context:
        from ..utils.context_extractor import extract_context_structure
        structure = extract_context_structure(user_context)
        structured_context = json.dumps(structure)  # Serialize to JSON string

    properties = RelationshipProperties(
        strength=arguments.get("strength", 0.5),
        confidence=arguments.get("confidence", 0.8),
        context=structured_context  # Store JSON string
    )

    relationship_id = await memory_db.create_relationship(
        from_memory_id=arguments["from_memory_id"],
        to_memory_id=arguments["to_memory_id"],
        relationship_type=RelationshipType(arguments["relationship_type"]),
        properties=properties
    )

    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"Relationship created successfully: {relationship_id}"
        )]
    )


@handle_tool_errors("get related memories")
async def handle_get_related_memories(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_related_memories tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to find relations for
            - relationship_types: Optional list of relationship types to filter
            - max_depth: Optional maximum traversal depth (default: 2)

    Returns:
        CallToolResult with list of related memories or error message
    """
    memory_id = arguments["memory_id"]
    relationship_types = None

    if "relationship_types" in arguments:
        relationship_types = [RelationshipType(t) for t in arguments["relationship_types"]]

    max_depth = arguments.get("max_depth", 2)

    related_memories = await memory_db.get_related_memories(
        memory_id=memory_id,
        relationship_types=relationship_types,
        max_depth=max_depth
    )

    if not related_memories:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"No related memories found for: {memory_id}"
            )]
        )

    # Format results
    results_text = f"Found {len(related_memories)} related memories:\n\n"
    for i, (memory, relationship) in enumerate(related_memories, 1):
        results_text += f"**{i}. {memory.title}** (ID: {memory.id})\n"
        results_text += f"Relationship: {relationship.type.value} (strength: {relationship.properties.strength})\n"
        results_text += f"Type: {memory.type.value} | Importance: {memory.importance}\n\n"

    return CallToolResult(
        content=[TextContent(type="text", text=results_text)]
    )
