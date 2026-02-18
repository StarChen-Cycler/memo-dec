"""
AI Client for memo-dec.
Handles summarization of file content using OpenAI-compatible APIs.
Supports both real-time and batch processing modes.
Based on: @memo-dec/summarize_docs_example.py lines 66-144, 146-523
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class AIClientError(Exception):
    """Custom exception for AI client errors."""
    pass


class AIClient:
    """
    Client for OpenAI-compatible API to generate file summaries.

    Supports both real-time and batch processing modes.
    """

    def __init__(self, config):
        """
        Initialize AIClient with configuration.

        Args:
            config (Config): Configuration object with API settings
        """
        self.config = config
        self.client = None

        # Load the OpenAI client library if available
        try:
            from openai import OpenAI
            self.OpenAI = OpenAI
            self.setup_client()
        except ImportError:
            self.OpenAI = None
            print("Warning: openai package not installed. Install with: pip install openai")

    def setup_client(self):
        """Initialize the OpenAI client with the API key and base URL."""
        if not self.OpenAI:
            return

        self.client = self.OpenAI(
            api_key=self.config.api_auth_key,
            base_url=self.config.api_base_url
        )

    def summarize_file(self, file_path, file_content, language=None):
        """
        Generate summary of file content using AI.

        Args:
            file_path (str): Relative path of the file
            file_content (str): Content of the file
            language (str, optional): Programming language for better context

        Returns:
            dict: Response with "summary" key containing the file summary

        Raises:
            AIClientError: If API call fails
        """
        if not self.client:
            raise AIClientError("OpenAI client not initialized. Check openai package installation.")

        if not file_content:
            return {"summary": f"File is empty: {file_path}"}

        # Limit content length to avoid exceeding token limits
        max_length = 80000  # Rough character limit (not exact token count)
        if len(file_content) > max_length:
            file_content = file_content[:max_length]
            truncation_note = "(...truncated due to length)"
        else:
            truncation_note = ""

        # Prepare the prompt
        mode = "batch" if self.config.batch_processing_enabled else "realtime"
        lang_note = f" (Language: {language})" if language else ""

        prompt = f"""Please analyze the following file content and provide a detailed summary.

File path: {file_path}{lang_note}

Analyze this file and provide:
1. Purpose and overall functionality of the file
2. Precise description of each function, class, and method (if applicable)
3. Key variables, constants, or configuration
4. Major properties and characteristics of the file
5. How this file fits into the larger project

Make the response compact but information-dense. Focus on actionable details that would help an AI agent understand and work with this code.

File content:
```
{file_content}
{truncation_note}
```

Respond with a JSON object:
- OPTIONAL but valid json
- It should have a key \"summary\" with a detailed markdown summary

