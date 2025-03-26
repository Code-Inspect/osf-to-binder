# utils.py
import os
import time

# Base directory for all operations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create necessary directories
LOGS_DIR = os.path.join(BASE_DIR, "logs")
REPOS_DIR = os.path.join(BASE_DIR, "repos")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(REPOS_DIR, exist_ok=True)

def log_message(project_id, stage, message):
    """Log a message with timestamp to both console and log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = f"[{timestamp}] [{project_id}] [{stage}] {message}"
    
    print(log_entry)
    
    # Write to project-specific log file
    log_file = os.path.join(LOGS_DIR, f"{project_id}.log")
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")
