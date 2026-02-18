#!/usr/bin/env python3
"""Test Swift symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_swift_symbols():
    """Test that Swift symbols are extracted correctly."""

    # Create a test Swift file
    test_content = """
import Foundation

// A simple class
class Person {
    var name: String
    var age: Int

    init(name: String, age: Int) {
        self.name = name
        self.age = age
    }

    func greet() -> String {
        return "Hello, I'm \(name)"
    }
}

// A struct
struct Point {
    var x: Int
    var y: Int
}

// An enum
enum Color {
    case red
    case green
    case blue
}

// A protocol
protocol Speaker {
    func speak() -> String
}

// Extension
extension Person: Speaker {
    func speak() -> String {
        return greet()
    }
}

// Variable declaration
let x: Int = 10
var y: String = "hello"
"""

    # Create temp file
    test_file = Path("test_example.swift")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "swift", Path(__file__).parent)

        # Check results
        print(f"Swift symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert 'Point' in symbol_names, "Should find Point struct"
        assert 'Color' in symbol_names, "Should find Color enum"
        assert 'Speaker' in symbol_names, "Should find Speaker protocol"
        assert 'greet' in symbol_names, "Should find greet method"

        print("\n✅ Swift symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_swift_symbols()
