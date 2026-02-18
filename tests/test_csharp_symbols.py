#!/usr/bin/env python3
"""Test C# symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_csharp_symbols():
    """Test that C# symbols are extracted correctly."""

    # Create a test C# file
    test_content = """
using System;

// A simple class
public class Person {
    private string name;
    private int age;

    public Person(string name, int age) {
        this.name = name;
        this.age = age;
    }

    public string Greet() {
        return $"Hello, I'm {name}";
    }
}

// An interface
public interface ISpeaker {
    string Speak();
}

// A struct
public struct Point {
    public int X;
    public int Y;
}

// Local function example
public class Example {
    public void Method() {
        int localFunction() => 42;
    }
}
"""

    # Create temp file
    test_file = Path("test_example.cs")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "csharp", Path(__file__).parent)

        # Check results
        print(f"C# symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert 'ISpeaker' in symbol_names, "Should find ISpeaker interface"
        assert 'Point' in symbol_names, "Should find Point struct"
        assert 'Greet' in symbol_names, "Should find Greet method"

        print("\n✅ C# symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_csharp_symbols()
