#!/usr/bin/env python3
"""Test SQL symbol extraction."""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memo_dec.symbol_extractor import extract_symbols
from test_helpers import save_test_results


def test_sql_symbols():
    """Test that SQL symbols are extracted correctly."""

    # Create a test SQL file
    test_content = """
-- Create a users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create a function
CREATE FUNCTION get_user_by_id(user_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT id, name, email
    FROM users
    WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;

-- Query with function call
SELECT * FROM get_user_by_id(1);

-- Create another table
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200),
    content TEXT
);
"""

    # Create temp file
    test_file = Path("test_example.sql")
    test_file.write_text(test_content)

    try:
        # Extract symbols
        symbols = extract_symbols(test_file)

        # Save debug output to file
        save_test_results(symbols, "sql", Path(__file__).parent)

        # Check results
        print(f"SQL symbols found: {len(symbols)}")
        for sym in symbols:
            print(f"  {sym['type']}: {sym['name']} (line {sym['line']})")

        # Verify we found expected symbols
        symbol_names = [s['name'] for s in symbols]

        assert 'users' in symbol_names, "Should find users table"
        assert 'posts' in symbol_names, "Should find posts table"
        assert 'get_user_by_id' in symbol_names, "Should find get_user_by_id function"

        print("\n✅ SQL symbol extraction test passed!")

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_sql_symbols()
