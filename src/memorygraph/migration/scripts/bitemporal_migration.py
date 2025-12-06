"""
002_add_bitemporal - Migration to add bi-temporal tracking to relationships.

This migration:
1. Adds temporal columns (valid_from, valid_until, recorded_at, invalidated_by)
2. Sets default values for existing relationships
3. Creates temporal indexes if not already present
4. Supports rollback (WARNING: loses temporal data)

Usage:
    from memorygraph.migration.scripts import migrate_to_bitemporal

    # Migrate existing database
    await migrate_to_bitemporal(backend)

    # Rollback (WARNING: loses temporal data)
    await rollback_from_bitemporal(backend)
"""

import json
import logging
import sqlite3
from typing import Optional
from ...backends.base import GraphBackend
from ...backends.sqlite_fallback import SQLiteFallbackBackend
from ...models import DatabaseConnectionError

logger = logging.getLogger(__name__)


async def migrate_to_bitemporal(
    backend: GraphBackend,
    dry_run: bool = False
) -> dict:
    """
    Migrate existing database to bi-temporal schema.

    This function adds temporal fields to the relationships table and sets
    sensible defaults for existing relationships:
    - valid_from = created_at (when the fact became true)
    - valid_until = NULL (still valid)
    - recorded_at = created_at (when we learned it)
    - invalidated_by = NULL (not superseded)

    Args:
        backend: Backend instance (must be connected)
        dry_run: If True, only report what would be changed without making changes

    Returns:
        Dictionary with migration statistics:
        {
            "success": bool,
            "dry_run": bool,
            "relationships_updated": int,
            "indexes_created": int,
            "errors": list
        }

    Raises:
        DatabaseConnectionError: If backend is not connected

    Example:
        >>> backend = SQLiteFallbackBackend()
        >>> await backend.connect()
        >>> result = await migrate_to_bitemporal(backend)
        >>> print(f"Updated {result['relationships_updated']} relationships")
    """
    # Check backend connection (use _connected attribute for SQLite backends)
    is_connected = getattr(backend, '_connected', False)
    if not backend or not is_connected:
        raise DatabaseConnectionError("Backend must be connected before migration")

    logger.info(f"Starting bi-temporal migration (dry_run={dry_run})")

    errors = []
    relationships_updated = 0
    indexes_created = 0

    try:
        # SQLite-based backends (SQLite, Turso) - use duck typing to avoid
        # isinstance issues when modules are reloaded during testing.
        # SQLite backends have a 'conn' attribute for the database connection.
        if hasattr(backend, 'conn') and backend.conn is not None:
            relationships_updated, indexes_created = await _migrate_sqlite_backend(
                backend, dry_run
            )

        # Neo4j/Memgraph backends - use execute_query method
        elif hasattr(backend, 'execute_query'):
            relationships_updated, indexes_created = await _migrate_graph_backend(
                backend, dry_run
            )

        else:
            raise ValueError(f"Unsupported backend type: {type(backend).__name__}")

        logger.info(
            f"Migration completed: {relationships_updated} relationships updated, "
            f"{indexes_created} indexes created"
        )

        return {
            "success": True,
            "dry_run": dry_run,
            "relationships_updated": relationships_updated,
            "indexes_created": indexes_created,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        errors.append(str(e))
        return {
            "success": False,
            "dry_run": dry_run,
            "relationships_updated": relationships_updated,
            "indexes_created": indexes_created,
            "errors": errors
        }


async def _migrate_sqlite_backend(
    backend: GraphBackend,
    dry_run: bool
) -> tuple[int, int]:
    """
    Migrate SQLite-based backend to bi-temporal schema.

    Args:
        backend: SQLite backend instance
        dry_run: If True, only count without updating

    Returns:
        Tuple of (relationships_updated, indexes_created)
    """
    # Runtime check for conn attribute (duck typing for SQLite backends)
    if not hasattr(backend, 'conn') or backend.conn is None:
        raise ValueError("Backend must have a 'conn' attribute for SQLite operations")

    cursor = backend.conn.cursor()

    # Check if temporal columns already exist
    cursor.execute("PRAGMA table_info(relationships)")
    columns = {row[1] for row in cursor.fetchall()}

    temporal_columns = {'valid_from', 'valid_until', 'recorded_at', 'invalidated_by'}
    existing_temporal = temporal_columns & columns
    missing_temporal = temporal_columns - columns

    if not missing_temporal:
        logger.info("Bi-temporal schema already exists, no migration needed")
        return 0, 0

    if existing_temporal and missing_temporal:
        logger.warning(
            f"Partial temporal schema detected. "
            f"Existing: {existing_temporal}, Missing: {missing_temporal}"
        )

    # Count relationships that need migration
    cursor.execute("SELECT COUNT(*) FROM relationships")
    count = cursor.fetchone()[0]
    logger.info(f"Found {count} relationships to migrate")

    if dry_run:
        logger.info(f"DRY RUN: Would update {count} relationships and create 3 indexes")
        return count, 3

    # Add temporal columns if missing
    for column in missing_temporal:
        try:
            if column == 'valid_from':
                cursor.execute("""
                    ALTER TABLE relationships
                    ADD COLUMN valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                """)
                logger.info("Added valid_from column")

            elif column == 'valid_until':
                cursor.execute("""
                    ALTER TABLE relationships
                    ADD COLUMN valid_until TIMESTAMP
                """)
                logger.info("Added valid_until column")

            elif column == 'recorded_at':
                cursor.execute("""
                    ALTER TABLE relationships
                    ADD COLUMN recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                """)
                logger.info("Added recorded_at column")

            elif column == 'invalidated_by':
                cursor.execute("""
                    ALTER TABLE relationships
                    ADD COLUMN invalidated_by TEXT
                """)
                logger.info("Added invalidated_by column")

        except sqlite3.Error as e:
            # Column might already exist from a previous partial migration
            logger.warning(f"Could not add column {column}: {e}")
        except Exception as e:
            # Unexpected error, re-raise
            logger.error(f"Unexpected error adding column {column}: {e}")
            raise

    # Set defaults for existing relationships using created_at
    # valid_from = created_at, recorded_at = created_at, valid_until = NULL
    cursor.execute("""
        UPDATE relationships
        SET valid_from = COALESCE(valid_from, created_at, CURRENT_TIMESTAMP),
            recorded_at = COALESCE(recorded_at, created_at, CURRENT_TIMESTAMP),
            valid_until = NULL,
            invalidated_by = NULL
        WHERE valid_from IS NULL OR recorded_at IS NULL
    """)

    updated = cursor.rowcount
    logger.info(f"Set temporal defaults for {updated} relationships")

    # Create temporal indexes
    indexes_created = 0

    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_temporal
            ON relationships(valid_from, valid_until)
        """)
        indexes_created += 1
        logger.info("Created idx_relationships_temporal")
    except sqlite3.Error as e:
        logger.warning(f"Could not create temporal index: {e}")

    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_current
            ON relationships(valid_until)
            WHERE valid_until IS NULL
        """)
        indexes_created += 1
        logger.info("Created idx_relationships_current (partial index)")
    except sqlite3.Error as e:
        logger.warning(f"Could not create current index: {e}")

    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_recorded
            ON relationships(recorded_at)
        """)
        indexes_created += 1
        logger.info("Created idx_relationships_recorded")
    except sqlite3.Error as e:
        logger.warning(f"Could not create recorded index: {e}")

    backend.conn.commit()
    logger.info(
        f"SQLite migration complete: {updated} relationships, "
        f"{indexes_created} indexes"
    )

    return updated, indexes_created


async def _migrate_graph_backend(
    backend: GraphBackend,
    dry_run: bool
) -> tuple[int, int]:
    """
    Migrate graph-based backend (Neo4j/Memgraph) to bi-temporal schema.

    For Neo4j/Memgraph, temporal fields are properties on relationships.
    We update all relationships to have the temporal properties.

    Args:
        backend: Graph backend instance
        dry_run: If True, only count without updating

    Returns:
        Tuple of (relationships_updated, indexes_created)
    """
    # Count relationships without temporal properties
    count_query = """
        MATCH ()-[r]->()
        WHERE r.valid_from IS NULL
        RETURN count(r) as count
    """

    count_result = await backend.execute_query(count_query)
    count = count_result[0]['count'] if count_result else 0

    logger.info(f"Found {count} relationships without temporal properties")

    if dry_run:
        logger.info(f"DRY RUN: Would update {count} relationships and create 3 indexes")
        return count, 3

    # Update relationships with temporal properties
    # Set valid_from = created_at (or now if created_at missing)
    # Set recorded_at = created_at (or now if created_at missing)
    # Set valid_until = NULL, invalidated_by = NULL
    update_query = """
        MATCH ()-[r]->()
        WHERE r.valid_from IS NULL
        SET r.valid_from = COALESCE(r.created_at, datetime()),
            r.recorded_at = COALESCE(r.created_at, datetime()),
            r.valid_until = NULL,
            r.invalidated_by = NULL
        RETURN count(r) as updated
    """

    result = await backend.execute_query(update_query, write=True)
    updated = result[0]['updated'] if result else 0

    logger.info(f"Updated {updated} relationships with temporal properties")

    # Create indexes for temporal queries
    indexes_created = 0

    try:
        # Index on valid_from for point-in-time queries
        await backend.execute_query(
            "CREATE INDEX rel_valid_from IF NOT EXISTS FOR ()-[r]-() ON (r.valid_from)",
            write=True
        )
        indexes_created += 1
        logger.info("Created index on valid_from")
    except Exception as e:
        logger.warning(f"Could not create valid_from index: {e}")

    try:
        # Index on valid_until for current relationship queries
        await backend.execute_query(
            "CREATE INDEX rel_valid_until IF NOT EXISTS FOR ()-[r]-() ON (r.valid_until)",
            write=True
        )
        indexes_created += 1
        logger.info("Created index on valid_until")
    except Exception as e:
        logger.warning(f"Could not create valid_until index: {e}")

    try:
        # Index on recorded_at for "what changed" queries
        await backend.execute_query(
            "CREATE INDEX rel_recorded_at IF NOT EXISTS FOR ()-[r]-() ON (r.recorded_at)",
            write=True
        )
        indexes_created += 1
        logger.info("Created index on recorded_at")
    except Exception as e:
        logger.warning(f"Could not create recorded_at index: {e}")

    logger.info(
        f"Graph migration complete: {updated} relationships, "
        f"{indexes_created} indexes"
    )

    return updated, indexes_created


async def rollback_from_bitemporal(
    backend: GraphBackend,
    dry_run: bool = False
) -> dict:
    """
    Rollback bi-temporal migration by removing temporal fields.

    WARNING: This operation loses all temporal data (valid_from, valid_until,
    recorded_at, invalidated_by). Use with caution!

    Args:
        backend: Backend instance (must be connected)
        dry_run: If True, only report what would be changed

    Returns:
        Dictionary with rollback statistics

    Example:
        >>> result = await rollback_from_bitemporal(backend)
        >>> print(f"Rolled back {result['relationships_updated']} relationships")
    """
    # Check backend connection (use _connected attribute for SQLite backends)
    is_connected = getattr(backend, '_connected', False)
    if not backend or not is_connected:
        raise DatabaseConnectionError("Backend must be connected before rollback")

    logger.warning("Starting bi-temporal rollback - THIS WILL LOSE TEMPORAL DATA")

    errors = []
    relationships_updated = 0
    indexes_dropped = 0

    try:
        # SQLite-based backends - use duck typing (check for conn attribute)
        if hasattr(backend, 'conn') and backend.conn is not None:
            relationships_updated, indexes_dropped = await _rollback_sqlite_backend(
                backend, dry_run
            )

        # Graph backends - use execute_query method
        elif hasattr(backend, 'execute_query'):
            relationships_updated, indexes_dropped = await _rollback_graph_backend(
                backend, dry_run
            )

        else:
            raise ValueError(f"Unsupported backend type: {type(backend).__name__}")

        logger.info(
            f"Rollback completed: {relationships_updated} relationships updated, "
            f"{indexes_dropped} indexes dropped"
        )

        return {
            "success": True,
            "dry_run": dry_run,
            "relationships_updated": relationships_updated,
            "indexes_dropped": indexes_dropped,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        errors.append(str(e))
        return {
            "success": False,
            "dry_run": dry_run,
            "relationships_updated": relationships_updated,
            "indexes_dropped": indexes_dropped,
            "errors": errors
        }


async def _rollback_sqlite_backend(
    backend: GraphBackend,
    dry_run: bool
) -> tuple[int, int]:
    """
    Rollback SQLite backend from bi-temporal schema.

    NOTE: SQLite does not support DROP COLUMN easily, so we:
    1. Drop temporal indexes
    2. Set temporal columns to NULL (preserves schema but clears data)

    Args:
        backend: SQLite backend instance
        dry_run: If True, only count without updating

    Returns:
        Tuple of (relationships_updated, indexes_dropped)
    """
    # Runtime check for conn attribute (duck typing for SQLite backends)
    if not hasattr(backend, 'conn') or backend.conn is None:
        raise ValueError("Backend must have a 'conn' attribute for SQLite operations")

    cursor = backend.conn.cursor()

    # Count relationships with temporal data
    cursor.execute("""
        SELECT COUNT(*) FROM relationships
        WHERE valid_from IS NOT NULL OR recorded_at IS NOT NULL
    """)

    count = cursor.fetchone()[0]
    logger.info(f"Found {count} relationships with temporal data")

    if dry_run:
        logger.info(
            f"DRY RUN: Would clear temporal data from {count} relationships "
            f"and drop 3 indexes"
        )
        return count, 3

    # Clear temporal data (set to NULL)
    cursor.execute("""
        UPDATE relationships
        SET valid_from = NULL,
            valid_until = NULL,
            recorded_at = NULL,
            invalidated_by = NULL
        WHERE valid_from IS NOT NULL OR recorded_at IS NOT NULL
    """)

    updated = cursor.rowcount
    logger.info(f"Cleared temporal data from {updated} relationships")

    # Drop temporal indexes
    indexes_dropped = 0

    try:
        cursor.execute("DROP INDEX IF EXISTS idx_relationships_temporal")
        indexes_dropped += 1
        logger.info("Dropped idx_relationships_temporal")
    except sqlite3.Error as e:
        logger.warning(f"Could not drop temporal index: {e}")

    try:
        cursor.execute("DROP INDEX IF EXISTS idx_relationships_current")
        indexes_dropped += 1
        logger.info("Dropped idx_relationships_current")
    except sqlite3.Error as e:
        logger.warning(f"Could not drop current index: {e}")

    try:
        cursor.execute("DROP INDEX IF EXISTS idx_relationships_recorded")
        indexes_dropped += 1
        logger.info("Dropped idx_relationships_recorded")
    except sqlite3.Error as e:
        logger.warning(f"Could not drop recorded index: {e}")

    backend.conn.commit()
    logger.info(
        f"SQLite rollback complete: {updated} relationships, "
        f"{indexes_dropped} indexes dropped"
    )

    return updated, indexes_dropped


async def _rollback_graph_backend(
    backend: GraphBackend,
    dry_run: bool
) -> tuple[int, int]:
    """
    Rollback graph backend from bi-temporal schema.

    Args:
        backend: Graph backend instance
        dry_run: If True, only count without updating

    Returns:
        Tuple of (relationships_updated, indexes_dropped)
    """
    # Count relationships with temporal properties
    count_query = """
        MATCH ()-[r]->()
        WHERE r.valid_from IS NOT NULL
        RETURN count(r) as count
    """

    count_result = await backend.execute_query(count_query)
    count = count_result[0]['count'] if count_result else 0

    logger.info(f"Found {count} relationships with temporal properties")

    if dry_run:
        logger.info(
            f"DRY RUN: Would remove temporal properties from {count} relationships "
            f"and drop 3 indexes"
        )
        return count, 3

    # Remove temporal properties
    update_query = """
        MATCH ()-[r]->()
        WHERE r.valid_from IS NOT NULL
        REMOVE r.valid_from, r.valid_until, r.recorded_at, r.invalidated_by
        RETURN count(r) as updated
    """

    result = await backend.execute_query(update_query, write=True)
    updated = result[0]['updated'] if result else 0

    logger.info(f"Removed temporal properties from {updated} relationships")

    # Drop temporal indexes
    indexes_dropped = 0

    try:
        await backend.execute_query("DROP INDEX rel_valid_from IF EXISTS", write=True)
        indexes_dropped += 1
        logger.info("Dropped valid_from index")
    except Exception as e:
        logger.warning(f"Could not drop valid_from index: {e}")

    try:
        await backend.execute_query("DROP INDEX rel_valid_until IF EXISTS", write=True)
        indexes_dropped += 1
        logger.info("Dropped valid_until index")
    except Exception as e:
        logger.warning(f"Could not drop valid_until index: {e}")

    try:
        await backend.execute_query("DROP INDEX rel_recorded_at IF EXISTS", write=True)
        indexes_dropped += 1
        logger.info("Dropped recorded_at index")
    except Exception as e:
        logger.warning(f"Could not drop recorded_at index: {e}")

    logger.info(
        f"Graph rollback complete: {updated} relationships, "
        f"{indexes_dropped} indexes dropped"
    )

    return updated, indexes_dropped
