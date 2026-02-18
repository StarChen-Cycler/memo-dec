import os
import json
import hashlib
import time
from pathlib import Path
import fnmatch
from openai import OpenAI

# Global variable for the user to set the absolute path of the project folder to monitor
PROJECT_PATH = ""  # User should set this to the absolute path of their project folder

# Global variable for the user to set the absolute path where the metadata JSON file should be stored
METADATA_STORAGE_PATH = None  # User can set this to specify where to store the metadata JSON file

# Batch processing configuration
BATCH_PROCESSING_ENABLED = False  # Set to True to enable batch processing
BATCH_MODEL_NAME = "qwen-long-latest"  # Model to use for batch processing
BATCH_COMPLETION_WINDOW = "24h"  # Completion window for batch jobs
BATCH_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB max file size
BATCH_MAX_REQUESTS = 50000  # Maximum requests per batch
BATCH_POLL_INTERVAL = 20  # Seconds between status checks (20 seconds)
BATCH_TIMEOUT = 24 * 60 * 60  # Timeout in seconds (24 hours)

class ClaudeAgent:
    """
    Agent class that uses the OpenAI-compatible API to generate summaries of file content
    Supports both real-time and batch processing modes
    """
    def __init__(self, env_file_path=None):
        self.api_base_url = None
        self.api_auth_key = None
        self.load_env(env_file_path)
        self.client = None
        self.setup_client()
    
    def load_env(self, env_file_path=None):
        """Load API URL and key from .claudeenv file"""
        if env_file_path is None:
            env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.claudeenv')
        
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key == 'API_BASE_URL':
                            self.api_base_url = value
                        elif key == 'API_AUTH_KEY':
                            self.api_auth_key = value
        else:
            raise FileNotFoundError(f"Environment file not found: {env_file_path}")
        
        if not self.api_base_url or not self.api_auth_key:
            raise ValueError("API_BASE_URL and API_AUTH_KEY must be set in the .claudeenv file")
    
    def setup_client(self):
        """Initialize the OpenAI client with the API key and base URL"""
        self.client = OpenAI(
            api_key=self.api_auth_key,
            base_url=self.api_base_url
        )
    
    def summarize_file(self, file_path, file_content):
        """
        Call API to summarize the content of a file
        Returns a summary in the format: {summary: # summary of the file content}
        """
        # Model used for summarization
        model_name = "qwen-long-latest"
        
        # Prepare the prompt for the model
        prompt = f"""
Please analyze the following file content and provide a detailed summary.
Include the following information:
1. Precise description of each function, class, and method in the file (if any)
2. Major properties and characteristics of the file
3. Make the reply compact with useful information

Format your response as a JSON object with a single key 'summary'.

File path: {file_path}

File content:
```
{file_content}
```

Respond only with a JSON object in this format:
{{
  "summary": "# Detailed summary including functions/classes/methods descriptions and major file properties"
}}
"""
        
        # Check if batch processing is enabled
        if BATCH_PROCESSING_ENABLED:
            # For batch processing, we return the request data instead of calling the API directly
            return self._create_batch_request(file_path, prompt, model_name)
        
        # Real-time processing (existing functionality)
        try:
            print(f"Using model: {model_name}")
            print(f"API base URL: {self.api_base_url}")
            
            # Call the API using the OpenAI client
            completion = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes code and provides detailed summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000
            )
            
            # Print additional API info
            print(f"API response model: {completion.model}")
            print(f"API response usage: {completion.usage}")
            
            # Extract the response content
            response_content = completion.choices[0].message.content
            
            # Try to parse the response as JSON
            try:
                # Try to parse the entire response as JSON
                summary_data = json.loads(response_content)
                return summary_data
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'({.*})', response_content, re.DOTALL)
                if json_match:
                    try:
                        summary_data = json.loads(json_match.group(1))
                        return summary_data
                    except json.JSONDecodeError:
                        pass
                
                # If all parsing attempts fail, return a formatted error
                return {"summary": f"Error parsing API response: {response_content}"}
        
        except Exception as e:
            return {"summary": f"API request error: {str(e)}"}
    
    def _create_batch_request(self, file_path, prompt, model_name):
        """
        Create a batch request for the file summarization
        Returns the request data that can be written to a JSONL file
        """
        request_data = {
            "custom_id": file_path,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that analyzes code and provides detailed summaries."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000
            }
        }
        return request_data


