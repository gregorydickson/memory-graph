"""
Context extraction utilities for relationship contexts.

This module provides pattern-based extraction of structured information
from natural language relationship context fields.
"""

import json
import re
from typing import Any, Dict, List, Optional


def extract_context_structure(text: Optional[str]) -> Dict[str, Any]:
    """
    Auto-extract structure from free-text context.

    Args:
        text: Natural language context string

    Returns:
        Dictionary with structure:
        {
            "text": str,              # Original text (always preserved)
            "scope": Optional[str],   # partial|full|conditional|None
            "components": List[str],  # Mentioned components/modules
            "conditions": List[str],  # When/if/requires patterns
            "evidence": List[str],    # Verification/testing mentions
            "temporal": Optional[str],# Version/date/time info
            "exceptions": List[str]   # Exclusions/limitations
        }

    Examples:
        >>> extract_context_structure("partially implements auth module")
        {
            "text": "partially implements auth module",
            "scope": "partial",
            "components": ["auth module"],
            "conditions": [],
            "evidence": [],
            "temporal": None,
            "exceptions": []
        }

        >>> extract_context_structure("verified by integration tests")
        {
            "text": "verified by integration tests",
            "scope": None,
            "components": [],
            "conditions": [],
            "evidence": ["integration tests"],
            "temporal": None,
            "exceptions": []
        }
    """
    if text is None:
        return {}

    if not isinstance(text, str):
        text = str(text)

    # Always preserve original text
    result = {
        "text": text,
        "scope": _extract_scope(text),
        "components": _extract_components(text),
        "conditions": _extract_conditions(text),
        "evidence": _extract_evidence(text),
        "temporal": _extract_temporal(text),
        "exceptions": _extract_exceptions(text),
    }

    return result


def parse_context(context: Optional[str]) -> Dict[str, Any]:
    """
    Parse context field - handles both JSON and free text.

    This function provides backward compatibility by:
    1. Trying to parse as JSON first (new structured format)
    2. Falling back to pattern extraction for legacy free text

    Args:
        context: Context string (either JSON or free text)

    Returns:
        Structured dictionary with extracted information

    Examples:
        >>> parse_context('{"text": "test", "scope": "partial"}')
        {"text": "test", "scope": "partial"}

        >>> parse_context("this is free text")
        {"text": "this is free text", "scope": None, ...}

        >>> parse_context(None)
        {}
    """
    if not context:
        return {}

    # Try parsing as JSON first (new format)
    try:
        return json.loads(context)
    except (json.JSONDecodeError, TypeError):
        # Legacy free-text format - extract structure
        return extract_context_structure(context)


def _extract_scope(text: str) -> Optional[str]:
    """
    Extract scope information from text.

    Patterns:
    - partial: "partially", "limited", "incomplete"
    - full: "fully", "complete", "completely", "entirely"
    - conditional: "conditional", "only", "if", "when"

    Args:
        text: Context text to analyze

    Returns:
        Scope type or None if not detected
    """
    if not text:
        return None

    text_lower = text.lower()

    # Partial scope patterns
    partial_patterns = [
        r'\bpartial(ly)?\b',
        r'\blimited\b',
        r'\bincomplete\b',
    ]

    for pattern in partial_patterns:
        if re.search(pattern, text_lower):
            return "partial"

    # Full scope patterns
    full_patterns = [
        r'\bfull(y)?\b',
        r'\bcomplete(ly)?\b',
        r'\bentirely\b',
    ]

    for pattern in full_patterns:
        if re.search(pattern, text_lower):
            return "full"

    # Conditional scope patterns
    conditional_patterns = [
        r'\bconditional(ly)?\b',
        r'\bonly\b',
    ]

    for pattern in conditional_patterns:
        if re.search(pattern, text_lower):
            return "conditional"

    return None


