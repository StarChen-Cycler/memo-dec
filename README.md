# Memo-Dec

**AI Codebase Context Assistant** - Helps AI agents understand codebases by extracting symbols, generating summaries, and managing project context.

## Features

- **Multi-Language Symbol Extraction**: Supports 23 programming languages including Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, Scala, Ruby, PHP, C#, Bash, YAML, TOML, SQL, and more
- **AI-Powered Summaries**: Generate intelligent file summaries using OpenAI GPT models
- **Smart Ignore Patterns**: Automatically detect and generate .memoignore patterns
- **Multiple Output Formats**: Export symbols as text, JSON, or Markdown
- **Git Integration**: Track changes and manage history
- **CLI Interface**: Simple command-line interface for all operations

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

---

### Method 1: Global Installation with pipx (Recommended)

**pipx** installs Python CLI tools globally with isolated environments - works independently of conda environments.

```bash
# 1. Install pipx (if not already installed)
pip install pipx
pipx ensurepath

# 2. Clone the repository
git clone https://github.com/StarChen-Cycler/memo-dec.git
cd memo-dec

# 3. Install globally with pipx
pipx install .
```

After installation, `memo-dec` is available **everywhere** on your system:

```bash
# Verify
memo-dec --help

# Works from any directory
cd /any/project
memo-dec init
```

---

### Method 2: Editable Install (For Development)

Use this if you want to modify the code and have changes take effect immediately.

```bash
# Clone and install in editable mode
git clone https://github.com/StarChen-Cycler/memo-dec.git
cd memo-dec
pip install -e .
```

**Note**: This installs to the **current Python environment only** (e.g., active conda env). To use in a different environment, reinstall or use pipx.

---

### Method 3: Install from GitHub URL

```bash
# Direct install from GitHub
pip install git+https://github.com/StarChen-Cycler/memo-dec.git
```

---

### Method 4: Conda Environment

If you use conda, you can install in a specific environment:

```bash
# Create a dedicated environment (optional)
conda create -n memo-tools python=3.10
conda activate memo-tools

# Install
pip install git+https://github.com/StarChen-Cycler/memo-dec.git
```

---

## Configuration

### OpenAI API Key (Optional)

For AI-powered features like `summarizedocs`, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file in your project root:

```
OPENAI_API_KEY=your-api-key-here
```

---

## Usage

### Initialize in Your Project

```bash
# Basic initialization
memo-dec init

# Initialize with full AI-powered context generation
memo-dec init --context
```

This creates a `.memo/` directory structure:
```
.memo/
├── .memoignore          # Files/folders to ignore
├── memosymbols.txt      # Code symbols (functions, classes, variables)
├── memocontent.json     # File summaries with hashes
├── AI_USAGE_GUIDE.md    # Guide for AI agents
├── memotree/
│   ├── memofoldertree.txt   # Folder structure only
│   └── memofiletree.txt     # Full file tree with sizes
├── memodocs/               # Additional documentation
├── .memosymbols-hist/     # Symbol history (timestamped JSON)
└── .memocontent-hist/     # Content history (timestamped JSON)
```

### Extract Symbols

```bash
# Extract from current directory (text output)
memo-dec extractsymbols

# Extract as JSON
memo-dec extractsymbols json

# Extract as Markdown
memo-dec extractsymbols markdown

# Extract from specific file
memo-dec extractsymbols txt path/to/file.py
```

### Query Stored Symbols

```bash
# Get all Python symbols in Markdown
memo-dec getsymbols markdown .py

# Get JavaScript symbols in JSON
memo-dec getsymbols json .js

# Get symbols from specific directory
memo-dec getsymbols txt .py src/

# Get all symbols
memo-dec getsymbols markdown
```

### Generate Summaries

```bash
# Generate summaries for all files
memo-dec summarizedocs

# Force update all summaries
memo-dec summarizedocs --force
```

### Query Stored Summaries

```bash
# Get all summaries in Markdown
memo-dec getsummary markdown

# Get Python file summaries in JSON
memo-dec getsummary json .py

# Get summaries from specific directory
memo-dec getsummary txt .js src/
```

### Manage Ignore Patterns

```bash
# Generate .memoignore for current directory
memo-dec findignore

# Generate for specific project
memo-dec findignore path/to/project

# Add patterns manually
memo-dec addignore "*.log" "temp/" "build/"

# View all patterns
cat .memo/.memoignore
```

### Update with Change Detection

```bash
# Update symbols (backup + re-extract)
memo-dec update --symbols

# Update content (incremental)
memo-dec update --content

# Update both
memo-dec update --all
```

---

## Supported Languages

| Language | Extensions | Symbols Extracted |
|----------|-----------|-------------------|
| Python | `.py` | functions, classes, variables |
| JavaScript | `.js` | functions, classes, variables |
| TypeScript | `.ts`, `.tsx` | functions, classes, interfaces, variables |
| Go | `.go` | functions, structs, interfaces, variables |
| Rust | `.rs` | functions, structs, enums, traits, variables |
| Kotlin | `.kt`, `.kts` | functions, classes, interfaces, objects, properties |
| Swift | `.swift` | functions, classes, structs, enums, protocols, variables |
| Scala | `.scala` | functions, classes, traits, objects, variables |
| Ruby | `.rb` | methods, classes, modules |
| PHP | `.php` | functions, classes, methods |
| C# | `.cs` | functions, classes, interfaces, methods |
| Bash | `.sh`, `.bash` | functions, variables |
| YAML | `.yml`, `.yaml` | keys |
| TOML | `.toml` | keys |
| SQL | `.sql` | tables, functions |
| Java | `.java` | methods, classes, fields |
| C/C++ | `.c`, `.cpp`, `.h` | functions, variables |
| Markdown | `.md` | headings |
| HTML | `.html`, `.htm` | tags, attributes |
| JSON | `.json` | keys |
| Vue | `.vue` | tags, attributes |
| Jupyter | `.ipynb` | functions, classes, variables |

---

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific language tests
python tests/test_python_symbols.py
python tests/test_rust_symbols.py
python tests/test_kotlin_symbols.py
# ... etc
```

### Project Structure

```
memo-dec/
├── memo_dec/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── config.py           # Configuration management
│   ├── symbol_extractor.py # Multi-language symbol extraction
│   ├── tree_generator.py   # File tree generation
│   ├── ai_client.py         # AI-powered summarization
│   ├── metadata.py          # File metadata management
│   ├── storage.py           # Storage management
│   ├── history.py           # History tracking
│   └── ignore_manager.py    # Ignore pattern management
├── tests/
│   ├── test_*.py          # Language-specific tests
│   └── test_results/      # Test output files
├── setup.py
└── README.md
```

---

## Troubleshooting

### "tree-sitter not available" error

Install tree-sitter language packages:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript
```

### "OpenAI API key not found" warning

Set your API key as described in the Configuration section. AI features will work without the key but will have limited functionality.

### Symbol extraction returns 0 results

- Verify the file extension is supported
- Check that tree-sitter language packages are installed
- Run tests to verify installation: `python tests/test_<language>_symbols.py`

---

## Examples

### Quick Start

```bash
# Navigate to your project
cd my-project

# Initialize memo-dec
memo-dec init

# Extract symbols
memo-dec extractsymbols markdown

# View results
cat .memo/memosymbols.txt
```

### Full AI-Powered Setup

```bash
# Navigate to your project
cd my-project

# Initialize with everything
memo-dec init --context

# This will:
# 1. Create .memo/ directory structure
# 2. Generate intelligent ignore patterns
# 3. Extract symbols from all source files
# 4. Generate AI summaries for each file
```

---

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
