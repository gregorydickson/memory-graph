"""
Migration scripts for schema and data changes.

This package contains migration scripts for evolving the MemoryGraph schema
and data structure over time.
"""

from typing import List
from .multitenancy_migration import migrate_to_multitenant, rollback_from_multitenant

__all__ = [
    'migrate_to_multitenant',
    'rollback_from_multitenant',
]