do NOT response with 2 newline at the beginning, do not response with \n sequence in the raw string"""

        try:
            # Call the API
            completion = self.client.chat.completions.create(
                model=self.config.batch_model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes code and provides detailed summaries. Respond with JSON containing a 'summary' key with markdown content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.3
            )

            # Extract response
            response_content = completion.choices[0].message.content

            if not response_content:
                return {"summary": f"Empty response from API for {file_path}"}

            # Try to parse JSON response
            try:
                summary_data = json.loads(response_content)
                if "summary" in summary_data:
                    return summary_data
                else:
                    # If JSON but no summary key, wrap it
                    return {"summary": response_content}

            except json.JSONDecodeError:
                # If not JSON, try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)

                if json_match:
                    try:
                        summary_data = json.loads(json_match.group())
                        if "summary" in summary_data:
                            return summary_data
                    except json.JSONDecodeError:
                        pass

                # If all parsing fails, return as summary
                return {"summary": response_content}

        except Exception as e:
            raise AIClientError(f"API request failed for {file_path}: {str(e)}")

    def identify_language(self, file_path):
        """
        Identify programming language from file extension.

        Args:
            file_path (str): Path to file

        Returns:
            str or None: Language name or None
        """
        ext = Path(file_path).suffix.lower()

        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (React)',
            '.c': 'C',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.h': 'C/C++ Header',
            '.java': 'Java',
            '.md': 'Markdown',
            '.html': 'HTML',
            '.json': 'JSON',
        }

        return language_map.get(ext)

    def check_api_connection(self):
        """
        Test API connection with a simple request.

        Returns:
            bool: True if connection successful

        Raises:
            AIClientError: If connection fails
        """
        if not self.client:
            raise AIClientError("OpenAI client not initialized")

        try:
            # Simple test request
            completion = self.client.chat.completions.create(
                model=self.config.batch_model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Respond with: {\"test\": \"success\"}"
                    }
                ],
                max_tokens=100
            )

            response = completion.choices[0].message.content
            return "success" in response.lower()

        except Exception as e:
            raise AIClientError(f"API connection test failed: {str(e)}")

    # =============== Batch Processing Methods ===============

    def create_batch_request(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """
        Create a batch request for file summarization.

        Args:
            file_path (str): Path to the file being summarized
            prompt (str): The prompt for summarization

        Returns:
            dict: Batch request data structure
        """
        return {
            "custom_id": file_path,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.config.batch_model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes code and provides detailed summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.3
            }
        }

    def submit_batch_job(self, batch_requests: List[Dict], batch_file_path: Path) -> Optional[str]:
        """
        Submit a batch job to the API.

        Args:
            batch_requests (list): List of batch request objects
            batch_file_path (Path): Path to save the batch JSONL file

        Returns:
            str or None: Batch ID if successful

        Raises:
            AIClientError: If batch submission fails
        """
        if not self.client:
            raise AIClientError("OpenAI client not initialized")

        if not batch_requests:
            raise AIClientError("No batch requests to submit")

        # Write batch requests to JSONL file
        print(f"Writing {len(batch_requests)} requests to {batch_file_path}...")
        batch_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(batch_file_path, 'w', encoding='utf-8') as f:
            for request in batch_requests:
                f.write(json.dumps(request, ensure_ascii=False) + '\n')

        print(f"Batch file size: {batch_file_path.stat().st_size} bytes")

        try:
            # Upload the batch file
            print("Uploading batch file...")
            file_object = self.client.files.create(
                file=batch_file_path,
                purpose="batch"
            )
            print(f"✓ Batch file uploaded. File ID: {file_object.id}")

            # Create the batch job
            print("Creating batch job...")
            batch = self.client.batches.create(
                input_file_id=file_object.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={
                    "description": f"Batch summarization of {len(batch_requests)} files"
                }
            )

            print(f"✓ Batch job created. Batch ID: {batch.id}")
            print(f"  Status: {batch.status}")

            return batch.id

        except Exception as e:
            raise AIClientError(f"Batch submission failed: {str(e)}")

    def poll_batch_status(self, batch_id: str, poll_interval: int = 10, timeout: int = 3600) -> Dict[str, Any]:
        """
        Poll batch job status until completion or timeout.

        Args:
            batch_id (str): Batch job ID
            poll_interval (int): Seconds between status checks
            timeout (int): Maximum seconds to wait

        Returns:
            dict: Final batch status

        Raises:
            AIClientError: If polling fails or timeout
        """
        if not self.client:
            raise AIClientError("OpenAI client not initialized")

        print(f"\n{'='*60}")
        print(f"Polling batch job: {batch_id}")
        print(f"Checking every {poll_interval} seconds (timeout: {timeout}s)")
        print(f"{'='*60}\n")

        start_time = time.time()
        last_status = None
        elapsed = 0

        while elapsed < timeout:
            try:
                # Get batch status
                batch = self.client.batches.retrieve(batch_id=batch_id)
                current_status = batch.status

                if current_status != last_status:
                    print(f"[{elapsed}s] Status: {current_status}")

                    # Show request counts if available
                    if hasattr(batch, 'request_counts'):
                        counts = batch.request_counts
                        total = getattr(counts, 'total', 0)
                        completed = getattr(counts, 'completed', 0)
                        failed = getattr(counts, 'failed', 0)
                        print(f"  Requests - Total: {total}, Completed: {completed}, Failed: {failed}")

                    last_status = current_status

                # Check if completed
                if current_status == "completed":
                    print(f"\n✓ Batch job completed!")
                    return {
                        "status": "completed",
                        "batch_id": batch_id,
                        "output_file_id": getattr(batch, 'output_file_id', None)
                    }

                elif current_status == "failed":
                    print(f"\n✗ Batch job failed!")
                    return {
                        "status": "failed",
                        "batch_id": batch_id,
                        "error": getattr(batch, 'errors', 'Unknown error')
                    }

                elif current_status == "cancelled":
                    print(f"\n✗ Batch job was cancelled!")
                    return {
                        "status": "cancelled",
                        "batch_id": batch_id
                    }

            except Exception as e:
                print(f"  Error checking status: {e}")

            # Wait before next check
            time.sleep(poll_interval)
            elapsed = int(time.time() - start_time)

            # Show progress every minute
            if elapsed % 60 == 0:
                print(f"[{elapsed}s] Still waiting...")

        print(f"\n✗ Timeout after {timeout} seconds!")
        raise AIClientError(f"Batch polling timeout after {timeout} seconds")

    def retrieve_batch_results(self, batch_status: Dict[str, Any], results_file: Path) -> bool:
        """
        Retrieve and save batch results.

        Args:
            batch_status (dict): Batch status from poll_batch_status
            results_file (Path): File to save results to

        Returns:
            bool: True if successful
        """
        if not self.client:
            raise AIClientError("OpenAI client not initialized")

        if batch_status.get('status') != 'completed':
            print("Batch job not completed, cannot retrieve results")
            return False

        output_file_id = batch_status.get('output_file_id')
        if not output_file_id:
            print("No output file ID in batch status")
            return False

        try:
            print(f"\nRetrieving batch results...")
            content = self.client.files.content(file_id=output_file_id)

            results_file.parent.mkdir(parents=True, exist_ok=True)
            content.write_to_file(results_file)

            print(f"✓ Results saved to {results_file}")
            print(f"  File size: {results_file.stat().st_size} bytes")

            return True

        except Exception as e:
            print(f"✗ Error retrieving results: {e}")
            return False

    def process_batch_results(self, results_file: Path) -> Dict[str, str]:
        """
        Process batch results and extract summaries.

        Args:
            results_file (Path): Path to batch results JSONL file

        Returns:
            dict: Dictionary mapping file paths to summaries
        """
        summaries = {}

        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            custom_id = result.get('custom_id')
                            response = result.get('response', {})
                            body = response.get('body', {})
                            choices = body.get('choices', [])

                            if custom_id and choices:
                                content = choices[0].get('message', {}).get('content', '')

                                # Try to parse as JSON to extract summary
                                try:
                                    summary_data = json.loads(content)
                                    summary = summary_data.get('summary', content)
                                except json.JSONDecodeError:
                                    summary = content

                                if summary:
                                    summaries[custom_id] = summary
                                    print(f"  [{i}] Extracted summary for {custom_id} ({len(summary)} chars)")

                        except json.JSONDecodeError:
                            print(f"  [{i}] Error parsing result line")

            print(f"\n✓ Processed {len(summaries)} summaries from batch results")
            return summaries

        except Exception as e:
            print(f"✗ Error processing batch results: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def summarize_files_batch(self, files_to_summarize: List[Dict], batch_file: Path, results_file: Path, poll_interval: int = 10) -> Dict[str, str]:
        """
        Complete batch summarization workflow.

        Args:
            files_to_summarize (list): List of dicts with file_path and content
            batch_file (Path): Path to save batch JSONL file
            results_file (Path): Path to save results JSONL file
            poll_interval (int): Seconds between status checks

        Returns:
            dict: Dictionary mapping file paths to summaries
        """
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARIZATION - {len(files_to_summarize)} files")
        print(f"{'='*60}")

        # Step 1: Create batch requests
        print(f"\nStep 1: Creating {len(files_to_summarize)} batch requests...")
        batch_requests = []

        for i, file_info in enumerate(files_to_summarize, 1):
            file_path = file_info['path']
            content = file_info['content']
            language = file_info.get('language')

            print(f"  [{i}] {file_path}")

            # Create prompt (reuse the same prompt logic from summarize_file)
            prompt = f"""Please analyze the following file content and provide a detailed summary.

