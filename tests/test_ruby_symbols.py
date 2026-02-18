#!/usr/bin/env python3
"""Test Ruby symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_ruby_symbols():
    """Test that Ruby symbols are extracted correctly."""

    # Create a test Ruby file
    test_content = """
# A simple class
class Person
  attr_accessor :name, :age

  def initialize(name, age)
    @name = name
    @age = age
  end

  def greet
    "Hello, I'm #{@name}"
  end
end

# A module
module MathUtils
  def self.add(a, b)
    a + b
  end
end

# A standalone method
def say_hello
  puts "Hello!"
end

# Variable assignment
x = 10
y = "hello"
"""

    # Create temp file
    test_file = Path("test_example.rb")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "ruby", Path(__file__).parent)

        # Check results
        print(f"Ruby symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert 'initialize' in symbol_names or 'greet' in symbol_names, "Should find methods"
        assert 'MathUtils' in symbol_names, "Should find MathUtils module"

        print("\n✅ Ruby symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_ruby_symbols()
