#!/usr/bin/env python3
"""
Tree-sitter symbol extractor for multiple programming languages.
Based on: @memo-dec/extract_symbols_final.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime

try:
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
    from tree_sitter_embedded_template import language as embedded_template_language
    # Additional language support
    from tree_sitter_go import language as go_language
    from tree_sitter_rust import language as rust_language
    from tree_sitter_ruby import language as ruby_language
    from tree_sitter_php import language_php as php_language
    from tree_sitter_c_sharp import language as c_sharp_language
    from tree_sitter_kotlin import language as kotlin_language
    from tree_sitter_swift import language as swift_language
    from tree_sitter_scala import language as scala_language
    from tree_sitter_bash import language as bash_language
    from tree_sitter_yaml import language as yaml_language
    from tree_sitter_toml import language as toml_language
    from tree_sitter_sql import language as sql_language

    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Tree-sitter not available: {e}")
    print("Install with: pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-c tree-sitter-java tree-sitter-markdown tree-sitter-html tree-sitter-json tree-sitter-embedded-template tree-sitter-go tree-sitter-rust tree-sitter-ruby tree-sitter-php tree-sitter-c-sharp tree-sitter-kotlin tree-sitter-swift tree-sitter-scala tree-sitter-bash tree-sitter-yaml tree-sitter-toml tree-sitter-sql")
    TREE_SITTER_AVAILABLE = False


# Map file extensions to language functions
LANGUAGE_MAP = {
    '.py': python_language if TREE_SITTER_AVAILABLE else None,
    '.js': js_language if TREE_SITTER_AVAILABLE else None,
    '.ts': ts_language if TREE_SITTER_AVAILABLE else None,
    '.tsx': tsx_language if TREE_SITTER_AVAILABLE else None,
    '.jsx': tsx_language if TREE_SITTER_AVAILABLE else None,  # Use TSX parser for JSX
    '.c': c_language if TREE_SITTER_AVAILABLE else None,
    '.cpp': c_language if TREE_SITTER_AVAILABLE else None,
    '.cc': c_language if TREE_SITTER_AVAILABLE else None,
    '.h': c_language if TREE_SITTER_AVAILABLE else None,
    '.java': java_language if TREE_SITTER_AVAILABLE else None,
    '.md': md_language if TREE_SITTER_AVAILABLE else None,
    '.html': html_language if TREE_SITTER_AVAILABLE else None,
    '.htm': html_language if TREE_SITTER_AVAILABLE else None,
    '.json': json_language if TREE_SITTER_AVAILABLE else None,
    '.vue': html_language if TREE_SITTER_AVAILABLE else None,
    '.ipynb': python_language if TREE_SITTER_AVAILABLE else None,  # Jupyter notebooks contain Python code
    # Additional languages
    '.go': go_language if TREE_SITTER_AVAILABLE else None,
    '.rs': rust_language if TREE_SITTER_AVAILABLE else None,
    '.rb': ruby_language if TREE_SITTER_AVAILABLE else None,
    '.php': php_language if TREE_SITTER_AVAILABLE else None,
    '.cs': c_sharp_language if TREE_SITTER_AVAILABLE else None,
    '.kt': kotlin_language if TREE_SITTER_AVAILABLE else None,
    '.kts': kotlin_language if TREE_SITTER_AVAILABLE else None,
    '.swift': swift_language if TREE_SITTER_AVAILABLE else None,
    '.scala': scala_language if TREE_SITTER_AVAILABLE else None,
    '.sh': bash_language if TREE_SITTER_AVAILABLE else None,
    '.bash': bash_language if TREE_SITTER_AVAILABLE else None,
    '.yml': yaml_language if TREE_SITTER_AVAILABLE else None,
    '.yaml': yaml_language if TREE_SITTER_AVAILABLE else None,
    '.toml': toml_language if TREE_SITTER_AVAILABLE else None,
    '.sql': sql_language if TREE_SITTER_AVAILABLE else None,
}

# Map extensions to language names for query lookup
LANG_NAME_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.jsx': 'javascript',
    '.c': 'c', '.cpp': 'c', '.cc': 'c', '.h': 'c',
    '.java': 'java',
    '.md': 'markdown',
    '.html': 'html', '.htm': 'html',
    '.json': 'json',
    '.vue': 'vue',
    '.ipynb': 'python',  # Jupyter notebooks
    # Additional languages
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.cs': 'c_sharp',
    '.kt': 'kotlin', '.kts': 'kotlin',
    '.swift': 'swift',
    '.scala': 'scala',
    '.sh': 'bash', '.bash': 'bash',
    '.yml': 'yaml', '.yaml': 'yaml',
    '.toml': 'toml',
    '.sql': 'sql',
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
    'typescript': {
        'function': '''
            (function_declaration name: (identifier) @name)
            (method_definition name: (property_identifier) @name)
            (variable_declarator
                name: (identifier) @name
                value: (function_expression)
            )
        ''',
        'class': '''
            (class_declaration name: (type_identifier) @name)
            (abstract_class_declaration name: (type_identifier) @name)
        ''',
        'variable': '(variable_declarator name: (identifier) @name)',
        'component': '''
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function)
            )
        ''',
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
        'tag': '(tag_name) @name',
        'attribute': '(attribute) @name',
    },
    'vue': {
        'tag': '(tag_name) @name',
        'attribute': '(attribute) @name',
    },
    'markdown': {
        'heading': '(atx_heading (inline) @name)',
    },
    # Additional language queries
    'go': {
        'function': '''
            (function_declaration name: (identifier) @name)
            (method_declaration name: (field_identifier) @name)
        ''',
        'class': '(type_spec name: (type_identifier) @name)',
        'variable': '(short_var_declaration left: (expression_list (identifier) @name))',
    },
    'rust': {
        'function': '''
            (function_item name: (identifier) @name)
        ''',
        'class': '''
            (struct_item name: (type_identifier) @name)
            (enum_item name: (type_identifier) @name)
            (trait_item name: (type_identifier) @name)
        ''',
        'variable': '(let_declaration pattern: (identifier) @name)',
    },
    'ruby': {
        'function': '''
            (method name: (identifier) @name)
            (singleton_method name: (identifier) @name)
        ''',
        'class': '''
            (class name: (constant) @name)
            (module name: (constant) @name)
        ''',
        'variable': '(assignment left: (variable) @name)',
    },
    'php': {
        'function': '''
            (function_definition name: (name) @name)
            (method_declaration name: (name) @name)
        ''',
        'class': '(class_declaration name: (name) @name)',
        'variable': '''
            (assignment left: (variable_name) @name)
            (expression_statement (assignment left: (variable_base) @name))
        ''',
    },
    'c_sharp': {
        'function': '''
            (method_declaration name: (identifier) @name)
            (local_function_statement name: (identifier) @name)
        ''',
        'class': '''
            (class_declaration name: (identifier) @name)
            (interface_declaration name: (identifier) @name)
            (struct_declaration name: (identifier) @name)
        ''',
        'variable': '''
            (variable_declaration (variable_declarator name: (identifier) @name))
            (field_declaration (variable_declarator name: (identifier) @name))
        ''',
    },
    'kotlin': {
        'function': '''
            (function_declaration (identifier) @name)
        ''',
        'class': '''
            (class_declaration (identifier) @name)
            (object_declaration (identifier) @name)
        ''',
        'variable': '''
            (property_declaration (identifier) @name)
        ''',
    },
    'swift': {
        'function': '''
            (function_declaration name: (simple_identifier) @name)
        ''',
        'class': '''
            (class_declaration name: (type_identifier) @name)
            (protocol_declaration name: (type_identifier) @name)
        ''',
        'variable': '''
            (variable_declaration name: (simple_identifier) @name)
        ''',
    },
    'scala': {
        'function': '''
            (function_definition name: (identifier) @name)
        ''',
        'class': '''
            (class_definition name: (identifier) @name)
            (trait_definition name: (identifier) @name)
            (object_definition name: (identifier) @name)
        ''',
        'variable': '(val_definition name: (identifier) @name)',
    },
    'bash': {
        'function': '''
            (function_definition name: (word) @name)
        ''',
        'variable': '(variable_assignment name: (variable_name) @name)',
    },
    'yaml': {
        'key': '(block_mapping_pair key: (flow_node) @name)',
    },
    'toml': {
        'key': '(pair (bare_key) @name)',
    },
    'sql': {
        'table': '(object_reference name: (identifier) @name)',
        'function': '''
            (create_function_routine name: (identifier) @name)
            (call_expression function: (object_reference name: (identifier) @name))
        ''',
    },
}


def extract_symbols_from_notebook(file_path):
    """
    Extract symbols from a Jupyter notebook (.ipynb) file.

    Args:
        file_path (Path): Path to .ipynb file

    Returns:
        list: List of symbol dictionaries with keys: file, line, type, name
    """
    if not TREE_SITTER_AVAILABLE:
        return []

    try:
        # Read and parse the notebook JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        # Initialize Python parser
        lang_func = python_language
        lang_key = 'python'

        lang = Language(lang_func())
        parser = Parser(lang)

        results = []
        cell_offset = 0  # Track cumulative line offset from previous cells

        if lang_key not in QUERIES:
            return results

        # Process each cell
        for cell_idx, cell in enumerate(notebook.get('cells', [])):
            # Only process code cells
            if cell.get('cell_type') != 'code':
                continue

            # Get the source code from the cell
            source = cell.get('source', [])
            if isinstance(source, list):
                # Join lines if source is a list
                code = ''.join(source)
            else:
                # Source might be a string in some formats
                code = source

            if not code.strip():
                continue  # Skip empty cells

            # Parse the code in this cell
            try:
                code_bytes = code.encode('utf-8')
                tree = parser.parse(code_bytes)

                # Process each query type for Python
                for symbol_type, query_str in QUERIES[lang_key].items():
                    try:
                        query = Query(lang, query_str)
                        cursor = QueryCursor(query)

                        for match in cursor.matches(tree.root_node):
                            capture_dict = match[1]

                            # Get the capture name
                            capture_names = list(capture_dict.keys())
                            if not capture_names:
                                continue

                            capture_name = capture_names[0]
                            if not capture_dict[capture_name]:
                                continue

                            # Get the first captured node
                            node = capture_dict[capture_name][0]

                            # Extract name from the node
                            if node.type == 'identifier':
                                name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')
                            else:
                                name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')

                            if name:
                                # Calculate line number: cell start + line in cell
                                line_in_cell = node.start_point[0] + 1
                                total_line = cell_offset + line_in_cell

                                results.append({
                                    'file': str(file_path),
                                    'line': total_line,
                                    'type': symbol_type,
                                    'name': name,
                                    'cell': cell_idx + 1  # Add cell number for notebooks
                                })

                    except Exception:
                        continue

            except Exception:
                # Skip this cell if parsing fails
                pass

            # Update offset for next cell (count lines in current cell)
            cell_offset += len(code.split('\n'))

        return results

    except Exception:
        return []


def extract_symbols_from_vue(file_path):
    """
    Extract symbols from a Vue Single-File Component (.vue) file.

    Parses <script> and <template> blocks separately with appropriate parsers.
    Supports:
    - <script setup> (Composition API)
    - <script> (Options API)
    - <script lang="ts"> (TypeScript)
    - <template> (HTML)

    Args:
        file_path (Path): Path to .vue file

    Returns:
        list: List of symbol dictionaries with keys: file, line, type, name
    """
    import re

    if not TREE_SITTER_AVAILABLE:
        return []

    try:
        content = file_path.read_text(encoding='utf-8')
        results = []

        # === Extract and parse <script> block(s) ===
        # Match <script>, <script setup>, <script lang="ts">, etc.
        script_pattern = r'<script\b[^>]*?(?:\s+lang\s*=\s*["\'](\w+)["\'])?[^>]*>(.*?)</script>'
        script_matches = list(re.finditer(script_pattern, content, re.DOTALL | re.IGNORECASE))

        for match in script_matches:
            lang_attr = match.group(1)  # Language attribute (e.g., 'ts', 'tsx')
            script_content = match.group(2)  # Script content

            if not script_content.strip():
                continue

            # Calculate line offset for this script block
            text_before = content[:match.start()]
            line_offset = text_before.count('\n')

            # Determine which parser to use
            if lang_attr and lang_attr.lower() in ('ts', 'typescript'):
                lang_func = ts_language
                lang_key = 'typescript'
            else:
                # Default to JavaScript for <script> blocks
                lang_func = js_language
                lang_key = 'javascript'

            try:
                lang = Language(lang_func())
                parser = Parser(lang)
                code_bytes = script_content.encode('utf-8')
                tree = parser.parse(code_bytes)

                if lang_key in QUERIES:
                    for symbol_type, query_str in QUERIES[lang_key].items():
                        try:
                            query = Query(lang, query_str)
                            cursor = QueryCursor(query)

                            for m in cursor.matches(tree.root_node):
                                capture_dict = m[1]
                                capture_names = list(capture_dict.keys())
                                if not capture_names:
                                    continue

                                capture_name = capture_names[0]
                                if not capture_dict[capture_name]:
                                    continue

                                node = capture_dict[capture_name][0]

                                # Extract name
                                if node.type == 'identifier':
                                    name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')
                                else:
                                    name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')

                                if name:
                                    # Calculate actual line number in original file
                                    # Formula: line_offset + node.start_point[0] + 1
                                    # - line_offset = newlines before <script> tag (0-indexed line of <script>)
                                    # - node.start_point[0] = 0-indexed line within script content
                                    # - +1 to convert to 1-indexed line number
                                    actual_line = line_offset + node.start_point[0] + 1

                                    results.append({
                                        'file': str(file_path),
                                        'line': actual_line,
                                        'type': symbol_type,
                                        'name': name,
                                        'block': 'script'
                                    })
                        except Exception:
                            continue
            except Exception:
                continue

        # === Extract and parse <template> block ===
        template_pattern = r'<template\b[^>]*>(.*?)</template>'
        template_match = re.search(template_pattern, content, re.DOTALL | re.IGNORECASE)

        if template_match:
            template_content = template_match.group(1)
            text_before = content[:template_match.start()]
            line_offset = text_before.count('\n')

            if template_content.strip():
                try:
                    lang = Language(html_language())
                    parser = Parser(lang)
                    code_bytes = template_content.encode('utf-8')
                    tree = parser.parse(code_bytes)

                    # Use HTML queries for template
                    for symbol_type, query_str in QUERIES['html'].items():
                        try:
                            query = Query(lang, query_str)
                            cursor = QueryCursor(query)

                            for m in cursor.matches(tree.root_node):
                                capture_dict = m[1]
                                capture_names = list(capture_dict.keys())
                                if not capture_names:
                                    continue

                                capture_name = capture_names[0]
                                if not capture_dict[capture_name]:
                                    continue

                                node = capture_dict[capture_name][0]
                                name = code_bytes[node.start_byte:node.end_byte].decode('utf-8')

                                if name:
                                    # Calculate actual line number in original file
                                    # Formula: line_offset + node.start_point[0] + 1
                                    # - line_offset = newlines before <template> tag (0-indexed line of <template>)
                                    # - node.start_point[0] = 0-indexed line within template content
                                    # - +1 to convert to 1-indexed line number
                                    actual_line = line_offset + node.start_point[0] + 1

                                    results.append({
                                        'file': str(file_path),
                                        'line': actual_line,
                                        'type': symbol_type,
                                        'name': name,
                                        'block': 'template'
                                    })
                        except Exception:
                            continue
                except Exception:
                    pass

        # Sort by line number
        results.sort(key=lambda x: x['line'])
        return results

    except Exception:
        return []


def should_ignore_path(path, ignore_patterns=None):
    """
    Check if a path should be ignored based on patterns.

    Args:
        path (Path): Path to check
        ignore_patterns (list): List of glob patterns to ignore

    Returns:
        bool: True if path should be ignored
    """
    if ignore_patterns is None:
        ignore_patterns = []

    import fnmatch

    # Try to get relative path for better pattern matching
    try:
        rel_path = path.relative_to(Path.cwd()) if path.is_absolute() else path
        rel_path_str = str(rel_path)
    except ValueError:
        # Path is not a subpath of cwd, use absolute path
        rel_path = path
        rel_path_str = str(path)

    # For absolute path checking, get the absolute path string
    abs_path_str = str(path.resolve()) if not path.is_absolute() else str(path)
    path_name = path.name

    # Check if any pattern matches
    for pattern in ignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            # Match files inside the directory: pattern* (e.g., .memo/*)
            dir_pattern = pattern.rstrip('/') + '/*'
            # Or match the directory itself
            dir_self = pattern.rstrip('/')

            if fnmatch.fnmatch(rel_path_str, dir_pattern):
                return True
            if fnmatch.fnmatch(rel_path_str, dir_self):
                return True
            if fnmatch.fnmatch(path.name, dir_self):
                return True

            # Check if path is inside the directory
            rel_path_parts = rel_path_str.replace('\\', '/').split('/')
            dir_parts = dir_self.replace('\\', '/').split('/')
            if len(rel_path_parts) >= len(dir_parts) and rel_path_parts[:len(dir_parts)] == dir_parts:
                return True

            # Check if any parent matches the directory
            for parent in path.parents:
                try:
                    parent_rel = parent.relative_to(Path.cwd())
                    if str(parent_rel).replace('\\', '/') == dir_self:
                        return True
                except ValueError:
                    # parent not relative to cwd, use absolute
                    if str(parent) == pattern.rstrip('/'):
                        return True
        else:
            # Regular file pattern
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(path_name, pattern):
                return True

            # Check if any parent directory matches
            for parent in path.parents:
                try:
                    parent_rel = parent.relative_to(Path.cwd())
                    if fnmatch.fnmatch(str(parent_rel).replace('\\', '/'), pattern):
                        return True
                except ValueError:
                    # parent not relative to cwd, use absolute
                    if fnmatch.fnmatch(str(parent), pattern):
                        return True

    return False


def load_ignore_patterns(memo_dir=None):
    """
    Load ignore patterns from .memo/.memoignore file.

    Args:
        memo_dir (Path, optional): Path to .memo directory

    Returns:
        list: List of ignore patterns
    """
    if memo_dir is None:
        memo_dir = Path.cwd() / '.memo'

    ignore_file = memo_dir / '.memoignore'
    patterns = []

    if ignore_file.exists():
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .memoignore: {e}", file=sys.stderr)

    return patterns


def extract_symbols(file_path):
    """
    Extract symbols from a source file using tree-sitter.

    Args:
        file_path (Path): Path to source file

    Returns:
        list: List of symbol dictionaries with keys: file, line, type, name
    """
    if not TREE_SITTER_AVAILABLE:
        return []

    ext = file_path.suffix

    # Special handling for Jupyter notebooks
    if ext == '.ipynb':
        return extract_symbols_from_notebook(file_path)

    # Special handling for Vue Single-File Components
    if ext == '.vue':
        return extract_symbols_from_vue(file_path)

    if ext not in LANGUAGE_MAP:
        return []

    try:
        # Read file
        code_bytes = file_path.read_bytes()

        # Initialize language and parser
        lang_func = LANGUAGE_MAP[ext]
        if lang_func is None:
            return []

        lang_key = LANG_NAME_MAP[ext]

        lang = Language(lang_func())
        parser = Parser(lang)

        # Parse
        tree = parser.parse(code_bytes)

        results = []

        if lang_key not in QUERIES:
            return results

        # Process each query type
        for symbol_type, query_str in QUERIES[lang_key].items():
            try:
                # Create query
                query = Query(lang, query_str)

                # Execute query
                cursor = QueryCursor(query)

                # Process each match
                for match in cursor.matches(tree.root_node):
                    capture_dict = match[1]

                    # Get the capture name
                    capture_names = list(capture_dict.keys())
                    if not capture_names:
                        continue

                    capture_name = capture_names[0]
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

            except Exception:
                continue

        return results

    except Exception:
        return []


def extract_symbols_from_directory(directory_path, recursive=True):
    """
    Extract symbols from all supported files in a directory.

    Args:
        directory_path (Path): Directory to scan
        recursive (bool): Whether to scan recursively

    Returns:
        list: List of all symbols found
    """
    if not directory_path.is_dir():
        return []

    all_symbols = []
    ignore_patterns = load_ignore_patterns()
    ignore_dir_cache = set()  # Cache directories that should be ignored

    # Use os.walk for efficient directory traversal
    import os

    # Walk directory tree
    if recursive:
        walker = os.walk(directory_path)
    else:
        walker = [(str(directory_path), [], os.listdir(directory_path))]

    for root, dirs, files in walker:
        root_path = Path(root)

        # Check if this directory should be ignored (use cache for efficiency)
        cache_key = str(root_path)
        if cache_key in ignore_dir_cache:
            # Skip this directory and all subdirectories
            dirs.clear()  # Prevents os.walk from recursing into subdirs
            continue

        # Check if directory should be ignored
        if should_ignore_path(root_path, ignore_patterns):
            ignore_dir_cache.add(cache_key)
            dirs.clear()  # Prevents os.walk from recursing into subdirs
            continue

        # Process files in this directory
        for file_name in files:
            file_path = root_path / file_name

            # Check extension first (faster than ignore check)
            if file_path.suffix not in LANGUAGE_MAP:
                continue

            # Skip if file should be ignored
            if should_ignore_path(file_path, ignore_patterns):
                continue

            # Process the file
            all_symbols.extend(extract_symbols(file_path))

    # Sort by file and line
    all_symbols.sort(key=lambda x: (x['file'], x['line']))

    return all_symbols


def format_symbols(symbols, format_type='table'):
    """
    Format symbols for display.

    Args:
        symbols (list): List of symbol dictionaries
        format_type (str): Format type: 'table', 'json', 'markdown'

    Returns:
        str: Formatted output
    """
    if not symbols:
        return "No symbols found."

    if format_type == 'json':
        return json.dumps(symbols, indent=2)

    elif format_type == 'markdown':
        output = "## Code Symbols\n\n"
        output += "| File | Line | Type | Name |\n"
        output += "|------|------|------|------|\n"
        for sym in symbols:
            file_short = str(Path(sym['file']).relative_to(Path.cwd())) if sym['file'].startswith(str(Path.cwd())) else sym['file']
            output += f"| {file_short} | {sym['line']} | {sym['type']} | {sym['name']} |\n"
        return output

    else:  # table format (ultra compact - 50 per line)
        from collections import defaultdict
        symbols_by_file = defaultdict(list)
        for sym in symbols:
            if sym['file'].startswith(str(Path.cwd())):
                file_short = str(Path(sym['file']).relative_to(Path.cwd()))
            else:
                file_short = sym['file']
            symbols_by_file[file_short].append(sym)

        output = "Memo-dec Symbols (ultra compact - 100 per line):\n" + "-" * 80 + f"\nTotal symbols: {len(symbols)}\n\n"

        # Display symbols in horizontal format (50 per line)
        for file_path, file_symbols in sorted(symbols_by_file.items()):
            output += f"{file_path}\n"

            line_groups = []
            for i in range(0, len(file_symbols), 100):  # 100 symbols per line
                group = file_symbols[i:i+50]
                line_parts = []
                for sym in group:
                    # Format: line:type[:3]:name (compact)
                    line_parts.append(f"{sym['line']}:{sym['type'][:3]}:{sym['name']}")
                line_groups.append(" ".join(line_parts))  # Single space separator

            for line in line_groups:
                output += f"{line}\n"
            output += "\n"

        return output


def save_symbols_to_file(symbols, output_path):
    """
    Save symbols to a file.

    Args:
        symbols (list): List of symbol dictionaries
        output_path (Path): Path to save file

    Returns:
        Path: Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(format_symbols(symbols, 'table'))

    return output_path
