#!/usr/bin/env python3
"""Helper functions for testing symbol extraction."""

from pathlib import Path
from typing import List, Dict


# Type mapping to match memosymbols.txt format (short tags)
TYPE_MAP = {
    'function': 'fun',
    'class': 'cla',
    'variable': 'var',
    'interface': 'int',
    'struct': 'str',
    'trait': 'trt',
    'method': 'mtd',
    'component': 'cmp',
    'table': 'tbl',
    'key': 'key',
    'tag': 'tag',
    'heading': 'hdr',
    'enum': 'enu',
    'type': 'typ',
    'module': 'mod',
    'property': 'prp',
    'attribute': 'att',
}


def save_test_results(symbols: List[Dict], language_name: str, test_dir: Path = None) -> Path:
    """
    Save extracted symbols to a txt file in line:type:name format.

    Args:
        symbols: List of symbol dictionaries with keys: file, line, type, name
        language_name: Name of the language (e.g., "go", "rust")
        test_dir: Directory containing the test file (defaults to current tests/)

    Returns:
        Path: Path to the saved result file
    """
    if test_dir is None:
        test_dir = Path(__file__).parent

    # Create test_results directory
    test_results_dir = test_dir / "test_results"
    test_results_dir.mkdir(exist_ok=True)

    # Format symbols as line:type:name (matching memosymbols.txt format)
    output_lines = []
    for sym in symbols:
        line = sym['line']
        sym_type = sym['type']
        name = sym['name']

        # Get short type tag (3 chars max)
        type_short = TYPE_MAP.get(sym_type, sym_type[:3])

        # Format: line:type:name
        output_lines.append(f"{line}:{type_short}:{name}")

    # Write to file
    result_file = test_results_dir / f"test_{language_name}_symbols.txt"
    result_file.write_text("\n".join(output_lines) + "\n")

    return result_file


def format_symbols_summary(symbols: List[Dict]) -> str:
    """
    Format symbols as a summary string for console output.

    Args:
        symbols: List of symbol dictionaries

    Returns:
        str: Formatted summary
    """
    if not symbols:
        return "No symbols found."

    lines = [f"Total symbols: {len(symbols)}"]
    for sym in symbols:
        lines.append(f"  {sym['line']}:{sym['type'][:3]}:{sym['name']}")

    return "\n".join(lines)
