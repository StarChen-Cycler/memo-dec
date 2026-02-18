#!/usr/bin/env python3
"""
Tree-sitter symbol extractor for multiple programming languages.
Compatible with py-tree-sitter v0.25+ API.
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from tree_sitter import Language, Parser, Query, QueryCursor

# Import language modules
from tree_sitter_python import language as python_language
from tree_sitter_javascript import language as js_language
from tree_sitter_typescript import language_typescript as ts_language, language_tsx as tsx_language
from tree_sitter_c import language as c_language
from tree_sitter_java import language as java_language
from tree_sitter_markdown import language as md_language
from tree_sitter_html import language as html_language
from tree_sitter_json import language as json_language

# Map file extensions to language functions
LANGUAGE_MAP = {
    '.py': python_language,
    '.js': js_language,
    '.ts': ts_language,
    '.tsx': tsx_language,
    '.c': c_language,
    '.cpp': c_language,
    '.cc': c_language,
    '.h': c_language,
    '.java': java_language,
    '.md': md_language,
    '.html': html_language,
    '.htm': html_language,
    '.json': json_language,
}

# Tree-sitter queries for extracting symbols
QUERIES = {
    'python': {
        'function': '(function_definition name: (identifier) @name)',
        'class': '(class_definition name: (identifier) @name)',
        'variable': '(assignment left: (identifier) @name)',
    },
    'javascript': {
        'function': '(function_declaration name: (identifier) @name)',
        'class': '(class_declaration name: (identifier) @name)',
        'variable': '(variable_declarator name: (identifier) @name)',
    },
    'c': {
        'function': '(function_declarator declarator: (identifier) @name)',
        'variable': '(declaration declarator: (identifier) @name)',
    },
    'java': {
        'function': '(method_declaration name: (identifier) @name)',
        'class': '(class_declaration name: (identifier) @name)',
        'variable': '(field_declaration declarator: (variable_declarator name: (identifier) @name))',
    },
    'json': {
        'key': '(pair key: (string) @name)',
    },
    'html': {
        'attribute': '(attribute) @name',
    },
    'markdown': {
        'heading': '(atx_heading (inline) @name)',
    },
}

# Map extensions to language names for query lookup
LANG_NAME_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'javascript',
    '.tsx': 'javascript',
    '.c': 'c', '.cpp': 'c', '.cc': 'c', '.h': 'c',
    '.java': 'java',
    '.md': 'markdown',
    '.html': 'html', '.htm': 'html',
    '.json': 'json',
}

# Files and folders to ignore (skip during directory traversal)
IGNORED_FILES = {
    # Common temporary and editor files
    '.DS_Store', 'Thumbs.db', '*.tmp', '*.temp',
    '.gitignore', '.editorconfig', '.env', '*.log',
    # Editor swap files
    '*.swp', '*.swo', '*~', '.*.swp',
    # IDE files
    '.vscode', '.idea', '*.sublime-*',
    # OS files
    'desktop.ini', '.directory',
}

IGNORED_FOLDERS = {
    # Version control
    '.git', '.svn', '.hg',
    # Dependencies and build artifacts
    'node_modules', 'venv', 'env', '__pycache__', '.pytest_cache',
    'build', 'dist', 'out', 'target',
    # IDE folders
    '.vscode', '.idea',
    # OS folders
    '.Trash', '$Recycle.Bin',
}

# Helper function to check if a path should be ignored
def should_ignore(path, is_dir=False):
    """Check if a file or folder should be ignored."""
    name = path.name

    # Check exact matches
    if is_dir:
        return name in IGNORED_FOLDERS
    else:
        # Check exact filename matches
        if name in IGNORED_FILES:
            return True

        # Check wildcard patterns
        for pattern in IGNORED_FILES:
            if '*' in pattern:
                if pattern.startswith('*') and name.endswith(pattern[1:]):
                    return True
                if pattern.endswith('*') and name.startswith(pattern[:-1]):
                    return True

    return False

def extract_symbols(file_path):
    """Extract symbols from a source file using tree-sitter."""
    ext = file_path.suffix
    if ext not in LANGUAGE_MAP:
        return []

    try:
        # Read file
        code_bytes = file_path.read_bytes()

        # Initialize language and parser
        lang_func = LANGUAGE_MAP[ext]
        lang = Language(lang_func())
        parser = Parser(lang)

        # Parse
        tree = parser.parse(code_bytes)

        results = []
        lang_key = LANG_NAME_MAP[ext]

        if lang_key not in QUERIES:
            return results

        # Process each query type
        for symbol_type, query_str in QUERIES[lang_key].items():
            try:
                # Create query
                query = Query(lang, query_str)

                # Execute query
                cursor = QueryCursor(query)
                matches = cursor.matches(tree.root_node)

                # Process each match
                for match in matches:
                    capture_dict = match[1]

                    # Get the capture name (could be 'name' or other)
                    capture_names = list(capture_dict.keys())
                    if not capture_names:
                        continue

                    capture_name = capture_names[0]  # Get first capture
                    if not capture_dict[capture_name]:
                        continue

                    # Get the first captured node
                    node = capture_dict[capture_name][0]

                    # Extract name from the node
                    if lang_key == 'json' and node.type == 'string':
                        name = code_bytes[node.start_byte:node.end_byte].decode('utf-8').strip('"')
                    elif node.type == 'identifier':
                        name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')
                    else:
                        name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')

                    if name:
                        line_num = node.start_point[0] + 1

                        results.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': symbol_type,
                            'name': name
                        })

            except Exception as e:
                print(f"Warning: {e}", file=sys.stderr)
                continue

        return results

    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract symbols from source code files using tree-sitter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract symbols from a Python file and display only
  python extract_symbols.py my_script.py

  # Extract symbols from the entire src directory and save JSON and TXT outputs
  python extract_symbols.py src --output json txt

  # Process only, don't save any output files
  python extract_symbols.py src --output none

  # Display results and save only JSON (no text report)
  python extract_symbols.py src --output json
        """
    )

    parser.add_argument('path', type=Path,
                        help='File or directory to analyze')
    parser.add_argument('--output', nargs='*', default=['none'],
                        choices=['none', 'json', 'txt'],
                        help='Output formats to save (default: none)')

    args = parser.parse_args()

    path = args.path
    all_symbols = []

    if path.is_file():
        all_symbols.extend(extract_symbols(path))
    else:
        # Process all supported files recursively, respecting ignore lists
        for ext in LANGUAGE_MAP.keys():
            for file_path in path.rglob(f"*{ext}"):
                # Skip if parent folders are ignored
                should_skip = False
                for parent in file_path.parents:
                    if parent == path:
                        break
                    if should_ignore(parent, is_dir=True):
                        should_skip = True
                        break

                if should_skip:
                    continue

                # Skip if file itself should be ignored
                if should_ignore(file_path):
                    continue

                all_symbols.extend(extract_symbols(file_path))

    # Sort results by file and line number
    all_symbols.sort(key=lambda x: (x['file'], x['line']))

    # Print formatted results
    print(f"{'File':<60} {'Line':<6} {'Type':<10} {'Name'}")
    print("-" * 90)

    for sym in all_symbols:
        print(f"{sym['file']:<60} {sym['line']:<6} {sym['type']:<10} {sym['name']}")

    # Print summary
    print(f"\nTotal symbols found: {len(all_symbols)}")

    # Save output files based on CLI flags
    if 'none' not in args.output:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = path.stem if path.is_file() else path.name

        if 'json' in args.output:
            # Save as JSON
            json_file = output_dir / f"{source_name}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(all_symbols, f, indent=2, ensure_ascii=False)
            print(f"\n✓ JSON output saved to: {json_file}")

        if 'txt' in args.output:
            # Save as formatted text
            txt_file = output_dir / f"{source_name}_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write("TREE-SITTER SYMBOL EXTRACTION REPORT\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Source: {path}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total symbols: {len(all_symbols)}\n\n")

                f.write(f"{'File':<60} {'Line':<6} {'Type':<10} {'Name'}\n")
                f.write("-" * 90 + "\n")

                for sym in all_symbols:
                    f.write(f"{sym['file']:<60} {sym['line']:<6} {sym['type']:<10} {sym['name']}\n")

            print(f"✓ Text output saved to: {txt_file}")

if __name__ == "__main__":
    main()
