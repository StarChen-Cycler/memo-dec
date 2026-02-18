"""
Metadata management for memo-dec.
Handles storage and retrieval of file summaries and metadata.
Based on: @memo-dec/summarize_docs_example.py lines 260-369
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime

from .history import HistoryManager


class MetadataManager:
    """
    Manages metadata storage for memo-dec.

    Stores file metadata including hashes and summaries in memocontent.json.
    Format:
        {
            "src/main.py": {
                "hash": "abc123...",
                "last_updated": 1234567890,
                "summary": "Detailed file summary..."
            }
        }
    """

    def __init__(self, metadata_file=None, project_path=None):
        """
        Initialize MetadataManager.

        Args:
            metadata_file (Path, optional): Path to metadata file
            project_path (Path, optional): Path to project root
        """
        if metadata_file:
            self.metadata_file = Path(metadata_file)
        else:
            if project_path is None:
                project_path = Path.cwd()
            self.metadata_file = project_path / '.memo' / 'memocontent.json'

    def load_metadata(self):
        """
        Load metadata from JSON file.

        Returns:
            dict: File metadata dictionary
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Error parsing metadata file {self.metadata_file}: {e}")
                print("Creating new metadata file...")
                return {}
            except Exception as e:
                print(f"Warning: Error reading metadata file {self.metadata_file}: {e}")
                return {}

        return {}

    def save_metadata(self, metadata):
        """
        Save metadata to JSON file.

        Args:
            metadata (dict): File metadata dictionary

        Returns:
            Path: Path to saved file
        """
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return self.metadata_file

    def update_file_metadata(self, metadata, rel_path, file_hash, summary):
        """
        Update metadata for a single file.

        Args:
            metadata (dict): Current metadata dictionary
            rel_path (str): Relative path to file
            file_hash (str): File hash
            summary (str): File summary

        Returns:
            dict: Updated metadata dictionary
        """
        metadata[rel_path] = {
            "hash": file_hash,
            "last_updated": time.time(),
            "summary": summary
        }
        return metadata

    def remove_deleted_files(self, metadata, current_files):
        """
        Remove metadata entries for files that no longer exist.

        Args:
            metadata (dict): Current metadata dictionary
            current_files (set): Set of currently existing files

        Returns:
            tuple: (updated_metadata, removed_count)
        """
        removed = []
        for rel_path in list(metadata.keys()):
            if rel_path not in current_files:
                del metadata[rel_path]
                removed.append(rel_path)

        return metadata, len(removed)

    def get_file_info(self, metadata, rel_path):
        """
        Get metadata for a specific file.

        Args:
            metadata (dict): Metadata dictionary
            rel_path (str): Relative path to file

        Returns:
            dict or None: File metadata or None if not found
        """
        return metadata.get(rel_path)

    def has_file_changed(self, metadata, rel_path, file_hash):
        """
        Check if a file has changed based on hash.

        Args:
            metadata (dict): Metadata dictionary
            rel_path (str): Relative path to file
            file_hash (str): Current file hash

        Returns:
            bool: True if file is new or has changed
        """
        if rel_path not in metadata:
            return True

        old_hash = metadata[rel_path].get('hash')
        return old_hash != file_hash

    def get_summary(self, metadata, rel_path):
        """
        Get summary for a specific file.

        Args:
            metadata (dict): Metadata dictionary
            rel_path (str): Relative path to file

        Returns:
            str or None: File summary or None
        """
        if rel_path in metadata:
            return metadata[rel_path].get('summary')
        return None

    def get_files_to_update(self, file_info, metadata):
        """
        Get list of files that need updating (new or changed).

        Args:
            file_info (dict): Current file information from scanner
            metadata (dict): Previous metadata

        Returns:
            list: List of file paths that need updating
        """
        to_update = []

        for rel_path, info in file_info.items():
            if self.has_file_changed(metadata, rel_path, info['hash']):
                to_update.append(rel_path)

        return to_update

    def get_stats(self, metadata):
        """
        Get statistics about metadata.

        Args:
            metadata (dict): Metadata dictionary

        Returns:
            dict: Statistics dictionary
        """
        if not metadata:
            return {"total_files": 0, "total_size": 0}

        stats = {
            "total_files": len(metadata),
            "by_extension": {}
        }

        for rel_path, info in metadata.items():
            ext = Path(rel_path).suffix.lower()
            if ext not in stats["by_extension"]:
                stats["by_extension"][ext] = 0
            stats["by_extension"][ext] += 1

        return stats


