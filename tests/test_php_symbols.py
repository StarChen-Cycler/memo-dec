#!/usr/bin/env python3
"""Test PHP symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_php_symbols():
    """Test that PHP symbols are extracted correctly."""

    # Create a test PHP file
    test_content = """
<?php
// A simple class
class Person {
    private $name;
    private $age;

    public function __construct($name, $age) {
        $this->name = $name;
        $this->age = $age;
    }

    public function greet() {
        return "Hello, I'm " . $this->name;
    }
}

// A standalone function
function say_hello() {
    echo "Hello!";
}

// Variable assignment
$x = 10;
$y = "hello";
?>
"""

    # Create temp file
    test_file = Path("test_example.php")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "php", Path(__file__).parent)

        # Check results
        print(f"PHP symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'Person' in symbol_names, "Should find Person class"
        assert any(s in symbol_names for s in ['__construct', 'greet']), "Should find methods"

        print("\n✅ PHP symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_php_symbols()
