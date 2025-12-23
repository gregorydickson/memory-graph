"""Tests for backend capability detection."""
import pytest


class TestBackendCapabilities:
    """Test suite for backend capability detection."""

    def test_sqlite_is_cypher_capable(self):
        """SQLite backend should report Cypher capability."""
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        backend = SQLiteFallbackBackend(":memory:")
        assert backend.is_cypher_capable() is True

    def test_cloud_is_not_cypher_capable(self):
        """Cloud backend should report no Cypher capability."""
        from memorygraph.backends.cloud_backend import CloudRESTAdapter

        # Mock the required config
        backend = CloudRESTAdapter.__new__(CloudRESTAdapter)
        backend._initialized = False
        assert backend.is_cypher_capable() is False

    def test_all_graph_backends_are_cypher_capable(self):
        """All GraphBackend subclasses should be Cypher capable."""
        from memorygraph.backends.base import GraphBackend
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        # SQLite is the only one we can easily instantiate without external deps
        backend = SQLiteFallbackBackend(":memory:")
        assert isinstance(backend, GraphBackend)
        assert backend.is_cypher_capable() is True

    def test_cloud_adapter_deprecation_alias(self):
        """CloudBackend alias should work for backwards compatibility."""
        from memorygraph.backends.cloud_backend import CloudBackend, CloudRESTAdapter

        assert CloudBackend is CloudRESTAdapter
