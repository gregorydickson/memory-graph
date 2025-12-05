"""
001_add_multitenancy - Migration to add multi-tenancy support.

This migration:
1. Backfills tenant_id for existing memories (if specified)
2. Sets visibility to 'team' for existing memories
3. Creates multi-tenant indexes if not already present
4. Supports rollback by removing tenant assignments

Usage:
    from memorygraph.migration.scripts import migrate_to_multitenant

    # Migrate with default tenant
    await migrate_to_multitenant(backend, tenant_id="default")

    # Rollback
    await rollback_from_multitenant(backend)
"""

import logging
from typing import Optional
from ...backends.base import GraphBackend
from ...backends.sqlite_fallback import SQLiteFallbackBackend
from ...backends.turso import TursoBackend
from ...models import DatabaseConnectionError, Memory

logger = logging.getLogger(__name__)


async def migrate_to_multitenant(
    backend: GraphBackend,
    tenant_id: str = "default",
    dry_run: bool = False,
    visibility: str = "team"
) -> dict:
    """
    Migrate existing single-tenant database to multi-tenant mode.

    This function backfills tenant_id and visibility fields for all existing
    memories that don't have them set.

    Args:
        backend: Backend instance (must be connected)
        tenant_id: Tenant ID to assign to existing memories (default: "default")
        dry_run: If True, only report what would be changed without making changes
        visibility: Visibility level to set (default: "team")

    Returns:
        Dictionary with migration statistics:
        {
            "success": bool,
            "dry_run": bool,
            "memories_updated": int,
            "errors": list
        }

    Raises:
        DatabaseConnectionError: If backend is not connected
        ValueError: If tenant_id is empty or visibility is invalid

    Example:
        >>> backend = SQLiteFallbackBackend()
        >>> await backend.connect()
        >>> result = await migrate_to_multitenant(backend, tenant_id="acme-corp")
        >>> print(f"Updated {result['memories_updated']} memories")
    """
    if not backend or not backend.is_connected():
        raise DatabaseConnectionError("Backend must be connected before migration")

    if not tenant_id or not tenant_id.strip():
        raise ValueError("tenant_id cannot be empty")

    valid_visibility = ["private", "project", "team", "public"]
    if visibility not in valid_visibility:
        raise ValueError(f"visibility must be one of {valid_visibility}, got '{visibility}'")

    logger.info(f"Starting multi-tenancy migration (dry_run={dry_run})")
    logger.info(f"Assigning tenant_id='{tenant_id}', visibility='{visibility}'")

    errors = []
    memories_updated = 0

    try:
        # SQLite-based backends (SQLite, Turso)
        if isinstance(backend, (SQLiteFallbackBackend, TursoBackend)):
            memories_updated = await _migrate_sqlite_backend(
                backend, tenant_id, visibility, dry_run
            )

        # Neo4j/Memgraph backends
        elif hasattr(backend, 'execute_query'):
            memories_updated = await _migrate_graph_backend(
                backend, tenant_id, visibility, dry_run
            )

        else:
            raise ValueError(f"Unsupported backend type: {type(backend).__name__}")

        logger.info(f"Migration completed: {memories_updated} memories processed")

        return {
            "success": True,
            "dry_run": dry_run,
            "memories_updated": memories_updated,
            "tenant_id": tenant_id,
            "visibility": visibility,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        errors.append(str(e))
        return {
            "success": False,
            "dry_run": dry_run,
            "memories_updated": memories_updated,
            "tenant_id": tenant_id,
            "visibility": visibility,
            "errors": errors
        }


async def _migrate_sqlite_backend(
    backend: SQLiteFallbackBackend,
    tenant_id: str,
    visibility: str,
    dry_run: bool
) -> int:
    """
    Migrate SQLite-based backend to multi-tenant mode.

    Args:
        backend: SQLite backend instance
        tenant_id: Tenant ID to assign
        visibility: Visibility level to set
        dry_run: If True, only count without updating

    Returns:
        Number of memories updated
    """
    cursor = backend.conn.cursor()

    # Count memories without tenant_id
    cursor.execute("""
        SELECT COUNT(*) FROM nodes
        WHERE label = 'Memory'
        AND (
            json_extract(properties, '$.context.tenant_id') IS NULL
            OR json_extract(properties, '$.context.tenant_id') = ''
        )
    """)

    count = cursor.fetchone()[0]
    logger.info(f"Found {count} memories without tenant_id")

    if dry_run:
        logger.info(f"DRY RUN: Would update {count} memories")
        return count

    # Update memories by fetching, modifying, and updating each one
    # This ensures proper JSON structure handling
    cursor.execute("""
        SELECT id, properties FROM nodes
        WHERE label = 'Memory'
        AND (
            json_extract(properties, '$.context.tenant_id') IS NULL
            OR json_extract(properties, '$.context.tenant_id') = ''
        )
    """)

    import json
    updated = 0

    for row in cursor.fetchall():
        node_id = row[0]
        properties = json.loads(row[1])

        # Ensure context exists
        if 'context' not in properties or properties['context'] is None:
            properties['context'] = {}

        # Set tenant_id and visibility
        properties['context']['tenant_id'] = tenant_id
        properties['context']['visibility'] = visibility

        # Update the node
        cursor.execute("""
            UPDATE nodes
            SET properties = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [json.dumps(properties), node_id])

        updated += 1

    backend.conn.commit()
    logger.info(f"Updated {updated} memories with tenant_id='{tenant_id}'")

    return updated


async def _migrate_graph_backend(
    backend: GraphBackend,
    tenant_id: str,
    visibility: str,
    dry_run: bool
) -> int:
    """
    Migrate graph-based backend (Neo4j/Memgraph) to multi-tenant mode.

    Args:
        backend: Graph backend instance
        tenant_id: Tenant ID to assign
        visibility: Visibility level to set
        dry_run: If True, only count without updating

    Returns:
        Number of memories updated
    """
    # Count memories without tenant_id
    count_query = """
        MATCH (m:Memory)
        WHERE m.context_tenant_id IS NULL OR m.context_tenant_id = ''
        RETURN count(m) as count
    """

    count_result = await backend.execute_query(count_query)
    count = count_result[0]['count'] if count_result else 0

    logger.info(f"Found {count} memories without tenant_id")

    if dry_run:
        logger.info(f"DRY RUN: Would update {count} memories")
        return count

    # Update memories with tenant_id and visibility
    update_query = """
        MATCH (m:Memory)
        WHERE m.context_tenant_id IS NULL OR m.context_tenant_id = ''
        SET m.context_tenant_id = $tenant_id,
            m.context_visibility = $visibility,
            m.updated_at = timestamp()
        RETURN count(m) as updated
    """

    result = await backend.execute_query(
        update_query,
        {"tenant_id": tenant_id, "visibility": visibility},
        write=True
    )

    updated = result[0]['updated'] if result else 0
    logger.info(f"Updated {updated} memories with tenant_id='{tenant_id}'")

    return updated


async def rollback_from_multitenant(
    backend: GraphBackend,
    dry_run: bool = False
) -> dict:
    """
    Rollback multi-tenancy migration by removing tenant_id assignments.

    NOTE: This does not delete the tenant_id fields, it only sets them to NULL.
    This preserves the option to re-enable multi-tenancy in the future.

    Args:
        backend: Backend instance (must be connected)
        dry_run: If True, only report what would be changed

    Returns:
        Dictionary with rollback statistics

    Example:
        >>> result = await rollback_from_multitenant(backend)
        >>> print(f"Rolled back {result['memories_updated']} memories")
    """
    if not backend or not backend.is_connected():
        raise DatabaseConnectionError("Backend must be connected before rollback")

    logger.info(f"Starting multi-tenancy rollback (dry_run={dry_run})")

    errors = []
    memories_updated = 0

    try:
        # SQLite-based backends
        if isinstance(backend, (SQLiteFallbackBackend, TursoBackend)):
            memories_updated = await _rollback_sqlite_backend(backend, dry_run)

        # Graph backends
        elif hasattr(backend, 'execute_query'):
            memories_updated = await _rollback_graph_backend(backend, dry_run)

        else:
            raise ValueError(f"Unsupported backend type: {type(backend).__name__}")

        logger.info(f"Rollback completed: {memories_updated} memories processed")

        return {
            "success": True,
            "dry_run": dry_run,
            "memories_updated": memories_updated,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        errors.append(str(e))
        return {
            "success": False,
            "dry_run": dry_run,
            "memories_updated": memories_updated,
            "errors": errors
        }


async def _rollback_sqlite_backend(
    backend: SQLiteFallbackBackend,
    dry_run: bool
) -> int:
    """
    Rollback SQLite backend from multi-tenant mode.

    Args:
        backend: SQLite backend instance
        dry_run: If True, only count without updating

    Returns:
        Number of memories updated
    """
    cursor = backend.conn.cursor()

    # Count memories with tenant_id
    cursor.execute("""
        SELECT COUNT(*) FROM nodes
        WHERE label = 'Memory'
        AND json_extract(properties, '$.context.tenant_id') IS NOT NULL
    """)

    count = cursor.fetchone()[0]
    logger.info(f"Found {count} memories with tenant_id")

    if dry_run:
        logger.info(f"DRY RUN: Would clear tenant_id from {count} memories")
        return count

    # Clear tenant_id from memories
    cursor.execute("""
        SELECT id, properties FROM nodes
        WHERE label = 'Memory'
        AND json_extract(properties, '$.context.tenant_id') IS NOT NULL
    """)

    import json
    updated = 0

    for row in cursor.fetchall():
        node_id = row[0]
        properties = json.loads(row[1])

        # Clear tenant_id (set to NULL)
        if 'context' in properties and properties['context']:
            properties['context']['tenant_id'] = None
            # Optionally reset visibility to default
            properties['context']['visibility'] = 'project'

        # Update the node
        cursor.execute("""
            UPDATE nodes
            SET properties = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [json.dumps(properties), node_id])

        updated += 1

    backend.conn.commit()
    logger.info(f"Cleared tenant_id from {updated} memories")

    return updated


async def _rollback_graph_backend(
    backend: GraphBackend,
    dry_run: bool
) -> int:
    """
    Rollback graph backend from multi-tenant mode.

    Args:
        backend: Graph backend instance
        dry_run: If True, only count without updating

    Returns:
        Number of memories updated
    """
    # Count memories with tenant_id
    count_query = """
        MATCH (m:Memory)
        WHERE m.context_tenant_id IS NOT NULL
        RETURN count(m) as count
    """

    count_result = await backend.execute_query(count_query)
    count = count_result[0]['count'] if count_result else 0

    logger.info(f"Found {count} memories with tenant_id")

    if dry_run:
        logger.info(f"DRY RUN: Would clear tenant_id from {count} memories")
        return count

    # Clear tenant_id from memories
    update_query = """
        MATCH (m:Memory)
        WHERE m.context_tenant_id IS NOT NULL
        SET m.context_tenant_id = NULL,
            m.context_visibility = 'project',
            m.updated_at = timestamp()
        RETURN count(m) as updated
    """

    result = await backend.execute_query(update_query, write=True)
    updated = result[0]['updated'] if result else 0

    logger.info(f"Cleared tenant_id from {updated} memories")

    return updated
