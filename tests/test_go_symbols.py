#!/usr/bin/env python3
"""Test Go symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_go_symbols():
    """Test that Go symbols are extracted correctly."""

    # Create a test Go file
    test_content = """
package main

import "fmt"

// Main function
func main() {
    fmt.Println("Hello, World!")
}

// A simple function
func add(a int, b int) int {
    return a + b
}

// A struct type
type Person struct {
    Name string
    Age  int
}

// An interface
type Speaker interface {
    Speak() string
}

// A method
func (p Person) Speak() string {
    return "Hello"
}

// Variable declaration
var x int = 10
"""

    # Create temp file
    test_file = Path("test_example.go")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "go", Path(__file__).parent)

        # Check results
        print(f"Go symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]
        symbol_types = [s['type'] for s in symbols]

        assert 'main' in symbol_names, "Should find main function"
        assert 'add' in symbol_names, "Should find add function"
        assert 'Person' in symbol_names, "Should find Person struct"
        assert 'Speaker' in symbol_names, "Should find Speaker interface"

        print("\n✅ Go symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_go_symbols()
