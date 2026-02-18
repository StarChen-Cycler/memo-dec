#!/usr/bin/env python3
"""Test Scala symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_scala_symbols():
    """Test that Scala symbols are extracted correctly."""

    # Create a test Scala file
    test_content = """
// A simple class
class Person(val name: String, val age: Int) {
  def greet(): String = s"Hello, I'm $name"
}

// A trait
trait Speaker {
  def speak(): String
}

// An object (singleton)
object Config {
  val version = "1.0"
}

// A case class
case class Point(x: Int, y: Int)

// Variable declaration
val x: Int = 10
var y: String = "hello"
"""

    # Create temp file
    test_file = Path("test_example.scala")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "scala", Path(__file__).parent)

        # Check results
        print(f"Scala symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert 'Speaker' in symbol_names, "Should find Speaker trait"
        assert 'Config' in symbol_names, "Should find Config object"
        assert 'Point' in symbol_names, "Should find Point case class"
        assert 'greet' in symbol_names, "Should find greet method"

        print("\n✅ Scala symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_scala_symbols()
