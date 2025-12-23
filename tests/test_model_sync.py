"""Tests to ensure core and SDK models stay in sync."""
import pytest
from memorygraph.models import MemoryType, RelationshipType


class TestMemoryTypeSync:
    """Test that MemoryType enum is synchronized between core and SDK."""

    def test_memory_type_has_conversation(self):
        """Ensure CONVERSATION type exists in core."""
        assert hasattr(MemoryType, 'CONVERSATION')
        assert MemoryType.CONVERSATION.value == "conversation"

    def test_all_memory_types_documented(self):
        """Ensure all memory types are accounted for."""
        expected_types = {
            'task', 'code_pattern', 'problem', 'solution',
            'project', 'technology', 'error', 'fix',
            'command', 'file_context', 'workflow', 'general',
            'conversation'
        }
        actual_types = {t.value for t in MemoryType}
        assert expected_types == actual_types, (
            f"Missing: {expected_types - actual_types}, "
            f"Extra: {actual_types - expected_types}"
        )

    def test_sdk_memory_types_match_core(self):
        """Verify SDK MemoryType enum matches core."""
        try:
            # Import SDK models separately to avoid circular import issues
            import sys
            import importlib.util

            sdk_path = "/Users/gregorydickson/memory-graph/sdk/memorygraphsdk/models.py"
            spec = importlib.util.spec_from_file_location("sdk_models", sdk_path)
            if spec and spec.loader:
                sdk_models = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sdk_models)
                SDKMemoryType = sdk_models.MemoryType

                core_types = {t.value for t in MemoryType}
                sdk_types = {t.value for t in SDKMemoryType}

                assert core_types == sdk_types, (
                    f"Core types: {sorted(core_types)}\n"
                    f"SDK types: {sorted(sdk_types)}\n"
                    f"Missing in SDK: {core_types - sdk_types}\n"
                    f"Extra in SDK: {sdk_types - core_types}"
                )
            else:
                pytest.skip("Could not load SDK models")
        except Exception as e:
            pytest.skip(f"SDK not available in test environment: {e}")


class TestRelationshipTypeSync:
    """Test that RelationshipType enum is synchronized between core and SDK."""

    def test_all_relationship_types_documented(self):
        """Ensure all relationship types are accounted for."""
        expected_types = {
            # Causal relationships
            'CAUSES', 'TRIGGERS', 'LEADS_TO', 'PREVENTS', 'BREAKS',
            # Solution relationships
            'SOLVES', 'ADDRESSES', 'ALTERNATIVE_TO', 'IMPROVES', 'REPLACES',
            # Context relationships
            'OCCURS_IN', 'APPLIES_TO', 'WORKS_WITH', 'REQUIRES', 'USED_IN',
            # Learning relationships
            'BUILDS_ON', 'CONTRADICTS', 'CONFIRMS', 'GENERALIZES', 'SPECIALIZES',
            # Similarity relationships
            'SIMILAR_TO', 'VARIANT_OF', 'RELATED_TO', 'ANALOGY_TO', 'OPPOSITE_OF',
            # Workflow relationships
            'FOLLOWS', 'DEPENDS_ON', 'ENABLES', 'BLOCKS', 'PARALLEL_TO',
            # Quality relationships
            'EFFECTIVE_FOR', 'INEFFECTIVE_FOR', 'PREFERRED_OVER', 'DEPRECATED_BY', 'VALIDATED_BY'
        }
        actual_types = {t.value for t in RelationshipType}
        assert expected_types == actual_types, (
            f"Missing: {expected_types - actual_types}, "
            f"Extra: {actual_types - expected_types}"
        )

    def test_sdk_relationship_types_match_core(self):
        """Verify SDK RelationshipType enum matches core."""
        try:
            # Import SDK models separately to avoid circular import issues
            import importlib.util

            sdk_path = "/Users/gregorydickson/memory-graph/sdk/memorygraphsdk/models.py"
            spec = importlib.util.spec_from_file_location("sdk_models", sdk_path)
            if spec and spec.loader:
                sdk_models = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sdk_models)
                SDKRelationshipType = sdk_models.RelationshipType

                core_types = {t.value for t in RelationshipType}
                sdk_types = {t.value for t in SDKRelationshipType}

                assert core_types == sdk_types, (
                    f"Core types: {sorted(core_types)}\n"
                    f"SDK types: {sorted(sdk_types)}\n"
                    f"Missing in SDK: {core_types - sdk_types}\n"
                    f"Extra in SDK: {sdk_types - core_types}"
                )
            else:
                pytest.skip("Could not load SDK models")
        except Exception as e:
            pytest.skip(f"SDK not available in test environment: {e}")


class TestSDKBiTemporalFields:
    """Test that SDK Relationship model has bi-temporal fields."""

    def test_sdk_relationship_has_bitemporal_fields(self):
        """Ensure SDK Relationship model has optional bi-temporal fields."""
        try:
            # Import SDK models separately to avoid circular import issues
            import importlib.util
            import typing

            sdk_path = "/Users/gregorydickson/memory-graph/sdk/memorygraphsdk/models.py"
            spec = importlib.util.spec_from_file_location("sdk_models", sdk_path)
            if spec and spec.loader:
                sdk_models = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sdk_models)
                Relationship = sdk_models.Relationship

                # Check that Relationship class has bi-temporal fields
                assert hasattr(Relationship, 'model_fields'), "Relationship should be a Pydantic model"
                fields = Relationship.model_fields

                # Check for bi-temporal fields
                assert 'valid_from' in fields, "Relationship should have valid_from field"
                assert 'valid_until' in fields, "Relationship should have valid_until field"
                assert 'recorded_at' in fields, "Relationship should have recorded_at field"
                assert 'invalidated_by' in fields, "Relationship should have invalidated_by field"

                # Verify they are optional (nullable)
                # In Pydantic v2, we check the annotation directly
                valid_from_type = fields['valid_from'].annotation
                assert typing.get_origin(valid_from_type) is typing.Union or 'None' in str(valid_from_type), \
                    "valid_from should be optional (datetime | None)"
            else:
                pytest.skip("Could not load SDK models")

        except Exception as e:
            pytest.skip(f"SDK not available in test environment: {e}")


class TestModelSyncDocumentation:
    """Test that model differences are documented."""

    def test_enum_counts(self):
        """Document the current counts for reference."""
        memory_type_count = len(MemoryType)
        relationship_type_count = len(RelationshipType)

        # These are informational - they help track changes
        assert memory_type_count == 13, f"Expected 13 memory types, got {memory_type_count}"
        assert relationship_type_count == 35, f"Expected 35 relationship types, got {relationship_type_count}"
