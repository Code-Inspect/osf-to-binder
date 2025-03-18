import os

# Define file paths
BASE_DIR = "/data/meet/CodeInspector/Automating_Reproducibility"  # Adjust based on your directory structure
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Logs directory
PROJECTS_LIST_FILE = os.path.join(BASE_DIR, "project_ids.txt")  # The .txt file with project IDs
MERGED_LOG_FILE = os.path.join(LOGS_DIR, "merged_logs.txt")  # Final merged file

def merge_execution_logs():
    """Merges {project_id}.log from the logs directory into one file."""
    if not os.path.exists(PROJECTS_LIST_FILE):
        print(f"❌ Error: Project list file '{PROJECTS_LIST_FILE}' not found!")
        return

    if not os.path.exists(LOGS_DIR):
        print(f"❌ Error: Logs directory '{LOGS_DIR}' not found!")
        return

    with open(PROJECTS_LIST_FILE, "r") as file:
        project_ids = [line.strip() for line in file if line.strip()]

    if not project_ids:
        print("⚠️ No project IDs found in the file.")
        return

    print(f"📂 Merging log files from {LOGS_DIR} ({len(project_ids)} projects)...")

    # Open the merged log file in append mode
    with open(MERGED_LOG_FILE, "a") as merged_log:
        for project_id in project_ids:
            log_file_path = os.path.join(LOGS_DIR, f"{project_id}_execution.log")  # Look for {project_id}.log in logs/

            if os.path.exists(log_file_path):
                print(f"✅ Found log file for {project_id}, merging...")
                with open(log_file_path, "r") as log_file:
                    merged_log.write(f"\n=== Project {project_id} Log ===\n")
                    merged_log.write(log_file.read())
                    merged_log.write("\n" + "=" * 50 + "\n")  # Separator between logs
            else:
                print(f"⚠️ No {project_id}.log found in {LOGS_DIR}, skipping.")

    print(f"✅ Merging completed! All logs saved in {MERGED_LOG_FILE}")

# Run the function
merge_execution_logs()
