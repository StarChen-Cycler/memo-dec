#!/usr/bin/env python3
"""Test YAML symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_yaml_symbols():
    """Test that YAML symbols are extracted correctly."""

    # Create a test YAML file
    test_content = """
# Application configuration
app:
  name: MyApp
  version: 1.0
  database:
    host: localhost
    port: 5432

# Server settings
server:
  host: 0.0.0.0
  port: 8080
  ssl:
    enabled: true
    cert_path: /etc/certs

# Logging
logging:
  level: INFO
  format: json
"""

    # Create temp file
    test_file = Path("test_example.yaml")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "yaml", Path(__file__).parent)

        # Check results
        print(f"YAML symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols (keys)
        symbol_names = [s['name'] for s in symbols]

        assert any('app' in s or 'name' in s for s in symbol_names), "Should find YAML keys"

        print("\n✅ YAML symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_yaml_symbols()
