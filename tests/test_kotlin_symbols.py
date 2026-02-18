#!/usr/bin/env python3
"""Test Kotlin symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_kotlin_symbols():
    """Test that Kotlin symbols are extracted correctly."""

    # Create a test Kotlin file
    test_content = """
// A simple class
class Person(val name: String, val age: Int) {
    fun greet(): String {
        return "Hello, I'm $name"
    }
}

// An interface
interface Speaker {
    fun speak(): String
}

// An object (singleton)
object Config {
    const val VERSION = "1.0"
}

// Data class
data class Point(val x: Int, val y: Int)

// Companion object
class MyClass {
    companion object {
        fun create() = MyClass()
    }
}

// Top-level function
fun sayHello() {
    println("Hello!")
}

// Variable declaration
val x: Int = 10
"""

    # Create temp file
    test_file = Path("test_example.kt")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "kotlin", Path(__file__).parent)

        # Check results
        print(f"Kotlin symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert 'Speaker' in symbol_names, "Should find Speaker interface"
        assert 'Config' in symbol_names, "Should find Config object"
        assert 'sayHello' in symbol_names, "Should find sayHello function"

        print("\n✅ Kotlin symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_kotlin_symbols()
