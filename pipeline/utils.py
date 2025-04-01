import os
import time

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGS_DIR = "logs"
REPOS_DIR = "repos"
RESULTS_DIR = "results"
DOWNLOADS_DIR = "downloads"
METADATA_DIR = "metadata"


def log_message(project_id, stage, message, execution_log=False):
    """Log a message with timestamp to console and file."""
    # Generate timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the full log message
    log_entry = f"[{timestamp}] [{project_id}] [{stage}] {message}"
    
    # Print to console for non-execution logs
    if not execution_log:
        print(log_entry)
    
    # Write to file (both regular and execution logs)
    log_file = os.path.join(LOGS_DIR, f"{project_id}{'_execution' if execution_log else ''}.log")
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")

def get_project_path(project_id):
    """Returns the path to the project repo directory."""
    return os.path.join(REPOS_DIR, f"{project_id}_repo")

def get_src_path(project_id):
    """Returns the path to the project source directory."""
    return os.path.join(get_project_path(project_id), f"{project_id}_src")

def get_zip_file_path(project_id):
    """Returns the path to the project zip file."""
    return os.path.join(DOWNLOADS_DIR, f"{project_id}.zip")
