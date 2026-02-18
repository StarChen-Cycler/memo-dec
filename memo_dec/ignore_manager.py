"""
Ignore Manager Module for Memo-Dec

Handles AI-powered generation and management of .memoignore files.
Based on Phase 5: Smart File Discovery (--findignore)
"""

import json
import os
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path


class IgnoreManagerError(Exception):
    """Custom exception for ignore manager errors."""
    pass


class IgnoreManager:
    """
    Manages .memoignore file generation using AI analysis.
    """

    def __init__(self, ai_client, tree_generator):
        """
        Initialize IgnoreManager.

        Args:
            ai_client: AIClient instance for API calls
            tree_generator: Module with tree generation functions
        """
        self.ai_client = ai_client
        self.tree_generator = tree_generator
        self.default_patterns = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '__pycache__/',
            '.git/',
            '.svn/',
            '.hg/',
            '.DS_Store',
            '*.log',
            '*.tmp',
            '*.temp',
            'node_modules/',
            'env/',
            'venv/',
            '.env/',
            'build/',
            'dist/',
            '*.egg-info/',
            '.pytest_cache/',
            '.tox/',
            '.coverage',
            'htmlcov/',
            '.idea/',
            '.vscode/',
            '*.swp',
            '*.swo',
            '*~',
            '.memo/',
        ]

    def generate_ignore_prompt(self, project_tree: str, is_large_project: bool = False) -> str:
        """
        Generate prompt for AI to identify ignorable files/folders.

        Args:
            project_tree: String representation of project structure
            is_large_project: Whether this is a large project (affects analysis approach)

        Returns:
            Formatted prompt string
        """
        if is_large_project:
            return f"""You are analyzing a LARGE project structure to identify files and folders that should be ignored for code analysis purposes.

Project structure (folders only for large projects):
```
{project_tree}
```

Please identify:
1. Folders that contain generated files, build artifacts, or dependencies that should be ignored
2. Common patterns that typically contain non-source-code files

Respond with a JSON object in this format:
{{
  "ignore_folders": ["folder1/", "folder2/", "pattern1*/"]
}}

Consider these common patterns to ignore:
- Build artifacts (build/, dist/, target/, out/)
- Dependencies (node_modules/, vendor/, packages/)
- Generated files
- IDE/editor configuration (.idea/, .vscode/)
- Version control (.git/, .svn/)
"""
        else:
            return f"""You are analyzing a project structure to identify files and folders that should be ignored for code analysis purposes.

Project structure:
```
{project_tree}
```

Please identify:
1. Files and folders that contain build artifacts, generated files, or dependencies
2. Files that are not source code (binaries, images, logs, temporary files)
3. Standard ignore patterns that are typically excluded from version control

Respond with a JSON object in this format:
{{
  "ignore_files": ["*.log", "*.tmp", "pattern*"],
  "ignore_folders": ["folder1/", "node_modules/", "build/"]
}}

Examples of what should be ignored:
- Build artifacts (*.pyc, *.o, *.class, build/, dist/, target/)
- Dependencies (node_modules/, vendor/, packages/)
- Generated files
- IDE/editor files (.idea/, .vscode/, *.swp)
- Version control metadata (.git/, .svn/, .hg/)
- Logs and temporary files (*.log, *.tmp, *.temp)
- OS files (.DS_Store, Thumbs.db)
"""

    def _load_existing_ignore_patterns(self, project_path: str) -> List[str]:
        """
        Load existing .memoignore patterns if available.

        Args:
            project_path: Path to project root

        Returns:
            List of ignore patterns
        """
        ignore_file = os.path.join(project_path, '.memo', '.memoignore')
        patterns = []

        if os.path.exists(ignore_file):
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                print(f"Warning: Could not read existing .memoignore: {e}")

        # Always include default patterns as fallback
        if not patterns:
            patterns = self.default_patterns

        return patterns

    def generate_ignore_file(
        self,
        project_path: str,
        use_batch: bool = False,
        existing_patterns: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Generate .memoignore file using AI analysis of project structure.

        Args:
            project_path: Path to project root
            use_batch: Whether to use batch processing (not used for this simple request)
            existing_patterns: Optional list of existing ignore patterns to use for filtering

        Returns:
            Dictionary with 'ignore_files' and 'ignore_folders' keys

        Raises:
            IgnoreManagerError: If generation fails
        """
        if not self.ai_client.client:
            raise IgnoreManagerError("AI client not initialized")

        project_path = os.path.abspath(project_path)

        # Check if project is large
        is_large = self.tree_generator.is_large_project(project_path)

        # Load patterns if not provided
        if existing_patterns is None:
            existing_patterns = self._load_existing_ignore_patterns(project_path)

        # Generate tree structure
        if is_large:
            # For large projects, start with folder-only analysis
            tree = self.tree_generator.generate_tree_structure(
                project_path,
                include_files=False,
                ignore_patterns=existing_patterns
            )
        else:
            # For smaller projects, include files
            tree = self.tree_generator.generate_tree_structure(
                project_path,
                include_files=True,
                ignore_patterns=existing_patterns
            )

        print(f"Project analysis: {'Large' if is_large else 'Small/Medium'} project detected")
        print(f"Analyzing project structure ({len(tree)} characters)...")

        # Generate prompt
        prompt = self.generate_ignore_prompt(tree, is_large)

        try:
            # Call AI API
            completion = self.ai_client.client.chat.completions.create(
                model=self.ai_client.config.batch_model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes project structures and identifies files/folders that should be ignored for code analysis. Respond with valid JSON in the specified format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )

            response_content = completion.choices[0].message.content

            if not response_content:
                raise IgnoreManagerError("Empty response from AI API")

            # Parse JSON response
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)

                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise IgnoreManagerError(f"Invalid JSON response from AI: {response_content[:200]}")

            return result

        except Exception as e:
            raise IgnoreManagerError(f"AI API call failed: {str(e)}")

    def consolidate_ignore_results(self, results: List[Dict[str, List[str]]]) -> Dict[str, Set[str]]:
        """
        Consolidate multiple AI analysis results by computing union of all suggestions.
        Changes from intersection (reliable patterns appearing in >=2 results) to union (all patterns from all runs).

        Args:
            results: List of result dictionaries from multiple AI calls

        Returns:
            Dictionary with 'ignore_files' and 'ignore_folders' as sets
        """
        if not results:
            return {"ignore_files": set(), "ignore_folders": set()}

        # Collect all suggestions across all runs (union)
        all_files = set()
        all_folders = set()

        for result in results:
            all_files.update(result.get("ignore_files", []))
            all_folders.update(result.get("ignore_folders", []))

        # Add default patterns
        for pattern in self.default_patterns:
            if pattern.endswith('/'):
                all_folders.add(pattern)
            else:
                all_files.add(pattern)

        return {
            "ignore_files": all_files,
            "ignore_folders": all_folders
        }

    def save_ignore_file(self, project_path: str, ignore_patterns: Dict[str, Set[str]]) -> str:
        """
        Save ignore patterns to .memo/.memoignore file.
        Appends new patterns to existing file, doesn't replace it.

        Args:
            project_path: Path to project root
            ignore_patterns: Dictionary with 'ignore_files' and 'ignore_folders' sets

        Returns:
            Path to the saved ignore file
        """
        memo_dir = os.path.join(project_path, '.memo')
        ignore_file = os.path.join(memo_dir, '.memoignore')

        # Ensure .memo directory exists
        os.makedirs(memo_dir, exist_ok=True)

        # Read existing patterns
        existing_folders = set()
        existing_files = set()

        if os.path.exists(ignore_file):
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            if line.endswith('/'):
                                existing_folders.add(line)
                            else:
                                existing_files.add(line)
            except Exception as e:
                print(f"Warning: Could not read existing .memoignore: {e}")

        # Get new patterns from AI
        new_folders = ignore_patterns.get("ignore_folders", set())
        new_files = ignore_patterns.get("ignore_files", set())

        # Find patterns to add (not already in existing)
        folders_to_add = new_folders - existing_folders
        files_to_add = new_files - existing_files

        # If nothing new to add, return early
        if not folders_to_add and not files_to_add:
            print(f"\n✓ No new ignore patterns to add")
            print(f"  Existing file: {ignore_file}")
            print(f"  - {len(existing_folders)} existing folder patterns")
            print(f"  - {len(existing_files)} existing file patterns")
            return ignore_file

        # Read existing file content
        original_content = ""
        if os.path.exists(ignore_file):
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    original_content = f.read().rstrip()  # Remove trailing whitespace
            except Exception as e:
                print(f"Warning: Could not read existing .memoignore: {e}")

        # Build new content
        content = original_content

        # Add separator if original content exists and doesn't end with newline
        if content and not content.endswith('\n'):
            content += '\n'

        # Add section header for AI-generated patterns
        if folders_to_add or files_to_add:
            content += "\n# AI-generated patterns (memo-dec --findignore)\n"
            content += "# The following patterns were automatically identified\n"
            content += "#\n"

        # Add new folders
        if folders_to_add:
            # Check if we need to add a "Folders" subsection
            if '# Folders' not in content or any(f not in content for f in sorted(folders_to_add)):
                content += "# Folders\n"
                for pattern in sorted(folders_to_add):
                    content += f"{pattern}\n"
                content += "\n"

        # Add new files
        if files_to_add:
            # Check if we need to add a "Files" subsection
            if '# Files' not in content or any(f not in content for f in sorted(files_to_add)):
                content += "# Files\n"
                for pattern in sorted(files_to_add):
                    content += f"{pattern}\n"

        # Write updated content
        with open(ignore_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Print summary
        print(f"\n✓ Ignore file updated: {ignore_file}")
        if folders_to_add:
            print(f"  - {len(folders_to_add)} new folder patterns added:")
            for pattern in sorted(folders_to_add):
                print(f"    + {pattern}")
        if files_to_add:
            print(f"  - {len(files_to_add)} new file patterns added:")
            for pattern in sorted(files_to_add):
                print(f"    + {pattern}")
        print(f"\nTotal patterns:")
        print(f"  - {len(existing_folders) + len(folders_to_add)} folder patterns")
        print(f"  - {len(existing_files) + len(files_to_add)} file patterns")

        return ignore_file

    def run_multiple_analyses(self, project_path: str, iterations: int = 3) -> Dict[str, Set[str]]:
        """
        Run multiple AI analyses and consolidate results for reliability.

        Args:
            project_path: Path to project root
            iterations: Number of times to run analysis (default: 3)

        Returns:
            Consolidated ignore patterns
        """
        print(f"\nRunning {iterations} AI analyses for reliability...")

        # Load existing ignore patterns to filter tree generation (only once)
        existing_patterns = self._load_existing_ignore_patterns(project_path)
        if existing_patterns and existing_patterns != self.default_patterns:
            print("\nUsing existing .memoignore patterns to filter project tree...")
            print(f"Found {len(existing_patterns)} existing patterns")

        results = []
        for i in range(iterations):
            print(f"\nAnalysis {i + 1}/{iterations}:")
            try:
                result = self.generate_ignore_file(project_path, existing_patterns)
                results.append(result)
                print(f"  ✓ Analysis {i + 1} completed")
            except Exception as e:
                print(f"  ✗ Analysis {i + 1} failed: {str(e)}")

        if not results:
            raise IgnoreManagerError("All AI analyses failed")

        # Consolidate results
        consolidated = self.consolidate_ignore_results(results)

        print(f"\nConsolidation complete:")
        print(f"  - {len(consolidated['ignore_files'])} file patterns identified")
        print(f"  - {len(consolidated['ignore_folders'])} folder patterns identified")

        return consolidated

    def generate_ignore_file_with_reliability(self, project_path: str) -> str:
        """
        Generate .memoignore file with multiple AI analyses for reliability.

        Args:
            project_path: Path to project root

        Returns:
            Path to saved ignore file

        Raises:
            IgnoreManagerError: If generation fails
        """
        # Run multiple analyses
        consolidated = self.run_multiple_analyses(project_path, iterations=3)

        # Save the consolidated results
        ignore_file_path = self.save_ignore_file(project_path, consolidated)

        return ignore_file_path


def add_ignore_pattern(project_path: str, patterns: List[str]) -> bool:
    """
    Add patterns to existing .memoignore file.

    Args:
        project_path: Path to project root
        patterns: List of patterns to add

    Returns:
        True if successful
    """
    memo_dir = os.path.join(project_path, '.memo')
    ignore_file = os.path.join(memo_dir, '.memoignore')

    # Ensure .memo directory exists
    os.makedirs(memo_dir, exist_ok=True)

    # Read existing patterns
    existing_patterns = set()
    if os.path.exists(ignore_file):
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_patterns.add(line)

    # Add new patterns
    new_patterns = set(patterns)
    all_patterns = existing_patterns | new_patterns

    # Sort patterns (folders first, then files)
    folders = sorted([p for p in all_patterns if p.endswith('/')])
    files = sorted([p for p in all_patterns if not p.endswith('/')])

    # Write patterns
    with open(ignore_file, 'w', encoding='utf-8') as f:
        f.write("# .memoignore - Files and folders to ignore for code analysis\n")
        f.write("# Auto-generated and manually maintained patterns\n\n")

        if folders:
            f.write("# Folders\n")
            for pattern in folders:
                f.write(f"{pattern}\n")
            f.write("\n")

        if files:
            f.write("# Files\n")
            for pattern in files:
                f.write(f"{pattern}\n")

    added_count = len(new_patterns - existing_patterns)
    print(f"✓ Added {added_count} new patterns to {ignore_file}")

    return True
