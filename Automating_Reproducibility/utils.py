# utils.py
import os
import time

# Base directory for all operations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def log_message(project_id, stage, message):
    """Log a message with timestamp to both console and log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = f"[{timestamp}] [{project_id}] [{stage}] {message}"
    
    print(log_entry)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Write to project-specific log file
    log_file = os.path.join(logs_dir, f"{project_id}.log")
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")