class ProjectMonitor:
    """
    Monitors a project folder, generates file metadata, and stores summaries
    Supports both real-time and batch processing modes
    """
    def __init__(self, project_path, agent=None):
        self.project_path = Path(project_path)
        # Use METADATA_STORAGE_PATH if set, otherwise default to project path
        if METADATA_STORAGE_PATH:
            metadata_path = Path(METADATA_STORAGE_PATH)
            # Create directory if it doesn't exist
            metadata_path.mkdir(parents=True, exist_ok=True)
            self.metadata_file = metadata_path / "claude_context_metadata.json"
        else:
            self.metadata_file = self.project_path / "claude_context_metadata.json"
        self.agent = agent if agent else ClaudeAgent()
        self.ignore_patterns = self.load_ignore_patterns()
        # Batch processing variables
        self.batch_requests = []
        self.batch_file_path = self.project_path / "claude_batch_requests.jsonl"
        
    def load_ignore_patterns(self):
        """Load ignore patterns from .contextignore file"""
        ignore_patterns = [
            # Default patterns to ignore
            ".git", ".nuxt", ".output", "node_modules", "__pycache__",
            "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.class",
            "*.exe", "*.bin", "*.pkl", "*.h5", "*.model", "*.jpg", "*.jpeg", 
            "*.png", "*.gif", "*.svg", "*.ico", "*.pdf", "*.zip", "*.tar.gz",
            "*.mp3", "*.mp4", "*.avi", "*.mov", "*.wav", "*.flac", "*.lock"
        ]
        
        # Regex patterns for temporary files and build hashes
        self.ignore_regex_patterns = [
            r'^\.[0-9]+$',  # Files like .0, .2, .20, .12, .56
            r'^\.[A-Za-z0-9]{5,}$'  # Hash-like temp files like .7usdW, .aaYVD, .MVHJS (5 or more chars)
        ]
        
        # Load ignore patterns from the context-for-claude-code folder
        ignore_file = Path(os.path.dirname(os.path.abspath(__file__))) / ".contextignore"
        if ignore_file.exists():
            with open(ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        
        # Load ignore patterns from the project folder being monitored
        project_ignore_file = self.project_path / ".contextignore"
        if project_ignore_file.exists():
            with open(project_ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        
        return ignore_patterns
    
    def should_ignore(self, path):
        """Check if a file or directory should be ignored"""
        import re
        
        rel_path = os.path.relpath(path, self.project_path)
        filename = os.path.basename(path)
        
        # Check if any part of the path matches an ignore pattern
        path_parts = rel_path.split(os.sep)
        for part in path_parts:
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True
        
        # Check if the full path matches any pattern
        for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
        
        # Check regex patterns for temporary files
        if hasattr(self, 'ignore_regex_patterns'):
            for regex_pattern in self.ignore_regex_patterns:
                if re.match(regex_pattern, filename):
                    return True
        
        return False
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def load_metadata(self):
        """Load existing metadata from JSON file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Error parsing metadata file. Creating a new one.")
                    return {}
        return {}
    
    def save_metadata(self, metadata):
        """Save metadata to JSON file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def scan_project(self):
        """
        Scan the project directory and update the metadata
        Supports both real-time and batch processing modes
        """
        metadata = self.load_metadata()
        current_files = set()
        
        # Reset batch requests if in batch mode
        if BATCH_PROCESSING_ENABLED:
            self.batch_requests = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Filter out directories that should be ignored
            dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip files that should be ignored
                if self.should_ignore(file_path):
                    continue
                
                # Skip the metadata file itself
                if os.path.abspath(file_path) == os.path.abspath(self.metadata_file):
                    continue
                
                rel_path = os.path.relpath(file_path, self.project_path)
                current_files.add(rel_path)
                
                try:
                    # Calculate file hash
                    file_hash = self.calculate_file_hash(file_path)
                    
                    # Check if file is new or modified
                    if rel_path not in metadata or metadata[rel_path].get("hash") != file_hash:
                        print(f"Processing file: {rel_path}")
                        
                        # Create or update metadata entry
                        if rel_path not in metadata:
                            metadata[rel_path] = {
                                "hash": file_hash,
                                "last_updated": time.time(),
                                "summary": ""
                            }
                        else:
                            metadata[rel_path]["hash"] = file_hash
                            metadata[rel_path]["last_updated"] = time.time()
                        
                        # Save metadata after hash generation
                        self.save_metadata(metadata)
                        
                        # Generate summary for the file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                file_content = f.read()
                            
                            summary_data = self.agent.summarize_file(rel_path, file_content)
                            
                            # Handle batch vs real-time processing
                            if BATCH_PROCESSING_ENABLED:
                                # Store batch request data
                                self.batch_requests.append(summary_data)
                                print(f"Batch request created for {rel_path}")
                            else:
                                # Real-time processing
                                metadata[rel_path]["summary"] = summary_data.get("summary", "")
                                print(f"Summary generated for {rel_path}")
                                
                                # Save metadata after summary generation
                                self.save_metadata(metadata)
                        except Exception as e:
                            print(f"Error processing file {rel_path}: {str(e)}")
                            # Save metadata even if summary generation fails
                            self.save_metadata(metadata)
                except Exception as e:
                    print(f"Error processing file {rel_path}: {str(e)}")
        
        # Handle batch processing if enabled
        if BATCH_PROCESSING_ENABLED and self.batch_requests:
            self._process_batch_requests()
            # For batch processing, we don't want to continue with the rest of the method
            # as the results will be processed when the batch completes
            return
        
        # Remove entries for files that no longer exist
        deleted_files = set(metadata.keys()) - current_files
        for file in deleted_files:
            del metadata[file]
            print(f"Removed metadata for deleted file: {file}")
        
        # Save updated metadata
        self.save_metadata(metadata)
        print(f"Metadata saved to {self.metadata_file}")
    
    def _process_batch_requests(self):
        """
        Process all batch requests by writing them to a JSONL file and submitting to the batch API
        Supports splitting large batches into smaller chunks
        """
        if not self.batch_requests:
            print("No batch requests to process")
            return
        
        # Get file type information and user preferences before proceeding
        file_type_info = self._get_file_type_info()
        if not file_type_info:
            print("No files to process after filtering")
            return
        
        # Show file types to user and get their selection
        excluded_types = self._get_user_file_type_selection(file_type_info)
        
        # Filter batch requests based on user selection
        filtered_requests = self._filter_batch_requests_by_type(excluded_types)
        if not filtered_requests:
            print("No files to process after user selection")
            return
        
        # Show cost estimation and get final confirmation
        if not self._get_user_cost_confirmation(filtered_requests):
            print("Batch request cancelled by user")
            return
        
        # Update batch requests with filtered requests
        self.batch_requests = filtered_requests
        
        # Check if we need to split into multiple batches
        if len(self.batch_requests) > BATCH_MAX_REQUESTS:
            print(f"Splitting {len(self.batch_requests)} requests into multiple batches...")
            self._process_batch_requests_in_chunks()
            return
        
        # Check file size before submission
        batch_file_size = self._write_batch_requests_to_file(self.batch_requests, self.batch_file_path)
        if batch_file_size > BATCH_MAX_FILE_SIZE:
            print(f"Batch file size ({batch_file_size} bytes) exceeds limit ({BATCH_MAX_FILE_SIZE} bytes)")
            print("Splitting batch into smaller chunks...")
            self._process_batch_requests_in_chunks()
            return
        
        # Submit batch job if we have a client
        if self.agent.client:
            try:
                self._submit_batch_job()
            except Exception as e:
                print(f"Error submitting batch job: {str(e)}")
    
    def _write_batch_requests_to_file(self, requests, file_path):
        """
        Write batch requests to a JSONL file and return the file size
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for request in requests:
                    f.write(json.dumps(request, ensure_ascii=False) + '\n')
            print(f"Batch requests written to {file_path}")
            return file_path.stat().st_size
        except Exception as e:
            print(f"Error writing batch requests to file: {str(e)}")
            return 0
    
    def _process_batch_requests_in_chunks(self):
        """
        Process batch requests by splitting them into smaller chunks
        """
        # Get file type information and user preferences before proceeding
        file_type_info = self._get_file_type_info()
        if not file_type_info:
            print("No files to process after filtering")
            return
        
        # Show file types to user and get their selection
        excluded_types = self._get_user_file_type_selection(file_type_info)
        
        # Filter batch requests based on user selection
        filtered_requests = self._filter_batch_requests_by_type(excluded_types)
        if not filtered_requests:
            print("No files to process after user selection")
            return
        
        # Show cost estimation and get final confirmation
        if not self._get_user_cost_confirmation(filtered_requests):
            print("Batch request cancelled by user")
            return
        
        # Update batch requests with filtered requests
        self.batch_requests = filtered_requests
        
        # Split requests into chunks
        chunks = [self.batch_requests[i:i + BATCH_MAX_REQUESTS] 
                 for i in range(0, len(self.batch_requests), BATCH_MAX_REQUESTS)]
        
        print(f"Splitting {len(self.batch_requests)} requests into {len(chunks)} batches")
        
        batch_info_list = []
        for i, chunk in enumerate(chunks):
            chunk_file_path = self.project_path / f"claude_batch_requests_chunk_{i}.jsonl"
            chunk_file_size = self._write_batch_requests_to_file(chunk, chunk_file_path)
            
            if chunk_file_size > 0:
                try:
                    # Upload the batch file
                    print(f"Uploading batch chunk {i+1}/{len(chunks)}...")
                    file_object = self.agent.client.files.create(
                        file=Path(chunk_file_path),
                        purpose="batch"
                    )
                    print(f"Batch chunk {i+1} uploaded. File ID: {file_object.id}")
                    
                    # Create the batch job
                    print(f"Creating batch job for chunk {i+1}...")
                    batch = self.agent.client.batches.create(
                        input_file_id=file_object.id,
                        endpoint="/v1/chat/completions",
                        completion_window=BATCH_COMPLETION_WINDOW,
                        metadata={
                            "ds_name": f"Claude Context Helper Batch Job Chunk {i+1}/{len(chunks)}",
                            "ds_description": f"Batch processing of file summaries for Claude Context Helper - Chunk {i+1}"
                        }
                    )
                    print(f"Batch job for chunk {i+1} created. Batch ID: {batch.id}")
                    
                    # Save batch job info
                    batch_info = {
                        "batch_id": batch.id,
                        "input_file_id": file_object.id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "created_at": batch.created_at,
                        "completion_window": batch.completion_window
                    }
                    batch_info_list.append(batch_info)
                    
                except Exception as e:
                    print(f"Error processing batch chunk {i+1}: {str(e)}")
        
        # Save all batch job info
        if batch_info_list:
            batch_info_file = self.project_path / "claude_batch_info.json"
            with open(batch_info_file, 'w', encoding='utf-8') as f:
                json.dump(batch_info_list, f, indent=2, ensure_ascii=False)
            print(f"Batch job info saved to {batch_info_file}")
            
            # Automatically start polling the batch jobs
            print("\nStarting automatic polling of batch job status...")
            print("Checking every 20 seconds until completion.\n")
            self.poll_batch_status()
    
    def _submit_batch_job(self):
        """
        Submit the batch job to the API and automatically start polling
        """
        try:
            # Upload the batch file
            print("Uploading batch file...")
            file_object = self.agent.client.files.create(
                file=Path(self.batch_file_path),
                purpose="batch"
            )
            print(f"Batch file uploaded. File ID: {file_object.id}")
            
            # Create the batch job
            print("Creating batch job...")
            batch = self.agent.client.batches.create(
                input_file_id=file_object.id,
                endpoint="/v1/chat/completions",
                completion_window=BATCH_COMPLETION_WINDOW,
                metadata={
                    "ds_name": "Claude Context Helper Batch Job",
                    "ds_description": "Batch processing of file summaries for Claude Context Helper"
                }
            )
            print(f"Batch job created. Batch ID: {batch.id}")
            print(f"Batch job status: {batch.status}")
            
            # Save batch job info
            batch_info = {
                "batch_id": batch.id,
                "input_file_id": file_object.id,
                "created_at": batch.created_at,
                "completion_window": batch.completion_window
            }
            
            batch_info_file = self.project_path / "claude_batch_info.json"
            with open(batch_info_file, 'w', encoding='utf-8') as f:
                json.dump(batch_info, f, indent=2, ensure_ascii=False)
            print(f"Batch job info saved to {batch_info_file}")
            
            # Automatically start polling the batch job
            print("\nStarting automatic polling of batch job status...")
            print("Checking every 20 seconds until completion.\n")
            self.poll_batch_status(batch.id)
            
        except Exception as e:
            print(f"Error submitting batch job: {str(e)}")
    
    def check_batch_status(self, batch_id=None):
        """
        Check the status of a batch job and retrieve results if completed
        Supports both single batch ID and multiple batches from batch info file
        """
        # If no batch_id provided, try to load from batch info file
        if not batch_id:
            batch_info_file = self.project_path / "claude_batch_info.json"
            if not batch_info_file.exists():
                print("No batch job info found. Run scan_project with BATCH_PROCESSING_ENABLED=True first.")
                return
            
            try:
                with open(batch_info_file, 'r', encoding='utf-8') as f:
                    batch_info = json.load(f)
                
                # Check if we have multiple batches (list) or single batch (dict)
                if isinstance(batch_info, list):
                    # Handle multiple batches
                    self._check_multiple_batch_status(batch_info)
                    return
                else:
                    # Handle single batch
                    batch_id = batch_info.get("batch_id")
            except Exception as e:
                print(f"Error reading batch info file: {str(e)}")
                return
        
        if not batch_id:
            print("No batch ID provided or found in batch info file.")
            return
        
        # Check single batch job status
        try:
            print(f"Checking status of batch job: {batch_id}")
            batch = self.agent.client.batches.retrieve(batch_id=batch_id)
            print(f"Batch job status: {batch.status}")
            
            # If completed, retrieve results
            if batch.status == "completed":
                self._retrieve_batch_results(batch)
            elif batch.status == "failed":
                print(f"Batch job failed. Error: {batch.errors}")
                # Try to retrieve error file if available
                if batch.error_file_id:
                    self._retrieve_batch_error_results(batch)
            else:
                print(f"Batch job is still {batch.status}. Please check again later.")
                
        except Exception as e:
            print(f"Error checking batch status: {str(e)}")
    
    def _check_multiple_batch_status(self, batch_info_list):
        """
        Check the status of multiple batch jobs and retrieve results when all are completed
        """
        print(f"Checking status of {len(batch_info_list)} batch jobs...")
        
        completed_batches = []
        failed_batches = []
        pending_batches = []
        
        for batch_info in batch_info_list:
            batch_id = batch_info.get("batch_id")
            try:
                print(f"Checking status of batch job: {batch_id}")
                batch = self.agent.client.batches.retrieve(batch_id=batch_id)
                print(f"Batch job {batch_id} status: {batch.status}")
                
                if batch.status == "completed":
                    completed_batches.append(batch)
                elif batch.status == "failed":
                    failed_batches.append(batch)
                else:
                    pending_batches.append(batch)
            except Exception as e:
                print(f"Error checking batch status for {batch_id}: {str(e)}")
                failed_batches.append({"id": batch_id, "error": str(e)})
        
        print(f"Completed: {len(completed_batches)}, Failed: {len(failed_batches)}, Pending: {len(pending_batches)}")
        
        # Process completed batches
        for batch in completed_batches:
            try:
                self._retrieve_batch_results(batch)
            except Exception as e:
                print(f"Error retrieving results for batch {batch.id}: {str(e)}")
        
        # Process failed batches
        for batch in failed_batches:
            if hasattr(batch, 'error_file_id') and batch.error_file_id:
                try:
                    self._retrieve_batch_error_results(batch)
                except Exception as e:
                    print(f"Error retrieving error results for batch {batch.id}: {str(e)}")
    
    def poll_batch_status(self, batch_id=None, timeout=None):
        """
        Poll the status of a batch job until completion, failure, or timeout
        Checks every 20 seconds and ends when complete
        """
        import time
        
        # Set polling interval to 20 seconds
        poll_interval = 20
        
        if timeout is None:
            timeout = BATCH_TIMEOUT
            
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            # Check batch job status
            try:
                if not batch_id:
                    batch_info_file = self.project_path / "claude_batch_info.json"
                    if not batch_info_file.exists():
                        print("No batch job info found.")
                        return
                    
                    try:
                        with open(batch_info_file, 'r', encoding='utf-8') as f:
                            batch_info = json.load(f)
                    except json.JSONDecodeError:
                        print("Error reading batch job info file. File may be corrupted.")
                        return
                    except Exception as e:
                        print(f"Error reading batch job info file: {str(e)}")
                        return
                    
                    # Handle both single and multiple batches
                    if isinstance(batch_info, list):
                        # For multiple batches, check all
                        all_completed = True
                        any_failed = False
                        any_in_progress = False
                        
                        for info in batch_info:
                            batch_id = info.get("batch_id")
                            batch = self.agent.client.batches.retrieve(batch_id=batch_id)
                            if batch.status not in ["completed", "failed"]:
                                all_completed = False
                                any_in_progress = True
                            if batch.status == "failed":
                                any_failed = True
                            print(f"Batch {batch_id}: {batch.status}")
                        
                        if all_completed:
                            print("All batches completed!")
                            self._check_multiple_batch_status(batch_info)
                            return
                        elif any_failed:
                            print("One or more batches failed!")
                            self._check_multiple_batch_status(batch_info)
                            return
                        elif not any_in_progress:
                            print("No batches in progress.")
                            return
                    else:
                        batch_id = batch_info.get("batch_id")
                
                if batch_id:
                    try:
                        batch = self.agent.client.batches.retrieve(batch_id=batch_id)
                        current_status = batch.status
                    except Exception as e:
                        print(f"Error retrieving batch status: {str(e)}")
                        print(f"Waiting 20 seconds before retry...")
                        time.sleep(poll_interval)
                        continue
                    
                    if current_status != last_status:
                        print(f"Batch job status: {current_status}")
                        if hasattr(batch, 'request_counts'):
                            counts = batch.request_counts
                            # Access attributes directly instead of using get method
                            total = getattr(counts, 'total', 0)
                            completed = getattr(counts, 'completed', 0)
                            failed = getattr(counts, 'failed', 0)
                            print(f"Requests - Total: {total}, "
                                  f"Completed: {completed}, "
                                  f"Failed: {failed}")
                        last_status = current_status
                    
                    # End polling when batch is completed or failed
                    if current_status == "completed":
                        print("Batch job completed!")
                        self._retrieve_batch_results(batch)
                        return
                    elif current_status == "failed":
                        print(f"Batch job failed. Error: {batch.errors}")
                        if batch.error_file_id:
                            self._retrieve_batch_error_results(batch)
                        return
                    elif current_status == "cancelled":
                        print("Batch job was cancelled.")
                        return
                    
                print(f"Waiting 20 seconds before next check... (elapsed: {int(time.time() - start_time)}s)")
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"Error polling batch status: {str(e)}")
                print(f"Waiting 20 seconds before retry...")
                time.sleep(poll_interval)
        
        print(f"Batch polling timeout reached after {timeout} seconds.")
    
    def _retrieve_batch_results(self, batch):
        """
        Retrieve and process results from a completed batch job
        """
        try:
            if not batch.output_file_id:
                print("No output file ID found for completed batch job.")
                return
            
            print("Downloading batch results...")
            content = self.agent.client.files.content(file_id=batch.output_file_id)
            
            # Save results to file
            results_file_path = self.project_path / "claude_batch_results.jsonl"
            content.write_to_file(results_file_path)
            print(f"Batch results saved to {results_file_path}")
            
            # Process results and update metadata
            self._process_batch_results(results_file_path)
            
        except Exception as e:
            print(f"Error retrieving batch results: {str(e)}")
    
    def _retrieve_batch_error_results(self, batch):
        """
        Retrieve and process error results from a failed batch job
        """
        try:
            if not batch.error_file_id:
                print("No error file ID found for failed batch job.")
                return
            
            print("Downloading batch error results...")
            content = self.agent.client.files.content(file_id=batch.error_file_id)
            
            # Save error results to file
            error_file_path = self.project_path / "claude_batch_errors.jsonl"
            content.write_to_file(error_file_path)
            print(f"Batch error results saved to {error_file_path}")
            
            # Process error results
            self._process_batch_error_results(error_file_path)
            
        except Exception as e:
            print(f"Error retrieving batch error results: {str(e)}")
    
    def _process_batch_results(self, results_file_path):
        """
        Process batch results and update metadata with summaries
        """
        try:
            metadata = self.load_metadata()
            updated_count = 0
            
            with open(results_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            result = json.loads(line)
                            custom_id = result.get("custom_id")
                            response = result.get("response", {})
                            body = response.get("body", {})
                            choices = body.get("choices", [])
                            
                            if custom_id and choices:
                                content = choices[0].get("message", {}).get("content", "")
                                # Try to parse the content as JSON to extract the summary
                                try:
                                    summary_data = json.loads(content)
                                    summary = summary_data.get("summary", content)
                                except json.JSONDecodeError:
                                    summary = content
                                
                                # Update metadata
                                if custom_id in metadata:
                                    metadata[custom_id]["summary"] = summary
                                    metadata[custom_id]["last_updated"] = time.time()
                                    updated_count += 1
                                    print(f"Updated summary for {custom_id}")
                        except json.JSONDecodeError:
                            print(f"Error parsing result line: {line}")
            
            # Save updated metadata
            self.save_metadata(metadata)
            print(f"Updated {updated_count} file summaries in metadata")
            print(f"Metadata saved to {self.metadata_file}")
            
        except Exception as e:
            print(f"Error processing batch results: {str(e)}")
    
    def _process_batch_error_results(self, error_file_path):
        """
        Process batch error results and log failed requests
        """
        try:
            error_count = 0
            with open(error_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            error_result = json.loads(line)
                            custom_id = error_result.get("custom_id")
                            error = error_result.get("error", {})
                            error_code = error.get("code", "Unknown")
                            error_message = error.get("message", "Unknown error")
                            
                            print(f"Batch request failed for {custom_id}: {error_code} - {error_message}")
                            error_count += 1
                        except json.JSONDecodeError:
                            print(f"Error parsing error result line: {line}")
            
            print(f"Total failed batch requests: {error_count}")
            
        except Exception as e:
            print(f"Error processing batch error results: {str(e)}")
    
    def _get_file_type_info(self):
        """
        Analyze batch requests to get information about file types
        Returns a dictionary with file extensions and their counts
        """
        file_types = {}
        
        for request in self.batch_requests:
            custom_id = request.get("custom_id", "")
            if custom_id:
                # Extract file extension
                file_extension = os.path.splitext(custom_id)[1]
                if file_extension:
                    file_types[file_extension] = file_types.get(file_extension, 0) + 1
                else:
                    # For files without extension, use the full filename
                    file_types[custom_id] = file_types.get(custom_id, 0) + 1
        
        return file_types
    
    def _get_user_file_type_selection(self, file_type_info):
        """
        Show file types to user and get their selection of file types to exclude
        Returns a list of file extensions to exclude
        """
        if not file_type_info:
            return []
        
        # Display file type information
        print("\nFile types to be processed:")
        file_type_list = list(file_type_info.items())
        for i, (ext, count) in enumerate(file_type_list, 1):
            print(f"{ext}-{count}files", end=", " if i < len(file_type_list) else "\n")
        
        print("\nSelect file types to EXCLUDE from processing:")
        for i, (ext, count) in enumerate(file_type_list, 1):
            print(f"{i}) {ext}")
        
        print("Enter numbers separated by commas (e.g., 1,3) or press Enter to include all:")
        user_input = input().strip()
        
        excluded_types = []
        if user_input:
            try:
                selected_indices = [int(x.strip()) for x in user_input.split(",")]
                for index in selected_indices:
                    if 1 <= index <= len(file_type_list):
                        excluded_types.append(file_type_list[index - 1][0])
            except ValueError:
                print("Invalid input. Including all file types.")
        
        return excluded_types
    
    def _filter_batch_requests_by_type(self, excluded_types):
        """
        Filter batch requests based on excluded file types
        Returns filtered list of batch requests
        """
        if not excluded_types:
            return self.batch_requests
        
        filtered_requests = []
        for request in self.batch_requests:
            custom_id = request.get("custom_id", "")
            if custom_id:
                file_extension = os.path.splitext(custom_id)[1]
                if file_extension not in excluded_types:
                    filtered_requests.append(request)
        
        print(f"Filtered out {len(self.batch_requests) - len(filtered_requests)} files")
        print(f"Proceeding with {len(filtered_requests)} files")
        
        return filtered_requests
    
    def _get_user_cost_confirmation(self, requests):
        """
        Estimate cost and get user confirmation before sending batch request
        Returns True if user confirms, False otherwise
        """
        # Estimate cost based on number of requests
        # This is a rough estimation - in practice, this would depend on the model and usage
        num_requests = len(requests)
        estimated_cost = num_requests * 0.0005  # Example cost per request
        
        print(f"\nEstimated cost for {num_requests} requests: ${estimated_cost:.4f}")
        print("Do you want to proceed with the batch request? (y/n):")
        
        user_input = input().strip().lower()
        return user_input in ['y', 'yes']


def main():
    if not PROJECT_PATH:
        print("Error: PROJECT_PATH is not set. Please set the absolute path to your project folder.")
        return
    
    try:
        agent = ClaudeAgent()
        monitor = ProjectMonitor(PROJECT_PATH, agent)
        
        # Check command line arguments
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == "--check-batch":
                batch_id = sys.argv[2] if len(sys.argv) > 2 else None
                monitor.check_batch_status(batch_id)
            elif sys.argv[1] == "--poll-batch":
                batch_id = sys.argv[2] if len(sys.argv) > 2 else None
                timeout = int(sys.argv[3]) if len(sys.argv) > 3 else None
                monitor.poll_batch_status(batch_id, timeout)
            else:
                monitor.scan_project()
        else:
            monitor.scan_project()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()