File path: {file_path}
Language: {language or 'Unknown'}

Analyze this file and provide:
1. Purpose and overall functionality of the file
2. Precise description of each function, class, and method (if applicable)
3. Key variables, constants, or configuration
4. Major properties and characteristics of the file
5. How this file fits into the larger project

Make the response compact but information-dense.

File content:
```
{content[:50000]}  # Limit content length
```

Respond with a JSON object with a key "summary" containing detailed markdown summary."""

            # Create batch request
            request = self.create_batch_request(file_path, prompt)
            batch_requests.append(request)

        # Step 2: Submit batch job
        print(f"\nStep 2: Submitting batch job...")
        batch_id = self.submit_batch_job(batch_requests, batch_file)

        if not batch_id:
            print("✗ Failed to submit batch job")
            return {}

        # Step 3: Poll for completion
        print(f"\nStep 3: Waiting for batch completion...")
        batch_status = self.poll_batch_status(batch_id, poll_interval=poll_interval)

        if batch_status['status'] != 'completed':
            print(f"✗ Batch job failed: {batch_status.get('status')}")
            return {}

        # Step 4: Retrieve results
        print(f"\nStep 4: Retrieving batch results...")
        if not self.retrieve_batch_results(batch_status, results_file):
            print("✗ Failed to retrieve results")
            return {}

        # Step 5: Process results
        print(f"\nStep 5: Processing batch results...")
        summaries = self.process_batch_results(results_file)

        print(f"\n{'='*60}")
        print(f"BATCH SUMMARIZATION COMPLETE - {len(summaries)} files processed")
        print(f"{'='*60}")

        return summaries


if __name__ == '__main__':
    # Test AI client with mock response
    class MockConfig:
        def __init__(self):
            self.api_base_url = "https://mock.url"
            self.api_auth_key = "mock_key"
            self.batch_model_name = "mock-model"
            self.batch_processing_enabled = False

    try:
        config = MockConfig()
        client = AIClient(config)
        print("AIClient initialized successfully")
    except Exception as e:
        print(f"Error initializing AIClient: {e}")
