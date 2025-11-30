#!/usr/bin/env python3
"""
Demo script showing context extraction in action.

This demonstrates how natural language relationship contexts are automatically
extracted into structured data.
"""

import json
from memorygraph.utils.context_extractor import extract_context_structure, parse_context


def print_section(title):
    """Print a section divider."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def demo_simple_extraction():
    """Demo simple context extraction."""
    print_section("Simple Context Extraction")

    contexts = [
        "partially implements auth module",
        "fully supports payment processing",
        "only works in production environment",
        "verified by integration tests",
        "implemented in v2.1.0",
        "supports all formats except XML"
    ]

    for context in contexts:
        print(f"\nInput: '{context}'")
        result = extract_context_structure(context)

        # Show non-empty fields
        print("Extracted:")
        if result.get('scope'):
            print(f"  - Scope: {result['scope']}")
        if result.get('components'):
            print(f"  - Components: {result['components']}")
        if result.get('conditions'):
            print(f"  - Conditions: {result['conditions']}")
        if result.get('evidence'):
            print(f"  - Evidence: {result['evidence']}")
        if result.get('temporal'):
            print(f"  - Temporal: {result['temporal']}")
        if result.get('exceptions'):
            print(f"  - Exceptions: {result['exceptions']}")


def demo_complex_extraction():
    """Demo complex multi-pattern extraction."""
    print_section("Complex Multi-Pattern Context")

    context = """
    This solution partially addresses the authentication flow refactor
    completed in v2.1. It works reliably in staging and production
    environments but requires Redis to be available. Testing shows
    it handles edge cases well, except for SSO logout scenarios
    which are tracked separately. Verified by security audit and E2E tests.
    """

    print(f"\nInput:\n{context}")
    result = extract_context_structure(context)

    print("\nExtracted Structure:")
    print(json.dumps(result, indent=2))


def demo_backward_compatibility():
    """Demo backward compatibility with old and new contexts."""
    print_section("Backward Compatibility")

    # Old style: plain text
    old_context = "this is legacy free text context from old database"
    print(f"\nOld Style (free text): '{old_context}'")
    old_parsed = parse_context(old_context)
    print(f"Parsed successfully: {old_parsed['text'] == old_context}")
    print(f"Auto-extracted structure: scope={old_parsed.get('scope')}")

    # New style: JSON
    new_structure = {
        "text": "new structured context",
        "scope": "partial",
        "components": ["auth module"],
        "conditions": ["production"],
        "evidence": [],
        "temporal": "v2.0",
        "exceptions": []
    }
    new_context = json.dumps(new_structure)
    print(f"\nNew Style (JSON):")
    print(f"  Input: {new_context[:50]}...")
    new_parsed = parse_context(new_context)
    print(f"  Parsed successfully: {new_parsed['scope'] == 'partial'}")
    print(f"  Scope: {new_parsed['scope']}")
    print(f"  Components: {new_parsed['components']}")


def demo_real_world_examples():
    """Demo real-world use cases."""
    print_section("Real-World Examples")

    examples = {
        "Auth Implementation": "partially implements OAuth2 flow, requires Redis for session storage, verified by security tests",
        "Bug Fix": "fixes memory leak in worker threads, tested in production since v2.3.1",
        "Feature Limitation": "supports all database types except MongoDB, conditional on connection pooling",
        "Integration": "connects authentication with user management, works in all environments"
    }

    for name, context in examples.items():
        print(f"\n{name}:")
        print(f"  Input: '{context}'")
        result = extract_context_structure(context)

        # Show key extractions
        summary = []
        if result.get('scope'):
            summary.append(f"scope={result['scope']}")
        if result.get('components'):
            summary.append(f"{len(result['components'])} components")
        if result.get('conditions'):
            summary.append(f"{len(result['conditions'])} conditions")
        if result.get('evidence'):
            summary.append(f"{len(result['evidence'])} evidence")
        if result.get('temporal'):
            summary.append(f"temporal={result['temporal']}")
        if result.get('exceptions'):
            summary.append(f"{len(result['exceptions'])} exceptions")

        print(f"  Extracted: {', '.join(summary) if summary else 'text only'}")


def demo_json_storage():
    """Demo JSON storage format."""
    print_section("JSON Storage Format")

    context = "partially implements auth module, verified by tests, works in production"
    print(f"\nUser writes: '{context}'")

    structure = extract_context_structure(context)
    json_string = json.dumps(structure)

    print(f"\nStored in database as JSON string ({len(json_string)} chars):")
    print(json_string)

    print(f"\nOriginal text: {len(context)} chars")
    print(f"JSON string: {len(json_string)} chars")
    print(f"Overhead: {len(json_string) - len(context)} chars ({len(json_string)/len(context):.1f}x)")

    print("\nOn retrieval, can be parsed back to structure:")
    parsed = json.loads(json_string)
    print(f"  - Original text preserved: {parsed['text'] == context}")
    print(f"  - Scope extracted: {parsed['scope']}")
    print(f"  - Components found: {parsed['components']}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  CONTEXT EXTRACTION DEMO")
    print("  Automatic Structure Extraction from Natural Language")
    print("="*70)

    demo_simple_extraction()
    demo_complex_extraction()
    demo_backward_compatibility()
    demo_real_world_examples()
    demo_json_storage()

    print("\n" + "="*70)
    print("  Demo Complete!")
    print("="*70)
    print()


if __name__ == "__main__":
    main()
