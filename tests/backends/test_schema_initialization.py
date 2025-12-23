"""Tests for backend schema initialization."""
import pytest
import tempfile
import os
import json


class TestSchemaInitialization:
    """Test backend schema initialization."""

    @pytest.mark.asyncio
    async def test_sqlite_fresh_database_works(self):
        """Test that SQLite backend works with fresh database."""
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteFallbackBackend(db_path)

            # Connect first, then initialize schema
            await backend.connect()
            await backend.initialize_schema()

            # Verify tables were created
            cursor = backend.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            assert "nodes" in tables
            assert "relationships" in tables

            # Verify we can perform basic operations by inserting a node
            cursor.execute(
                "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                ("test-id", "Memory", json.dumps({"title": "Test Memory", "content": "Test content"}))
            )
            backend.conn.commit()

            # Verify we can retrieve
            cursor.execute("SELECT id, label, properties FROM nodes WHERE id = ?", ("test-id",))
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "test-id"
            assert row[1] == "Memory"

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_sqlite_schema_is_idempotent(self):
        """Test that calling initialize_schema multiple times is safe."""
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteFallbackBackend(db_path)

            # Connect first
            await backend.connect()

            # Call multiple times - should not error
            await backend.initialize_schema()
            await backend.initialize_schema()
            await backend.initialize_schema()

            # Verify tables still exist and work
            cursor = backend.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            assert "nodes" in tables
            assert "relationships" in tables

            # Should still work - insert a test node
            cursor.execute(
                "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                ("test-id", "Memory", json.dumps({"title": "Test", "content": "Content"}))
            )
            backend.conn.commit()

            # Verify insertion worked
            cursor.execute("SELECT COUNT(*) FROM nodes")
            count = cursor.fetchone()[0]
            assert count == 1

            await backend.disconnect()
