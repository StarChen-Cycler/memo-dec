#!/usr/bin/env python3
"""Test Bash symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_bash_symbols():
    """Test that Bash symbols are extracted correctly."""

    # Create a test Bash file
    test_content = """
#!/bin/bash

# A simple function
greet() {
    echo "Hello, $1!"
}

# Another function
add_numbers() {
    local a=$1
    local b=$2
    echo $((a + b))
}

# Variable assignment
CONFIG_FILE="/etc/config"
MAX_RETRIES=3

# Main function
main() {
    greet "World"
    add_numbers 5 3
}

main "$@"
"""

    # Create temp file
    test_file = Path("test_example.sh")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "bash", Path(__file__).parent)

        # Check results
        print(f"Bash symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'greet' in symbol_names, "Should find greet function"
        assert 'add_numbers' in symbol_names, "Should find add_numbers function"
        assert 'main' in symbol_names, "Should find main function"

        print("\n✅ Bash symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_bash_symbols()
