"""
Temporal tool handlers for bi-temporal queries.

This module contains handlers for temporal operations:
- query_as_of: Query relationships as they existed at a specific time
- get_relationship_history: Get full history of relationships for a memory
- what_changed: Show relationship changes since a specific time
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from mcp.types import CallToolResult, TextContent

from ..database import MemoryDatabase
from ..models import RelationshipType

logger = logging.getLogger(__name__)


async def handle_query_as_of(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle query_as_of tool call for point-in-time queries.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to query
            - as_of: ISO 8601 timestamp (e.g., "2024-12-01T00:00:00Z")
            - relationship_types: Optional list of relationship types to filter

    Returns:
        CallToolResult with relationships valid at that time or error message
    """
    try:
        memory_id = arguments["memory_id"]
        as_of_str = arguments["as_of"]

        # Parse ISO 8601 timestamp
        try:
            as_of = datetime.fromisoformat(as_of_str.replace('Z', '+00:00'))
        except ValueError:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Invalid timestamp format. Expected ISO 8601 (e.g., '2024-12-01T00:00:00Z'), got: {as_of_str}"
                )],
                isError=True
            )

        # Get optional relationship type filter
        relationship_types = None
        if "relationship_types" in arguments:
            relationship_types = [RelationshipType(t) for t in arguments["relationship_types"]]

        # Query as of the specified time
        related_memories = await memory_db.get_related_memories(
            memory_id=memory_id,
            relationship_types=relationship_types,
            as_of=as_of
        )

        if not related_memories:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No relationships found for memory '{memory_id}' as of {as_of_str}"
                )]
            )

        # Format results
        results_text = f"**Relationships as of {as_of_str}** ({len(related_memories)} found):\n\n"
        for i, (memory, relationship) in enumerate(related_memories, 1):
            results_text += f"**{i}. {memory.title}** (ID: {memory.id})\n"
            results_text += f"Relationship: {relationship.type.value} (strength: {relationship.properties.strength})\n"
            results_text += f"Valid from: {relationship.properties.valid_from.isoformat()}\n"
            if relationship.properties.valid_until:
                results_text += f"Valid until: {relationship.properties.valid_until.isoformat()}\n"
            else:
                results_text += "Valid until: current\n"
            results_text += f"Type: {memory.type.value} | Importance: {memory.importance}\n\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except KeyError as e:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to query as of: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to query as of: {e}"
            )],
            isError=True
        )


async def handle_get_relationship_history(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_relationship_history tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to get history for
            - relationship_types: Optional list of relationship types to filter

    Returns:
        CallToolResult with full relationship history or error message
    """
    try:
        memory_id = arguments["memory_id"]

        # Get optional relationship type filter
        relationship_types = None
        if "relationship_types" in arguments:
            relationship_types = [RelationshipType(t) for t in arguments["relationship_types"]]

        # Get full history (including invalidated relationships)
        history = await memory_db.get_relationship_history(
            memory_id=memory_id,
            relationship_types=relationship_types
        )

        if not history:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No relationship history found for memory: {memory_id}"
                )]
            )

        # Format results chronologically
        results_text = f"**Relationship History for {memory_id}** ({len(history)} relationships):\n\n"

        # Group by current vs invalidated
        current = [r for r in history if r.properties.valid_until is None]
        invalidated = [r for r in history if r.properties.valid_until is not None]

        if current:
            results_text += "## Current Relationships:\n\n"
            for i, rel in enumerate(current, 1):
                results_text += f"**{i}. {rel.type.value}**\n"
                results_text += f"From: {rel.from_memory_id} → To: {rel.to_memory_id}\n"
                results_text += f"Valid from: {rel.properties.valid_from.isoformat()}\n"
                results_text += f"Strength: {rel.properties.strength} | Confidence: {rel.properties.confidence}\n"
                if rel.properties.context:
                    # Context is stored as JSON string, parse it
                    try:
                        context = json.loads(rel.properties.context)
                        if context.get('summary'):
                            results_text += f"Context: {context['summary']}\n"
                    except (json.JSONDecodeError, KeyError):
                        pass
                results_text += "\n"

        if invalidated:
            results_text += "## Historical (Invalidated) Relationships:\n\n"
            for i, rel in enumerate(invalidated, 1):
                results_text += f"**{i}. {rel.type.value}**\n"
                results_text += f"From: {rel.from_memory_id} → To: {rel.to_memory_id}\n"
                results_text += f"Valid from: {rel.properties.valid_from.isoformat()}\n"
                results_text += f"Valid until: {rel.properties.valid_until.isoformat()}\n"
                if rel.properties.invalidated_by:
                    results_text += f"Superseded by: {rel.properties.invalidated_by}\n"
                results_text += f"Strength: {rel.properties.strength}\n\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except KeyError as e:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to get relationship history: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to get relationship history: {e}"
            )],
            isError=True
        )


async def handle_what_changed(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle what_changed tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - since: ISO 8601 timestamp to query from (e.g., "2024-12-01T00:00:00Z")

    Returns:
        CallToolResult with changes since the specified time or error message
    """
    try:
        since_str = arguments["since"]

        # Parse ISO 8601 timestamp
        try:
            since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
        except ValueError:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Invalid timestamp format. Expected ISO 8601 (e.g., '2024-12-01T00:00:00Z'), got: {since_str}"
                )],
                isError=True
            )

        # Query what changed
        changes = await memory_db.what_changed(since=since)

        new_rels = changes.get("new_relationships", [])
        invalidated_rels = changes.get("invalidated_relationships", [])

        if not new_rels and not invalidated_rels:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No relationship changes found since {since_str}"
                )]
            )

        # Format results
        results_text = f"**Changes since {since_str}**:\n\n"

        if new_rels:
            results_text += f"## New Relationships ({len(new_rels)}):\n\n"
            for i, rel in enumerate(new_rels, 1):
                results_text += f"**{i}. {rel.type.value}**\n"
                results_text += f"From: {rel.from_memory_id} → To: {rel.to_memory_id}\n"
                results_text += f"Recorded at: {rel.properties.recorded_at.isoformat()}\n"
                results_text += f"Strength: {rel.properties.strength}\n"
                if rel.properties.context:
                    try:
                        context = json.loads(rel.properties.context)
                        if context.get('summary'):
                            results_text += f"Context: {context['summary']}\n"
                    except (json.JSONDecodeError, KeyError):
                        pass
                results_text += "\n"

        if invalidated_rels:
            results_text += f"## Invalidated Relationships ({len(invalidated_rels)}):\n\n"
            for i, rel in enumerate(invalidated_rels, 1):
                results_text += f"**{i}. {rel.type.value}**\n"
                results_text += f"From: {rel.from_memory_id} → To: {rel.to_memory_id}\n"
                results_text += f"Invalidated at: {rel.properties.valid_until.isoformat()}\n"
                if rel.properties.invalidated_by:
                    results_text += f"Superseded by: {rel.properties.invalidated_by}\n"
                results_text += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except KeyError as e:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to get what changed: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to get what changed: {e}"
            )],
            isError=True
        )
