#!/usr/bin/env python3
"""Test TOML symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_toml_symbols():
    """Test that TOML symbols are extracted correctly."""

    # Create a test TOML file
    test_content = """
# Application configuration
app_name = "MyApp"
version = "1.0.0"

[database]
host = "localhost"
port = 5432
name = "mydb"

[server]
host = "0.0.0.0"
port = 8080

[server.ssl]
enabled = true
cert_path = "/etc/certs"

[logging]
level = "INFO"
format = "json"
"""

    # Create temp file
    test_file = Path("test_example.toml")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "toml", Path(__file__).parent)

        # Check results
        print(f"TOML symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols (keys)
        symbol_names = [s['name'] for s in symbols]

        assert any('app_name' in s or 'database' in s for s in symbol_names), "Should find TOML keys"

        print("\n✅ TOML symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_toml_symbols()
