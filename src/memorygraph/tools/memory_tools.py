"""
Memory CRUD tool handlers for the MCP server.

This module contains handlers for basic memory operations:
- store_memory: Create new memories
- get_memory: Retrieve a memory by ID
- update_memory: Modify an existing memory
- delete_memory: Remove a memory and its relationships
"""

import logging
from typing import Any, Dict

from mcp.types import CallToolResult, TextContent
from pydantic import ValidationError as PydanticValidationError

from ..database import MemoryDatabase
from ..models import Memory, MemoryType, MemoryContext
from ..utils.validation import validate_memory_input, ValidationError
from .error_handling import handle_tool_errors

logger = logging.getLogger(__name__)


@handle_tool_errors("store memory")
async def handle_store_memory(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle store_memory tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - type: Memory type (solution, problem, error, etc.)
            - title: Short descriptive title
            - content: Detailed content
            - summary: Optional brief summary
            - tags: Optional list of tags
            - importance: Optional importance score (0.0-1.0)
            - context: Optional context information

    Returns:
        CallToolResult with memory ID on success or error message on failure
    """
    # Validate input arguments
    validate_memory_input(arguments)

    # Extract context if provided
    context = None
    if "context" in arguments:
        context = MemoryContext(**arguments["context"])

    # Create memory object
    memory = Memory(
        type=MemoryType(arguments["type"]),
        title=arguments["title"],
        content=arguments["content"],
        summary=arguments.get("summary"),
        tags=arguments.get("tags", []),
        importance=arguments.get("importance", 0.5),
        context=context
    )

    # Store in database
    memory_id = await memory_db.store_memory(memory)

    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"Memory stored successfully with ID: {memory_id}"
        )]
    )


@handle_tool_errors("get memory")
async def handle_get_memory(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_memory tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to retrieve
            - include_relationships: Whether to include related memories (default: True)

    Returns:
        CallToolResult with formatted memory details or error message
    """
    memory_id = arguments["memory_id"]
    include_relationships = arguments.get("include_relationships", True)

    memory = await memory_db.get_memory(memory_id, include_relationships)

    if not memory:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Memory not found: {memory_id}"
            )],
            isError=True
        )

    # Format memory for display
    memory_text = f"""**Memory: {memory.title}**
Type: {memory.type.value}
Created: {memory.created_at}
Importance: {memory.importance}
Tags: {', '.join(memory.tags) if memory.tags else 'None'}

**Content:**
{memory.content}"""

    if memory.summary:
        memory_text = f"**Summary:** {memory.summary}\n\n" + memory_text

    # Add context information if available
    if memory.context:
        context_parts = []

        if memory.context.project_path:
            context_parts.append(f"Project: {memory.context.project_path}")

        if memory.context.files_involved:
            files_str = ', '.join(memory.context.files_involved[:3])
            if len(memory.context.files_involved) > 3:
                files_str += f" (+{len(memory.context.files_involved) - 3} more)"
            context_parts.append(f"Files: {files_str}")

        if memory.context.languages:
            context_parts.append(f"Languages: {', '.join(memory.context.languages)}")

        if memory.context.frameworks:
            context_parts.append(f"Frameworks: {', '.join(memory.context.frameworks)}")

        if memory.context.technologies:
            context_parts.append(f"Technologies: {', '.join(memory.context.technologies)}")

        if memory.context.git_branch:
            context_parts.append(f"Branch: {memory.context.git_branch}")

        if context_parts:
            context_text = "\n**Context:**\n" + "\n".join(f"  {part}" for part in context_parts)
            memory_text += "\n" + context_text

    return CallToolResult(
        content=[TextContent(type="text", text=memory_text)]
    )


@handle_tool_errors("update memory")
async def handle_update_memory(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle update_memory tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to update (required)
            - title: New title (optional)
            - content: New content (optional)
            - summary: New summary (optional)
            - tags: New tags list (optional)
            - importance: New importance score (optional)

    Returns:
        CallToolResult with success message or error
    """
    # Validate input arguments
    validate_memory_input(arguments)

    memory_id = arguments["memory_id"]

    # Get existing memory
    memory = await memory_db.get_memory(memory_id, include_relationships=False)
    if not memory:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Memory not found: {memory_id}"
            )],
            isError=True
        )

    # Update fields
    if "title" in arguments:
        memory.title = arguments["title"]
    if "content" in arguments:
        memory.content = arguments["content"]
    if "summary" in arguments:
        memory.summary = arguments["summary"]
    if "tags" in arguments:
        memory.tags = arguments["tags"]
    if "importance" in arguments:
        memory.importance = arguments["importance"]

    # Update in database
    success = await memory_db.update_memory(memory)

    if success:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Memory updated successfully: {memory_id}"
            )]
        )
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to update memory: {memory_id}"
            )],
            isError=True
        )


@handle_tool_errors("delete memory")
async def handle_delete_memory(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle delete_memory tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to delete

    Returns:
        CallToolResult with success message or error
    """
    memory_id = arguments["memory_id"]

    success = await memory_db.delete_memory(memory_id)

    if success:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Memory deleted successfully: {memory_id}"
            )]
        )
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to delete memory (may not exist): {memory_id}"
            )],
            isError=True
        )