class SummarizationEngine:
    """Orchestrates the summarization process."""

    def __init__(self, project_path=None):
        """
        Initialize SummarizationEngine.

        Args:
            project_path (Path, optional): Path to project root
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()

        # Initialize components
        from .file_monitor import FileMonitor
        from .config import Config

        self.file_monitor = FileMonitor(self.project_path)
        self.metadata = MetadataManager(project_path=self.project_path)
        self.history = HistoryManager(memo_dir=self.project_path / '.memo')

        # Load config from global config
        self.config = Config()

        # Initialize AI client
        try:
            from .ai_client import AIClient
            self.ai_client = AIClient(self.config)
        except Exception as e:
            print(f"Warning: Could not initialize AI client: {e}")
            self.ai_client = None

    def summarize_all(self, force_update=False):
        """
        Summarize all supported files in the project with real-time metadata updates.
        Similar to summarize_docs_example.py scan_project method.

        Args:
            force_update (bool): Whether to update all files regardless of changes

        Returns:
            dict: Statistics about processed files
        """
        # Scan project and load metadata
        print("Scanning project...")
        file_info = self.file_monitor.scan_project()
        print(f"Found {len(file_info)} total files")

        # Load existing metadata (this is our memocontent.json)
        metadata = self.metadata.load_metadata()
        print(f"Existing metadata has {len(metadata)} files")

        # Get files to update
        if force_update:
            files_to_update = list(file_info.keys())
            update_reason = "Force update requested"
        else:
            files_to_update = self.metadata.get_files_to_update(file_info, metadata)
            update_reason = "New or modified files detected"

        if not files_to_update:
            print("\nNo files need updating.")
            return {"processed": 0, "skipped": len(file_info), "errors": 0}

        # Show statistics
        print(f"\n{'='*60}")
        print(f"SUMMARIZATION PREVIEW")
        print(f"{'='*60}")
        print(f"Files to process: {len(files_to_update)} ({update_reason})")
        print(f"Total project files: {len(file_info)}")
        print(f"Unchanged files: {len(file_info) - len(files_to_update)}")
        print(f"Existing summaries: {len(metadata)}")

        # Calculate total size and estimate tokens
        total_chars = 0
        for rel_path in files_to_update:
            file_path = Path(self.project_path) / rel_path
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    total_chars += len(content)
            except:
                pass

        # Estimate tokens (rough: 4 chars per token for English)
        estimated_tokens = total_chars // 4 if total_chars > 0 else 0
        print(f"\nEstimated processing: {total_chars:,} characters (~{estimated_tokens:,} tokens)")
        print(f"Model: {self.config.batch_model_name if self.config else 'Not configured'}")

        # Check batch processing setting
        if self.config and self.config.batch_processing_enabled:
            print(f"\nBatch processing is ENABLED in global config")
            print("Options:")
            print("  1) Use batch processing (asynchronous, cost-effective for many files)")
            print("  2) Use real-time processing (immediate results, slower for many files)")
            print("  3) Cancel")
            print(f"Enter your choice (1-3):", end=" ")
            response = input().strip()

            if response == '1':
                # BATCH PROCESSING MODE
                print("\n→ Batch processing selected")
                return self._process_with_batch(file_info, files_to_update, metadata)
            elif response == '2':
                use_batch = False
                print("\n→ Real-time processing selected")
            else:
                print("\n✓ Cancelled by user")
                return {"processed": 0, "skipped": len(file_info), "errors": 0, "cancelled": True}
        else:
            print(f"\nBatch processing is DISABLED in global config")
            print("Proceed with real-time processing?")
            print("  (y) Yes - Generate summaries immediately")
            print("  (n) No - Cancel operation")
            print(f"Enter your choice (y/n):", end=" ")
            response = input().strip().lower()

            if response in ('y', 'yes'):
                use_batch = False
                print("\n→ Real-time processing selected")
            else:
                print("\n✓ Cancelled by user")
                return {"processed": 0, "skipped": len(file_info), "errors": 0, "cancelled": True}

        # Backup current content before updating (history version)
        content_path = self.project_path / '.memo' / 'memocontent.json'
        if content_path.exists():
            backup_path = self.history.backup_current_content(content_path)
            print(f"Backed up current content to {backup_path}")

        # Track current files to detect deletions
        current_files = set()
        processed = 0
        errors = 0
        file_count = 0

        # Walk through project directory (respecting ignore patterns from file_monitor)
        for root, dirs, files in os.walk(self.project_path):
            # Filter directories using file_monitor's should_ignore
            dirs[:] = [d for d in dirs if not self.file_monitor.should_ignore(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file

                # Skip files that should be ignored
                if self.file_monitor.should_ignore(file_path):
                    continue

                # Skip the metadata file itself
                if file_path.resolve() == content_path.resolve():
                    continue

                rel_path = str(file_path.relative_to(self.project_path))
                current_files.add(rel_path)
                file_count += 1

                try:
                    # Calculate file hash
                    file_hash = self.file_monitor.calculate_file_hash(file_path)

                    # Check if file is new or modified
                    is_new_or_modified = (rel_path not in metadata or
                                        metadata[rel_path].get("hash") != file_hash or
                                        force_update)

                    if not is_new_or_modified:
                        continue

                    print(f"\n[{file_count}] Processing: {rel_path}")

                    # Create or update metadata entry with hash (first save point)
                    if rel_path not in metadata:
                        metadata[rel_path] = {
                            "hash": file_hash,
                            "last_updated": time.time(),
                            "summary": ""
                        }
                        print(f"  New file detected")
                    else:
                        metadata[rel_path]["hash"] = file_hash
                        metadata[rel_path]["last_updated"] = time.time()
                        print(f"  File modified")

                    # Save metadata after hash update (real-time save)
                    self.metadata.save_metadata(metadata)
                    print(f"  ✓ Metadata updated and saved")

                    # Check if we need to generate summary
                    if self.ai_client is None:
                        print(f"  Warning: AI client not available, skipping summary")
                        errors += 1
                        continue

                    # Read file content
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()

                        if not content:
                            print(f"  Skipping empty file")
                            continue

                        # Identify language
                        language = self.ai_client.identify_language(rel_path)
                        if language:
                            print(f"  Language: {language}")

                        # Generate summary
                        print(f"  Generating summary...")
                        summary_data = self.ai_client.summarize_file(
                            rel_path,
                            content,
                            language=language
                        )

                        summary = summary_data.get('summary', '')

                        if summary:
                            print(f"  ✓ Summary generated ({len(summary)} chars)")

                            # Update metadata with summary (second save point)
                            metadata[rel_path]["summary"] = summary

                            # Save metadata after summary generation (real-time save)
                            self.metadata.save_metadata(metadata)
                            print(f"  ✓ Metadata with summary saved")

                            processed += 1
                        else:
                            print(f"  ✗ Empty summary generated")
                            errors += 1

                    except Exception as e:
                        print(f"  ✗ Error reading or processing file: {e}")
                        errors += 1

                except Exception as e:
                    print(f"  ✗ Error calculating hash: {e}")
                    errors += 1

        # Remove entries for files that no longer exist
        deleted_files = set(metadata.keys()) - current_files
        if deleted_files:
            print(f"\nRemoving {len(deleted_files)} deleted files from metadata")
            for file_path in deleted_files:
                del metadata[file_path]
                print(f"  Removed: {file_path}")

            # Save after deleting files
            self.metadata.save_metadata(metadata)
            print(f"  ✓ Metadata saved after cleanup")

        # Save to history if files were processed
        if processed > 0:
            history_file = self.history.save_content_history(metadata)
            print(f"\nContent saved to history: {history_file}")

        # Final save (redundant but safe)
        print(f"\nSaving metadata...")
        self.metadata.save_metadata(metadata)
        print(f"✓ Metadata saved to {self.metadata.metadata_file}")

        # Return statistics
        result = {
            "processed": processed,
            "errors": errors,
            "deleted": len(deleted_files),
            "total_files": len(file_info),
            "unchanged": len(file_info) - processed - len(deleted_files)
        }

        print(f"\nSummary: {processed} processed, {errors} errors, {len(deleted_files)} deleted")

        return result

    def _process_with_batch(self, file_info, files_to_update, metadata):
        """
        Process files using batch API mode.

        Args:
            file_info (dict): File information from scanner
            files_to_update (list): Files to process
            metadata (dict): Current metadata

        Returns:
            dict: Statistics about processed files
        """
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING MODE")
        print(f"{'='*60}")

        # Prepare files for batch
        files_to_summarize = []
        total_chars = 0

        for i, rel_path in enumerate(files_to_update, 1):
            file_path = Path(self.project_path) / rel_path

            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                if content:
                    # Identify language
                    language = self.ai_client.identify_language(rel_path) if self.ai_client else None

                    files_to_summarize.append({
                        'path': rel_path,
                        'content': content,
                        'language': language
                    })

                    total_chars += len(content)
                    print(f"  [{i}/{len(files_to_update)}] Prepared: {rel_path}")

            except Exception as e:
                print(f"  [✗] Error reading {rel_path}: {e}")

        if not files_to_summarize:
            print("\n✗ No valid files to process")
            return {"processed": 0, "errors": 0, "deleted": 0, "total_files": len(file_info)}

        # Estimate tokens
        estimated_tokens = total_chars // 4
        print(f"\nPrepared {len(files_to_summarize)} files for batch processing")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {estimated_tokens:,}")
        print(f"Model: {self.config.batch_model_name}")

        # Setup batch file paths in .memo folder
        batch_dir = self.project_path / '.memo' / 'batch-process'
        batch_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_file = batch_dir / f'batch_requests_{timestamp}.jsonl'
        results_file = batch_dir / f'batch_results_{timestamp}.jsonl'

        print(f"\nBatch files will be saved to: {batch_dir}")
        print(f"  - Requests: {batch_file.name}")
        print(f"  - Results: {results_file.name}")

        # Ask for confirmation
        print(f"\nProceed with batch processing?")
        print(f"  (y) Yes - Submit batch job")
        print(f"  (n) No - Cancel")
        print(f"Enter your choice (y/n):", end=" ")
        response = input().strip().lower()

        if response not in ('y', 'yes'):
            print("\n✓ Cancelled by user")
            return {"processed": 0, "errors": 0, "deleted": 0, "cancelled": True}

        try:
            # Process files in batch
            summaries = self.ai_client.summarize_files_batch(
                files_to_summarize,
                batch_file,
                results_file,
                poll_interval=20
            )

            if not summaries:
                print("\n✗ No summaries generated from batch results")
                return {"processed": 0, "errors": len(files_to_summarize), "deleted": 0}

            print(f"\n{'='*60}")
            print(f"PROCESSING BATCH RESULTS")
            print(f"{'='*60}")

            # Update metadata with batch results
            processed = 0
            errors = 0
            current_files = set(file_info.keys())

            for rel_path, summary in summaries.items():
                if rel_path in files_to_update:
                    try:
                        file_hash = file_info[rel_path]['hash']

                        # Update metadata
                        metadata[rel_path] = {
                            "hash": file_hash,
                            "last_updated": time.time(),
                            "summary": summary
                        }

                        processed += 1
                        print(f"  [{processed}] Updated: {rel_path} ({len(summary)} chars)")

                    except Exception as e:
                        print(f"  [✗] Error updating {rel_path}: {e}")
                        errors += 1

            # Save metadata
            print(f"\nSaving metadata...")
            self.metadata.save_metadata(metadata)
            print(f"✓ Metadata saved to {self.metadata.metadata_file}")

            # Remove deleted files
            deleted_files = set(metadata.keys()) - current_files
            if deleted_files:
                print(f"\nRemoving {len(deleted_files)} deleted files from metadata")
                for file_path in deleted_files:
                    del metadata[file_path]
                self.metadata.save_metadata(metadata)

            # Save to history
            if processed > 0:
                history_file = self.history.save_content_history(metadata)
                print(f"\nContent saved to history: {history_file}")

            print(f"\n{'='*60}")
            print(f"BATCH PROCESSING COMPLETE")
            print(f"{'='*60}")
            print(f"Processed: {processed}")
            print(f"Errors: {errors}")
            print(f"Deleted: {len(deleted_files)}")

            return {
                "processed": processed,
                "errors": errors,
                "deleted": len(deleted_files),
                "total_files": len(file_info),
                "batch_files": {
                    "requests": str(batch_file),
                    "results": str(results_file)
                }
            }

        except Exception as e:
            print(f"\n✗ Batch processing failed: {e}")
            import traceback
            traceback.print_exc()
            return {"processed": 0, "errors": len(files_to_update), "deleted": 0}


if __name__ == '__main__':
    # Test summarization engine
    print("Testing SummarizationEngine...")
    engine = SummarizationEngine()
