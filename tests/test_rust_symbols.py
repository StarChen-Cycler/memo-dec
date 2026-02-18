#!/usr/bin/env python3
"""Test Rust symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_rust_symbols():
    """Test that Rust symbols are extracted correctly."""

    # Create a test Rust file
    test_content = """
// Main function
fn main() {
    println!("Hello, World!");
}

// A simple function
fn add(a: i32, b: i32) -> i32 {
    a + b
}

// A struct
struct Person {
    name: String,
    age: u32,
}

// An enum
enum Color {
    Red,
    Green,
    Blue,
}

// A trait
trait Speaker {
    fn speak(&self) -> String;
}

// impl block with method
impl Speaker for Person {
    fn speak(&self) -> String {
        String::from("Hello")
    }
}

// Variable declaration
let x: i32 = 10;
"""

    # Create temp file
    test_file = Path("test_example.rs")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "rust", Path(__file__).parent)

        # Check results
        print(f"Rust symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'main' in symbol_names, "Should find main function"
        assert 'add' in symbol_names, "Should find add function"
        assert 'Person' in symbol_names, "Should find Person struct"
        assert 'Color' in symbol_names, "Should find Color enum"
        assert 'Speaker' in symbol_names, "Should find Speaker trait"

        print("\n✅ Rust symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_rust_symbols()