def _extract_conditions(text: str) -> List[str]:
    """
    Extract conditional statements from text.

    Patterns:
    - "when X"
    - "if X"
    - "in X environment"
    - "requires X"

    Args:
        text: Context text to analyze

    Returns:
        List of extracted conditions
    """
    if not text:
        return []

    conditions = []

    # Pattern: "when X"
    when_matches = re.finditer(r'\bwhen\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in when_matches:
        conditions.append(match.group(1).strip())

    # Pattern: "if X"
    if_matches = re.finditer(r'\bif\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in if_matches:
        conditions.append(match.group(1).strip())

    # Pattern: "in X environment"
    env_matches = re.finditer(
        r'\bin\s+([\w\-]+)\s+environment', text, re.IGNORECASE
    )
    for match in env_matches:
        conditions.append(match.group(1).strip())

    # Pattern: "requires X"
    requires_matches = re.finditer(r'\brequires\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in requires_matches:
        conditions.append(match.group(1).strip())

    # Pattern: "only works in X" or "only in X"
    only_in_matches = re.finditer(
        r'\bonly\s+(?:works\s+)?in\s+([^,\.;]+)', text, re.IGNORECASE
    )
    for match in only_in_matches:
        conditions.append(match.group(1).strip())

    return conditions


def _extract_evidence(text: str) -> List[str]:
    """
    Extract evidence/verification mentions from text.

    Patterns:
    - "verified by X"
    - "tested by X"
    - "proven by X"
    - "observed in X"

    Args:
        text: Context text to analyze

    Returns:
        List of extracted evidence
    """
    if not text:
        return []

    evidence = []

    # Pattern: "verified by X"
    verified_matches = re.finditer(
        r'\bverified\s+by\s+([^,\.;]+)', text, re.IGNORECASE
    )
    for match in verified_matches:
        evidence.append(match.group(1).strip())

    # Pattern: "tested by X"
    tested_matches = re.finditer(r'\btested\s+by\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in tested_matches:
        evidence.append(match.group(1).strip())

    # Pattern: "proven by X"
    proven_matches = re.finditer(r'\bproven\s+by\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in proven_matches:
        evidence.append(match.group(1).strip())

    # Pattern: "observed in X"
    observed_matches = re.finditer(
        r'\bobserved\s+in\s+([^,\.;]+)', text, re.IGNORECASE
    )
    for match in observed_matches:
        evidence.append(match.group(1).strip())

    return evidence


def _extract_temporal(text: str) -> Optional[str]:
    """
    Extract temporal information from text.

    Patterns:
    - Temporal markers: "since X", "after X", "as of X" (checked first for context)
    - Version numbers: "v2.1.0", "version 2.1.0"

    Args:
        text: Context text to analyze

    Returns:
        Temporal information or None if not detected
    """
    if not text:
        return None

    # Pattern: "since X" - use looser pattern that allows periods (for versions)
    since_match = re.search(r'\bsince\s+([^,;]+?)(?:\s*,|\s*;|$)', text, re.IGNORECASE)
    if since_match:
        return since_match.group(1).strip()

    # Pattern: "after X"
    after_match = re.search(r'\bafter\s+([^,;]+?)(?:\s*,|\s*;|$)', text, re.IGNORECASE)
    if after_match:
        return after_match.group(1).strip()

    # Pattern: "as of X"
    as_of_match = re.search(r'\bas\s+of\s+([^,;]+?)(?:\s*,|\s*;|$)', text, re.IGNORECASE)
    if as_of_match:
        return as_of_match.group(1).strip()

    # Pattern: Version numbers (v2.1.0 or 2.1.0)
    version_match = re.search(r'\bv?\d+\.\d+(?:\.\d+)?', text, re.IGNORECASE)
    if version_match:
        return version_match.group(0)

    return None


def _extract_exceptions(text: str) -> List[str]:
    """
    Extract exceptions/exclusions from text.

    Patterns:
    - "except X"
    - "excluding X"
    - "but not X"
    - "without X"

    Args:
        text: Context text to analyze

    Returns:
        List of extracted exceptions
    """
    if not text:
        return []

    exceptions = []

    # Pattern: "except X"
    except_matches = re.finditer(r'\bexcept\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in except_matches:
        exceptions.append(match.group(1).strip())

    # Pattern: "excluding X"
    excluding_matches = re.finditer(r'\bexcluding\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in excluding_matches:
        exceptions.append(match.group(1).strip())

    # Pattern: "but not X"
    but_not_matches = re.finditer(r'\bbut\s+not\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in but_not_matches:
        exceptions.append(match.group(1).strip())

    # Pattern: "without X"
    without_matches = re.finditer(r'\bwithout\s+([^,\.;]+)', text, re.IGNORECASE)
    for match in without_matches:
        exceptions.append(match.group(1).strip())

    return exceptions


def _extract_components(text: str) -> List[str]:
    """
    Extract component/module names from text using simple heuristics.

    This function uses basic noun phrase patterns to identify technical
    components mentioned in the context.

    Patterns:
    - "X module"
    - "X service"
    - "X layer"
    - "X system"
    - "X threads/process/flow"
    - Technical terms (capitalized words, hyphenated terms)

    Args:
        text: Context text to analyze

    Returns:
        List of extracted component names
    """
    if not text:
        return []

    components = []

    # Pattern: "X module/service/layer/system/component"
    component_patterns = [
        r'([\w\-]+)\s+module',
        r'([\w\-]+)\s+service',
        r'([\w\-]+)\s+layer',
        r'([\w\-]+)\s+system',
        r'([\w\-]+)\s+component',
        r'([\w\-]+)\s+database',
        r'([\w\-]+)\s+API',
        r'([\w\-]+)\s+threads?',
        r'([\w\-]+)\s+process(?:es)?',
        r'([\w\-]+)\s+flow',
        r'([\w\-]+)\s+leak',
    ]

    for pattern in component_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            component = f"{match.group(1)} {match.group(0).split()[-1]}"
            if component not in components:
                components.append(component)

    # Pattern: "implements/fixes X" where X is a technical noun phrase
    action_patterns = [
        r'\b(?:implements?|fixes?|supports?|handles?)\s+([\w\-]+(?:\s+[\w\-]+)?)',
    ]

    for pattern in action_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            component = match.group(1).strip()
            # Skip if it's just a scope word
            if component.lower() not in ['partially', 'fully', 'feature', 'all']:
                if component not in components:
                    components.append(component)

    # Pattern: Capitalized technical terms (e.g., PostgreSQL, Redis, OAuth)
    # Match words that start with capital letter and are at least 3 chars
    cap_matches = re.finditer(r'\b([A-Z][A-Za-z0-9]{2,})\b', text)
    for match in cap_matches:
        term = match.group(1)
        # Filter out common words that aren't technical terms
        if term not in ['The', 'This', 'That', 'It', 'Testing']:
            if term not in components:
                components.append(term)

    # Pattern: Hyphenated technical terms (e.g., two-factor, JWT-based)
    hyphen_matches = re.finditer(r'\b([\w]+-[\w]+)\b', text)
    for match in hyphen_matches:
        term = match.group(1)
        if term not in components:
            components.append(term)

    return components
