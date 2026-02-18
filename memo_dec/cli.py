#!/usr/bin/env python3
"""
Memo-dec CLI entry point with argument parser.
"""
import argparse
import sys
from pathlib import Path

from .config import Config, ConfigError
from .storage import StorageManager
from .symbol_extractor import extract_symbols_from_directory, format_symbols, save_symbols_to_file
from .history import HistoryManager
from .ignore_manager import IgnoreManager
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

  # Extract and display symbols
  memo-dec extractsymbols                     # Current directory, text format
  memo-dec extractsymbols json                # JSON format
  memo-dec extractsymbols markdown            # Markdown format
  memo-dec extractsymbols txt path/to/file    # Single file

  # Generate and save file summaries
  memo-dec summarizedocs                      # Generate summaries for all files
  memo-dec summarizedocs --force              # Force update all files

  # Get symbols with filters [IN DEVELOPMENT]
  memo-dec getsymbols markdown .py            # Python files
  memo-dec getsymbols json .js path/to/dir    # JavaScript files in specific dir

  # Get summaries with filters [IN DEVELOPMENT]
  memo-dec getsummary markdown                # All files in markdown format
  memo-dec getsummary json .py                # Python files in JSON format
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
    getsymbols_parser = subparsers.add_parser('getsymbols', help='Extract and display symbols')
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
    getsymbols_parser.description = 'Get code symbols with optional filtering'

    # Getsummary command
    getsummary_parser = subparsers.add_parser('getsummary', help='Generate file summaries')
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
    getsummary_parser.description = 'Get file summaries with optional filtering'

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
    """Handle getsymbols command."""
    print("Getsymbols functionality not yet implemented")
    # TODO: Implement symbol retrieval
    print(f"Output format: {args.output_format}")
    print(f"File type filter: {args.file_type_filter}")
    print(f"Filepath: {args.filepath}")


def handle_getsummary(args):
    """Handle getsummary command."""
    print("Getsummary functionality not yet implemented")
    # TODO: Implement summary retrieval
    print(f"Output format: {args.output_format}")
    print(f"File type filter: {args.file_type_filter}")
    print(f"Filepath: {args.filepath}")


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


if __name__ == '__main__':
    main()
