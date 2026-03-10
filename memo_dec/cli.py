#!/usr/bin/env python3
"""
Memo-dec CLI entry point with argument parser.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

from .config import Config, ConfigError
from .storage import StorageManager
from .symbol_extractor import extract_symbols_from_directory, format_symbols, save_symbols_to_file
from .history import HistoryManager
from .ignore_manager import IgnoreManager, add_ignore_pattern
from . import tree_generator
from .global_config import GlobalConfigManager


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='Memo-dec: AI Codebase Context Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize memo-dec in current project
  memo-dec init

  # Initialize with AI-powered context generation
  memo-dec init --context

  # Generate intelligent ignore patterns
  memo-dec findignore                         # Current directory
  memo-dec findignore path/to/project         # Specific project directory

  # Add patterns to .memoignore
  memo-dec addignore "*.log" "temp/"          # Add multiple patterns

  # Extract and display symbols
  memo-dec extractsymbols                     # Current directory, text format
  memo-dec extractsymbols json                # JSON format
  memo-dec extractsymbols markdown            # Markdown format
  memo-dec extractsymbols txt path/to/file    # Single file

  # Query stored symbols with filters
  memo-dec getsymbols                         # All symbols, markdown format
  memo-dec getsymbols json .py                # Python files, JSON format
  memo-dec getsymbols txt .js src/            # JS files in src/, text format

  # Generate and save file summaries
  memo-dec summarizedocs                      # Generate summaries for all files
  memo-dec summarizedocs --force              # Force update all files

  # Query stored summaries with filters
  memo-dec getsummary                         # All summaries, markdown format
  memo-dec getsummary json .py                # Python files, JSON format
  memo-dec getsummary txt .js src/            # JS files in src/, text format

  # Update symbols/content with change detection
  memo-dec update --symbols                   # Update symbols (backup + re-extract)
  memo-dec update --content                   # Update content (incremental)
  memo-dec update --all                       # Update both
        """
    )

    # Main commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize memo-dec in current project')
    init_parser.add_argument(
        '--context',
        action='store_true',
        help='Initialize with full context (runs --findignore, --extractsymbols, --summarizedocs)'
    )
    init_parser.description = 'Initialize memo-dec with optional AI-powered setup'

    # Getsymbols command
    getsymbols_parser = subparsers.add_parser('getsymbols', help='Query stored symbols with filters')
    getsymbols_parser.add_argument(
        'output_format',
        nargs='?',
        choices=['markdown', 'json', 'txt'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    getsymbols_parser.add_argument(
        'file_type_filter',
        nargs='?',
        help='File extension filter (e.g., .py, .js)'
    )
    getsymbols_parser.add_argument(
        'filepath',
        nargs='?',
        type=Path,
        default=Path('.'),
        help='Target file or directory (default: current directory)'
    )
    getsymbols_parser.description = 'Get code symbols from stored memosymbols.txt with optional filtering'

    # Getsummary command
    getsummary_parser = subparsers.add_parser('getsummary', help='Query stored summaries with filters')
    getsummary_parser.add_argument(
        'output_format',
        nargs='?',
        choices=['markdown', 'json', 'txt'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    getsummary_parser.add_argument(
        'file_type_filter',
        nargs='?',
        help='File extension filter (e.g., .py, .js)'
    )
    getsummary_parser.add_argument(
        'filepath',
        nargs='?',
        type=Path,
        default=Path('.'),
        help='Target file or directory (default: current directory)'
    )
    getsummary_parser.description = 'Get file summaries from stored memocontent.json with optional filtering'

    # Extractsymbols command
    extractsymbols_parser = subparsers.add_parser('extractsymbols', help='Extract code symbols')
    extractsymbols_parser.add_argument(
        'output_format',
        nargs='?',
        choices=['markdown', 'json', 'txt'],
        default='txt',
        help='Output format (default: txt/table)'
    )
    extractsymbols_parser.add_argument(
        'filepath',
        nargs='?',
        type=Path,
        default=Path('.'),
        help='Target file or directory (default: current directory)'
    )
    extractsymbols_parser.description = 'Extract symbols from code with tree-sitter'

    # Summarizedocs command
    summarizedocs_parser = subparsers.add_parser('summarizedocs', help='Generate file summaries')
    summarizedocs_parser.add_argument(
        '--force',
        action='store_true',
        help='Force update all files regardless of changes'
    )
    summarizedocs_parser.description = 'Generate AI summaries for all project files'

    # Findignore command
    findignore_parser = subparsers.add_parser('findignore', help='Generate intelligent ignore patterns')
    findignore_parser.add_argument(
        'path',
        nargs='?',
        type=Path,
        default=Path('.'),
        help='Target directory (default: current directory)'
    )
    findignore_parser.description = 'Generate AI-powered .memoignore file based on project structure'

    # Addignore command
    addignore_parser = subparsers.add_parser('addignore', help='Add patterns to .memoignore')
    addignore_parser.add_argument(
        'patterns',
        nargs='+',
        help='Patterns to add to .memoignore (e.g., "*.log" "temp/")'
    )
    addignore_parser.description = 'Add ignore patterns to .memoignore file'

    # Update command
    update_parser = subparsers.add_parser('update', help='Update symbols/content with change detection')
    update_parser.add_argument(
        '--symbols',
        action='store_true',
        help='Update symbols (backup current + re-extract)'
    )
    update_parser.add_argument(
        '--content',
        action='store_true',
        help='Update content (incremental update with change detection)'
    )
    update_parser.add_argument(
        '--all',
        action='store_true',
        help='Update both symbols and content'
    )
    update_parser.description = 'Update stored data with change detection and archiving'

    return parser


def main():
    """Main entry point for memo-dec CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == 'init':
            handle_init(args)
        elif args.command == 'getsymbols':
            handle_getsymbols(args)
        elif args.command == 'getsummary':
            handle_getsummary(args)
        elif args.command == 'extractsymbols':
            handle_extractsymbols(args)
        elif args.command == 'summarizedocs':
            handle_summarizedocs(args)
        elif args.command == 'findignore':
            handle_findignore(args)
        elif args.command == 'addignore':
            handle_addignore(args)
        elif args.command == 'update':
            handle_update(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_init(args):
    """Handle init command."""
    print("Initializing memo-dec...")
    print("=" * 60)

    # Check and setup global config
    global_mgr = GlobalConfigManager()
    config_exists = global_mgr.config_exists()

    # Create global config (automatically triggered)
    print("Setting up global configuration...")
    global_config_path = global_mgr.create_global_memoenv()

    if config_exists:
        print(f"✓ Using existing global config: {global_mgr.get_config_file_path()}")
        print()
    else:
        print(f"✓ Global config created at: {global_config_path}")
        print("  Please edit this file with your API credentials")
        print()

    # Create storage manager for project
    storage = StorageManager(Path.cwd())

    # Create .memo directory
    memo_dir = storage.create_memo_dir()
    print(f"✓ Created project memo directory: {memo_dir}")

    # Create default files
    memoignore_path = storage.create_memoignore()
    print(f"✓ Created {memoignore_path}")

    # Create history directories
    hist_dirs = storage.create_history_dirs()
    for hist_dir in hist_dirs:
        print(f"✓ Created {hist_dir}")

    # Create memodocs directory
    memodocs_dir = memo_dir / "memodocs"
    memodocs_dir.mkdir(exist_ok=True)
    print(f"✓ Created {memodocs_dir}")

    # Generate AI Usage Guide
    ai_guide_path = generate_ai_usage_guide(storage)
    if ai_guide_path:
        print(f"✓ Created {ai_guide_path}")

    print("\n" + "=" * 60)
    print("✓ Basic initialization complete!")
    print("\nNext steps:")

    print("1. Please edit your global configuration file:")
    print(f"   {global_mgr.get_config_file_path()}")
    print("   Set your API_BASE_URL and API_AUTH_KEY")

    if not args.context:
        print("\n2. To generate AI-powered context, run:")
        print("   memo-dec init --context")

    print("\nYour project .memo/ directory is ready for use!")

    print("\n" + "=" * 60)

    # Run AI-powered functions if --context flag is set
    if args.context:
        print("Running context generation (--context)...")
        print("=" * 60)

        success = True

        # Step 1: Generate ignore file with AI
        print("\n[Step 1/3] Generating intelligent ignore patterns...")
        try:
            # Load config from global
            try:
                config = Config()

                # Initialize AI client and ignore manager
                from .ai_client import AIClient
                ai_client = AIClient(config)
                ignore_manager = IgnoreManager(ai_client, tree_generator)

                # Generate ignore file with reliability
                ignore_file = ignore_manager.generate_ignore_file_with_reliability(str(Path.cwd()))
                print(f"✓ Ignore generation complete")
            except ConfigError as e:
                print(f"  Note: {e}")
                print("  Skipping --findignore (no API credentials configured yet)")
                print("  Please update your global config file with credentials first")
        except Exception as e:
            print(f"✗ Ignore generation failed: {e}")
            success = False

        # Step 2: Generate and save tree structures (after ignore file created)
        print("\n[Step 2/3] Generating project tree structures...")
        try:
            # Generate and save trees (respecting the newly created ignore patterns)
            tree_paths = storage.save_tree_files(Path.cwd())

            print(f"✓ Tree structures generated:")
            print(f"  - {tree_paths['folder_tree']}")
            print(f"  - {tree_paths['file_tree']}")
        except Exception as e:
            print(f"✗ Tree generation failed: {e}")
            success = False

        # Step 3: Extract symbols
        print("\n[Step 3/3] Extracting code symbols...")
        try:
            extractsymbols_args = argparse.Namespace(
                filepath=Path.cwd(),
                output_format='txt'
            )
            handle_extractsymbols(extractsymbols_args)
            print(f"✓ Symbol extraction complete")
        except Exception as e:
            print(f"✗ Symbol extraction failed: {e}")
            success = False

        if success:
            print("\n" + "=" * 60)
            print("✓ Full context initialization complete!")


def handle_getsymbols(args):
    """
    Handle getsymbols command - query stored symbols with filtering.

    Usage:
        memo-dec getsymbols                           # All symbols, markdown format
        memo-dec getsymbols json .py                  # Python files, JSON format
        memo-dec getsymbols txt .js src/              # JS files in src/, text format
    """
    import json

    target_path = Path(args.filepath) if args.filepath != Path('.') else Path.cwd()
    storage = StorageManager(target_path)
    symbols_path = storage.get_memosymbols_path()

    if not symbols_path.exists():
        print(f"Error: No memosymbols.txt found at {symbols_path}")
        print("Run 'memo-dec extractsymbols' first to generate symbols.")
        sys.exit(1)

    print(f"Querying symbols from {symbols_path}...")
    print(f"Output format: {args.output_format}")
    if args.file_type_filter:
        print(f"File type filter: {args.file_type_filter}")
    print("=" * 60)

    try:
        # Parse the stored symbols file
        symbols = parse_symbols_file(symbols_path)

        if not symbols:
            print("No symbols found in memosymbols.txt")
            return

        # Apply filters
        filtered_symbols = []
        file_type_filter = args.file_type_filter
        path_filter = str(args.filepath) if args.filepath != Path('.') else None

        for sym in symbols:
            # Filter by file type
            if file_type_filter:
                ext = Path(sym['file']).suffix.lower()
                filter_ext = file_type_filter.lower()
                if not filter_ext.startswith('.'):
                    filter_ext = '.' + filter_ext
                if ext != filter_ext:
                    continue

            # Filter by path prefix
            if path_filter and path_filter != '.':
                try:
                    rel_path = Path(sym['file']).relative_to(target_path)
                    if not str(rel_path).startswith(path_filter):
                        continue
                except ValueError:
                    continue

            filtered_symbols.append(sym)

        print(f"Found {len(filtered_symbols)} symbols (filtered from {len(symbols)} total)\n")

        # Output in requested format
        if args.output_format == 'json':
            print(json.dumps(filtered_symbols, indent=2))

        elif args.output_format == 'markdown':
            print("## Code Symbols\n")
            print("| File | Line | Type | Name |")
            print("|------|------|------|------|")
            for sym in filtered_symbols:
                file_short = Path(sym['file']).name
                print(f"| {file_short} | {sym['line']} | {sym['type']} | {sym['name']} |")

        else:  # txt format
            from collections import defaultdict
            symbols_by_file = defaultdict(list)
            for sym in filtered_symbols:
                file_short = Path(sym['file']).name
                symbols_by_file[file_short].append(sym)

            for file_name, file_symbols in sorted(symbols_by_file.items()):
                print(f"\n{file_name}")
                for sym in sorted(file_symbols, key=lambda x: x['line']):
                    print(f"  {sym['line']:4d} {sym['type'][:3]:3s} {sym['name']}")

    except Exception as e:
        print(f"Error reading symbols: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_getsummary(args):
    """
    Handle getsummary command - query stored summaries with filtering.

    Usage:
        memo-dec getsummary                           # All summaries, markdown format
        memo-dec getsummary json .py                  # Python files, JSON format
        memo-dec getsummary txt .js src/              # JS files in src/, text format
    """
    import json

    target_path = Path(args.filepath) if args.filepath != Path('.') else Path.cwd()
    storage = StorageManager(target_path)
    content_path = storage.get_memocontent_path()

    if not content_path.exists():
        print(f"Error: No memocontent.json found at {content_path}")
        print("Run 'memo-dec summarizedocs' first to generate summaries.")
        sys.exit(1)

    print(f"Querying summaries from {content_path}...")
    print(f"Output format: {args.output_format}")
    if args.file_type_filter:
        print(f"File type filter: {args.file_type_filter}")
    print("=" * 60)

    try:
        # Load metadata
        with open(content_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if not metadata:
            print("No summaries found in memocontent.json")
            return

        # Apply filters and collect summaries
        summaries = []
        file_type_filter = args.file_type_filter
        path_filter = str(args.filepath) if args.filepath != Path('.') else None

        for rel_path in sorted(metadata.keys()):
            info = metadata[rel_path]

            # Filter by file type
            if file_type_filter:
                ext = Path(rel_path).suffix.lower()
                filter_ext = file_type_filter.lower()
                if not filter_ext.startswith('.'):
                    filter_ext = '.' + filter_ext
                if ext != filter_ext:
                    continue

            # Filter by path prefix
            if path_filter and path_filter != '.':
                if not rel_path.startswith(path_filter):
                    continue

            summary = info.get('summary', '')
            if not summary:
                continue

            summaries.append({
                'file': rel_path,
                'summary': summary,
                'last_updated': info.get('last_updated')
            })

        print(f"Found {len(summaries)} summaries\n")

        if not summaries:
            print("No summaries found matching criteria.")
            return

        # Output in requested format
        if args.output_format == 'json':
            print(json.dumps(summaries, indent=2))

        elif args.output_format == 'markdown':
            print("## File Summaries\n")
            print("| File | Summary | Last Updated |")
            print("|------|---------|--------------|")
            for s in summaries:
                last_upd = datetime.fromtimestamp(s['last_updated']).strftime('%Y-%m-%d %H:%M:%S') if s.get('last_updated') else 'N/A'
                summary_short = s['summary'][:80] + '...' if len(s['summary']) > 80 else s['summary']
                print(f"| {s['file']} | {summary_short} | {last_upd} |")

        else:  # txt format
            for s in summaries:
                print(f"\n{'='*60}")
                print(f"File: {s['file']}")
                print(f"Last Updated: {datetime.fromtimestamp(s['last_updated']).strftime('%Y-%m-%d %H:%M:%S') if s.get('last_updated') else 'N/A'}")
                print(f"{'='*60}")
                print(s['summary'])

    except json.JSONDecodeError as e:
        print(f"Error parsing memocontent.json: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading summaries: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_extractsymbols(args):
    """Handle extractsymbols command."""
    print(f"Extracting symbols from {args.filepath}...")
    print(f"Output format: {args.output_format}")
    print("=" * 60)

    if not args.filepath.exists():
        print(f"Error: Path does not exist: {args.filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract symbols
        print("\n[1/5] Starting symbol extraction...")
        if args.filepath.is_file():
            from .symbol_extractor import extract_symbols
            print(f"  Processing single file: {args.filepath}")
            print(f"  File extension: {args.filepath.suffix}")
            symbols = extract_symbols(args.filepath)
        else:
            print(f"  Processing directory: {args.filepath}")
            print(f"  Recursive scan: True")
            symbols = extract_symbols_from_directory(args.filepath, recursive=True)

        print(f"  ✓ Extracted {len(symbols)} total symbols")

        # Display first few symbols for debugging
        if symbols:
            print(f"\n[2/5] Sample symbols (first 5):")
            for i, sym in enumerate(symbols[:5], 1):
                print(f"  {i}. {sym['file']}:{sym['line']} ({sym['type']}) - {sym['name']}")
            if len(symbols) > 5:
                print(f"  ... and {len(symbols) - 5} more")

        # Display formatted symbols
        print(f"\n[3/5] Displaying all symbols:")
        print(format_symbols(symbols, args.output_format))

        # Save to file
        print(f"\n[4/5] Saving symbols to file...")
        storage = StorageManager()

        # Backup current symbols if exists
        symbols_path = storage.get_memosymbols_path()
        history = HistoryManager()
        if symbols_path.exists():
            print(f"  Backing up existing symbols...")
            history.backup_current_symbols(symbols_path)
            print(f"  ✓ Backup complete")

        # Save new symbols
        print(f"  Saving to: {symbols_path}")
        save_symbols_to_file(symbols, symbols_path)
        print(f"  ✓ Saved successfully")

        # Save to history
        print(f"\n[5/5] Saving to history...")
        hist_file = history.save_symbol_history(symbols)
        print(f"  ✓ History saved to: {hist_file}")

        print("\n" + "=" * 60)
        print("✓ Symbol extraction complete!")

    except Exception as e:
        print(f"\n✗ Error extracting symbols: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_summarizedocs(args):
    """Handle summarizedocs command."""
    print("Generating file summaries...")

    try:
        from .metadata import SummarizationEngine

        engine = SummarizationEngine()
        stats = engine.summarize_all(force_update=args.force)

        print(f"\n✓ Summarization complete")

    except Exception as e:
        print(f"Error generating summaries: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_findignore(args):
    """Handle findignore command."""
    print("Generating intelligent ignore patterns...")
    print("=" * 60)

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)

    if not args.path.is_dir():
        print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Load config
        try:
            config = Config()
        except ConfigError as e:
            print(f"✗ Configuration error: {e}", file=sys.stderr)
            print("  Please run 'memo-dec init' first to set up your configuration")
            sys.exit(1)

        # Initialize AI client and ignore manager
        from .ai_client import AIClient
        ai_client = AIClient(config)
        ignore_manager = IgnoreManager(ai_client, tree_generator)

        print(f"\n[1/2] Analyzing project structure in: {args.path}")
        try:
            # Generate ignore file with reliability
            ignore_file = ignore_manager.generate_ignore_file_with_reliability(str(args.path))
            print(f"✓ Analysis complete")
        except Exception as e:
            print(f"✗ Analysis failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

        print(f"\n[2/2] Updating .memoignore file...")
        if ignore_file and Path(ignore_file).exists():
            print(f"✓ .memoignore file updated successfully")
            print(f"  Location: {ignore_file}")
        else:
            print("✓ Using existing .memoignore file")

        print("\n" + "=" * 60)
        print("✓ Ignore pattern generation complete!")
        print("\nTo view or edit the ignore patterns:")
        print(f"  cat {args.path / '.memo' / '.memoignore'}")

    except Exception as e:
        print(f"\n✗ Error generating ignore patterns: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_addignore(args):
    """Handle addignore command - add patterns to .memoignore."""
    print("Adding patterns to .memoignore...")
    print("=" * 60)

    project_path = str(Path.cwd())

    try:
        result = add_ignore_pattern(project_path, args.patterns)

        if result:
            print(f"\n✓ Successfully added {len(args.patterns)} pattern(s) to .memoignore")
            print("\nPatterns added:")
            for pattern in args.patterns:
                print(f"  + {pattern}")

            print("\nView all patterns:")
            print(f"  cat {project_path}/.memo/.memoignore")

    except Exception as e:
        print(f"✗ Error adding patterns: {e}", file=sys.stderr)
        sys.exit(1)


def handle_update(args):
    """Handle update command - update symbols/content with change detection."""
    # Default to --all if no specific flag
    if not args.symbols and not args.content and not args.all:
        args.all = True

    print("Updating memo-dec data...")
    print("=" * 60)

    success = True

    # Update symbols
    if args.symbols or args.all:
        print("\n[1/2] Updating symbols...")
        try:
            # Backup current symbols
            storage = StorageManager()
            symbols_path = storage.get_memosymbols_path()
            history = HistoryManager()

            if symbols_path.exists():
                backup_path = history.backup_current_symbols(symbols_path)
                print(f"  ✓ Backed up symbols to: {backup_path}")

            # Re-extract symbols
            extractsymbols_args = argparse.Namespace(
                filepath=Path.cwd(),
                output_format='txt'
            )
            handle_extractsymbols(extractsymbols_args)
            print("  ✓ Symbols updated")

        except Exception as e:
            print(f"  ✗ Symbol update failed: {e}")
            success = False

    # Update content
    if args.content or args.all:
        print("\n[2/2] Updating content (incremental)...")
        try:
            from .metadata import SummarizationEngine

            engine = SummarizationEngine()
            stats = engine.summarize_all(force_update=False)

            print(f"  ✓ Content updated: {stats.get('processed', 0)} files processed")

        except Exception as e:
            print(f"  ✗ Content update failed: {e}")
            success = False

    print("\n" + "=" * 60)
    if success:
        print("✓ Update complete!")
    else:
        print("✗ Update completed with errors")


def parse_symbols_file(symbols_path):
    """
    Parse memosymbols.txt file into structured symbol list.

    Args:
        symbols_path: Path to memosymbols.txt

    Returns:
        List of symbol dictionaries with keys: file, line, type, name
    """
    symbols = []

    with open(symbols_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse the ultra-compact format
    # Format per file:
    # filename.py
    # line:type:name line:type:name ...

    lines = content.split('\n')
    current_file = None

    for line in lines:
        line = line.strip()

        # Skip headers and empty lines
        if not line or line.startswith('#') or line.startswith('-') or line.startswith('Memo-dec') or line.startswith('Total'):
            continue

        # Check if this is a file path (contains . and doesn't contain :)
        if '.' in line and ':' not in line and '/' in line or line.endswith('.py') or line.endswith('.js'):
            # This might be a file path - check if it looks like one
            if any(line.endswith(ext) for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.rb', '.php', '.cs', '.kt', '.swift', '.scala', '.sh']):
                current_file = line
                continue

        # If we have a current file, parse symbols from this line
        if current_file:
            # Symbols are space-separated: line:type:name
            parts = line.split()
            for part in parts:
                if ':' in part:
                    try:
                        components = part.split(':')
                        if len(components) >= 3:
                            line_num = int(components[0])
                            sym_type = components[1]
                            name = ':'.join(components[2:])  # Handle names with colons

                            symbols.append({
                                'file': current_file,
                                'line': line_num,
                                'type': sym_type,
                                'name': name
                            })
                    except (ValueError, IndexError):
                        continue

    return symbols


def generate_ai_usage_guide(storage):
    """
    Generate AI_USAGE_GUIDE.md file for AI agents.

    Args:
        storage: StorageManager instance

    Returns:
        Path to generated file or None if failed
    """
    try:
        guide_path = storage.get_memo_dir() / "AI_USAGE_GUIDE.md"

        content = """# AI Usage Guide for memo-dec

This guide helps AI agents understand how to use memo-dec context files.

## Directory Structure

```
.memo/
├── .memoignore          # Files/folders to ignore
├── memosymbols.txt      # Code symbols (functions, classes, variables)
├── memocontent.json     # File summaries with hashes
├── memotree/
│   ├── memofoldertree.txt   # Folder structure only
│   └── memofiletree.txt     # Full file tree with sizes
├── memodocs/            # Additional documentation
├── .memosymbols-hist/   # Symbol history (timestamped JSON)
└── .memocontent-hist/   # Content history (timestamped JSON)
```

## Key Files

### memosymbols.txt
Ultra-compact symbol format:
```
path/to/file.py
  10:fun:function_name  25:cls:ClassName  40:var:VARIABLE_NAME
```
Format: `line:type:name` where type is:
- `fun` = function
- `cls` = class
- `var` = variable
- `com` = component (React/Vue)

### memocontent.json
JSON format with file metadata:
```json
{
  "path/to/file.py": {
    "hash": "abc123...",
    "last_updated": 1234567890,
    "summary": "File description..."
  }
}
```

## CLI Commands for AI Agents

```bash
# Quick queries
memo-dec getsymbols json .py           # Python symbols as JSON
memo-dec getsummary markdown .js src/  # JS summaries from src/

# Updates
memo-dec update --symbols              # Re-extract symbols (with backup)
memo-dec update --content              # Incremental content update
memo-dec update --all                  # Update both

# Maintenance
memo-dec addignore "*.log" "temp/"     # Add ignore patterns
memo-dec findignore                    # AI-powered ignore generation
```

## Best Practices

1. **Before major refactoring**: Run `memo-dec update --all` to refresh context
2. **Adding new file types**: Update `.memo/.memoignore` to include/exclude
3. **Large projects**: Use `getsymbols` with filters to query specific files
4. **History tracking**: Check `.memosymbols-hist/` for previous states

## Integration Tips

- Symbols file is optimized for fast parsing (100+ symbols per line)
- Use `--json` output for programmatic access
- File hashes in memocontent.json enable change detection
- Tree files help understand project structure at a glance
"""

        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return guide_path

    except Exception as e:
        print(f"Warning: Could not generate AI_USAGE_GUIDE.md: {e}")
        return None


if __name__ == '__main__':
    main()
