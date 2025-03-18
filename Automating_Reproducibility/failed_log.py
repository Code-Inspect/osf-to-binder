import os
import re
import pandas as pd

# Define relative file paths (assuming log file is inside a "logs" folder)
BASE_DIR = "/data/meet/CodeInspector/Automating_Reproducibility"  # Adjust based on your directory structure
log_file_path = os.path.join(BASE_DIR, "failed_execution_log.txt")
success_output_path = os.path.join(BASE_DIR, "successful_projects.csv")
failed_output_path = os.path.join(BASE_DIR, "failed_projects.csv")

# Ensure the log folder exists
if not os.path.exists(BASE_DIR):
    print(f"⚠️ Log folder '{BASE_DIR}' not found. Please ensure the log file is in the correct directory.")
    exit()

# Read the log file
with open(log_file_path, "r") as file:
    log_data = file.readlines()

# Lists to store successful and failed project IDs
successful_projects = []
failed_projects = []

# Regex patterns
project_pattern = re.compile(r"=== Project (\w+) Execution Log ===")
build_success_pattern = re.compile(r"✅ Container built successfully")

current_project = None
container_built = False

# Iterate over log lines
for line in log_data:
    project_match = project_pattern.search(line)
    if project_match:
        # Store the previous project in the correct list
        if current_project:
            if container_built:
                successful_projects.append(current_project)
            else:
                failed_projects.append(current_project)

        # Reset for the new project
        current_project = project_match.group(1)
        container_built = False  # Reset flag

    # Check for successful build
    if build_success_pattern.search(line):
        container_built = True

# Store the last project
if current_project:
    if container_built:
        successful_projects.append(current_project)
    else:
        failed_projects.append(current_project)

# Create DataFrames
df_successful = pd.DataFrame(successful_projects, columns=["Project ID"])
df_failed = pd.DataFrame(failed_projects, columns=["Project ID"])

# Save results to CSV
df_successful.to_csv(success_output_path, index=False)
df_failed.to_csv(failed_output_path, index=False)

# Display confirmation messages
print(f"✅ Successfully built project IDs saved to '{success_output_path}'")
print(f"❌ Failed project IDs saved to '{failed_output_path}'")

# Display the first few rows
df_successful.head(), df_failed.head()
