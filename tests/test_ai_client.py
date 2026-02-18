#!/usr/bin/env python3
"""
Test script to demonstrate both individual file summarization
and batch summarization capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from memo_dec.config import Config
from memo_dec.ai_client import AIClient
from memo_dec.metadata import MetadataManager


def test_individual_summarization():
    """Test summarizing individual files one by one."""
    print("=" * 70)
    print("TEST: Individual File Summarization")
    print("=" * 70)

    # Initialize client
    config = Config('.memo/.memoenv')
    client = AIClient(config)

    # Test files
    test_files = ['src/main.py', 'src/utils.js']

    for file_path in test_files:
        file = Path(file_path)
        print(f"\nProcessing {file_path}...")

        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        language = client.identify_language(str(file))
        print(f"  Language: {language}")
        print(f"  Content size: {len(content)} characters")

        result = client.summarize_file(str(file), content, language=language)

        if result and 'summary' in result:
            summary = result['summary']
            print(f"  ✓ Summary generated ({len(summary)} chars)")
            preview = summary[:200]
            print(f"  Preview: {preview}...")
        else:
            print(f"  ✗ Failed to generate summary")

    print("\n✓ Individual summarization test complete!\n")


def test_batch_summarization():
    """Test batch summarization of multiple files."""
    print("=" * 70)
    print("TEST: Batch File Summarization")
    print("=" * 70)

    config = Config('.memo/.memoenv')
    client = AIClient(config)

    # Prepare files
    files_to_summarize = []
    for file_path in ['src/main.py', 'src/utils.js']:
        file = Path(file_path)
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        language = client.identify_language(str(file))

        files_to_summarize.append({
            'path': str(file),
            'content': content,
            'language': language
        })

    print(f"\nProcessing {len(files_to_summarize)} files in batch...")
    print("Files:")
    for f in files_to_summarize:
        print(f"  - {f['path']} ({f['language']}, {len(f['content'])} chars)")

    # Run batch summarization
    batch_file = Path('.memo/test_batch.jsonl')
    results_file = Path('.memo/test_results.jsonl')

    summaries = client.summarize_files_batch(
        files_to_summarize,
        batch_file,
        results_file,
        poll_interval=10
    )

    print(f"\n✓ Batch complete! Generated {len(summaries)} summaries")

    # Display results
    for file_path, summary in summaries.items():
        print(f"\n{file_path}:")
        print(f"  Summary length: {len(summary)} characters")
        preview = summary[:300]
        print(f"  Preview: {preview}...")

    # Save to metadata
    print("\n" + "=" * 70)
    print("Saving to metadata...")

    metadata_mgr = MetadataManager(project_path=Path.cwd())
    metadata = metadata_mgr.load_metadata()

    import hashlib

    for file_info in files_to_summarize:
        file_path = file_info['path']
        if file_path in summaries:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            metadata = metadata_mgr.update_file_metadata(
                metadata,
                file_path,
                file_hash,
                summaries[file_path]
            )
            print(f"  ✓ Updated metadata for {file_path}")

    metadata_mgr.save_metadata(metadata)
    print(f"\n✓ Metadata saved to .memo/memocontent.json")


def compare_methods():
    """Compare individual vs batch summarization."""
    print("=" * 70)
    print("COMPARISON: Individual vs Batch Summarization")
    print("=" * 70)

    print("\nIndividual Summarization:")
    print("  Pros:")
    print("    - Immediate results")
    print("    - Easier to debug errors")
    print("    - Simpler implementation")
    print("  Cons:")
    print("    - Slower for many files")
    print("    - More API calls")
    print("    - Higher cost for large projects")

    print("\nBatch Summarization:")
    print("  Pros:")
    print("    - Much faster for many files")
    print("    - Single API call")
    print("    - Lower cost")
    print("    - Better for CI/CD pipelines")
    print("  Cons:")
    print("    - Requires waiting for completion")
    print("    - More complex implementation")
    print("    - Errors harder to debug")

    print("\n✓ Comparison complete!")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MEMO-DEC AI CLIENT TEST SUITE")
    print("=" * 70)

    try:
        # test_individual_summarization()
        test_batch_summarization()
        compare_methods()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
