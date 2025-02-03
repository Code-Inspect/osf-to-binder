# utils.py
import os
from datetime import datetime

def log_message(project_id, section, message):
    """
    Logs messages to execution_log.txt with timestamps and structured sections.

    Parameters:
    - project_id (str): The ID of the project.
    - section (str): The section name (e.g., "CONTAINER BUILD", "R EXECUTION").
    - message (str): The message to log (e.g., success or error message).
    """
    log_file = os.path.join("/data/meet/pipeline", project_id, "execution_log.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure the log file directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "a") as f:
        f.write(f"\n==== [{section}] ====\n")
        f.write(f"[{timestamp}] {message}\n")
        f.write("=" * 40 + "\n")
