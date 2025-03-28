import os
import subprocess
import sys
import csv
import shutil
import time
import pandas as pd
from utils import METADATA_DIR, REPOS_DIR, LOGS_DIR, RESULTS_DIR, log_message

RESULTS_FILE = os.path.join(RESULTS_DIR, "execution_results.csv")  # CSV file at the base level
TIMEOUT = None  # the time to wait for the container to run the script. `int` for timout in seconds. None means no timeout.


def log_execution_to_csv(project_id, file_name, status):
    """Logs execution results to a global CSV file."""
    with open(RESULTS_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([project_id, file_name, status])

    log_message(project_id, "R EXECUTION", f"✅ Logged execution result for {file_name} in {RESULTS_FILE}")


def list_files(container_name, directory, extensions):
    """Lists files with specific extensions in a given directory of the container."""
    files = []
    for ext in extensions:
        command = [
            "docker", "exec", container_name,
            "find", directory, "-name", f"*{ext}"
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            log_message(container_name, "R EXECUTION", f"Error listing {ext} files in {directory}: {result.stderr}")
        else:
            files.extend(result.stdout.strip().split("\n"))

    return [file for file in files if file]


def backup_project_src(project_id):
    """Backs up the project source directory."""
    project_path = os.path.join(REPOS_DIR, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")
    backup_path = os.path.join(project_path, f"{project_id}_src_backup")

    log_message(project_id, "R EXECUTION", f"📂 Creating backup of {src_path} in {backup_path}...")

    # Ensure the source folder exists
    if not os.path.exists(src_path):
        log_message(project_id, "R EXECUTION", f"❌ Error: Source directory '{src_path}' not found!")
        return

    # Ensure the backup directory exists, or create it
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)  # Remove old backup if it exists
    os.makedirs(backup_path)

    # Copy all files
    for item in os.listdir(src_path):
        src_item = os.path.join(src_path, item)
        dest_item = os.path.join(backup_path, item)
        
        if os.path.isdir(src_item):
            shutil.copytree(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)

    log_message(project_id, "R EXECUTION", f"✅ Backup completed at {backup_path}")

def restore_project_src(project_id):
    """Restores the project source directory from backup."""
    project_path = os.path.join(REPOS_DIR, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")
    backup_path = os.path.join(project_path, f"{project_id}_src_backup")

    log_message(project_id, "R EXECUTION", f"♻️ Restoring {src_path} from {backup_path}...")

    # Ensure the backup exists
    if not os.path.exists(backup_path):
        log_message(project_id, "R EXECUTION", f"⚠️ No backup found! Skipping restore step.")
        return

    # Remove current src directory and replace with backup
    if os.path.exists(src_path):
        shutil.rmtree(src_path)
    
    shutil.copytree(backup_path, src_path)
    log_message(project_id, "R EXECUTION", f"✅ Restore completed.")

def execute_r_file(container_name, r_file, log_file, project_id):
    """Executes an R file inside the container, backs up, and restores project source."""
    
    # Backup the project source directory before execution
    backup_project_src(project_id)

    # Get the correct working directory from the file path
    r_script_dir = os.path.dirname(r_file)

    log_message(project_id, "R EXECUTION", f"Executing {r_file} in container {container_name}...")

    command = [
        "docker", "exec", container_name,
        "bash", "-c", f'cd "{r_script_dir}" && Rscript "{os.path.basename(r_file)}"'
    ]
    
    try:
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=TIMEOUT
        )
    except subprocess.TimeoutExpired:
        result = subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr=f"Execution timed out after {TIMEOUT} seconds")

    # Log execution results
    log_message(project_id, "R EXECUTION", f"File: {r_file}", execution_log=True)
    
    if result.returncode == 0:
        log_message(project_id, "R EXECUTION", f"Execution Successful:\n{result.stdout}", execution_log=True)
        execution_status = "Successful"
    else:
        log_message(project_id, "R EXECUTION", f"Execution Failed:\n{result.stderr}", execution_log=True)
        execution_status = "Failed"
    
    log_message(project_id, "R EXECUTION", "=" * 40, execution_log=True)

    restore_project_src(project_id)

    log_execution_to_csv(project_id, r_file, execution_status)

def render_rmd_file(container_name, rmd_file, log_file, project_id):
    """Renders an Rmd file inside the container, manages backup and restores output files."""
    
    # Backup the project source directory before execution
    backup_project_src(project_id)

    log_message(project_id, "R EXECUTION", f"Rendering {rmd_file} in container {container_name}...")
    
    render_command = (
        f"R -e \"rmarkdown::render('{rmd_file}', output_dir='/data/{project_id}_src')\""
    )
    command = ["docker", "exec", container_name, "bash", "-c", render_command]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Log rendering results
    log_message(project_id, "R EXECUTION", f"File: {rmd_file}", execution_log=True)
    
    if result.returncode == 0:
        log_message(project_id, "R EXECUTION", f"Rendering Successful:\n{result.stdout}", execution_log=True)
        execution_status = "Successful"
    else:
        log_message(project_id, "R EXECUTION", f"Rendering Failed:\n{result.stderr}", execution_log=True)
        execution_status = "Failed"
    
    log_message(project_id, "R EXECUTION", "=" * 40, execution_log=True)

    restore_project_src(project_id)

    log_execution_to_csv(project_id, rmd_file, execution_status)
    
def run_all_files_in_container(project_id):
    """Automates execution of only the R and Rmd files listed in the CSV for the given project."""
    container_name = f"repo2docker-{project_id}"
    log_file = os.path.join(LOGS_DIR, f"{project_id}_execution.log")

    # Load CSV file
    cleaned_csv_path = os.path.join(METADATA_DIR, "project_id_r_code_file.csv")
    df_project_files = pd.read_csv(cleaned_csv_path)

    # Ensure the container is running
    try:
        inspect_command = ["docker", "inspect", "-f", "{{.State.Running}}", container_name]
        result = subprocess.run(inspect_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if "true" not in result.stdout:
            log_message(project_id, "R EXECUTION", f"Container {container_name} is not running.")
            return
    except subprocess.CalledProcessError:
        log_message(project_id, "R EXECUTION", f"Container {container_name} is not running.")
        return

    # List available R and Rmd files in the source directory
    src_dir = f"/data/{project_id}_src"  # Path inside the container
    available_files = list_files(container_name, directory=src_dir, extensions=[".R", ".Rmd", ".r", ".rmd"])

    if not available_files:
        log_message(project_id, "R EXECUTION", f"No R or Rmd files found in {src_dir} for container {container_name}.")
        return

    # Filter the files from the CSV for the specific project
    project_files = df_project_files[df_project_files["Project ID"] == project_id]["R Code File"].tolist()

    if not project_files:
        log_message(project_id, "R EXECUTION", f"⚠️ No matching R files found for project {project_id} in the CSV. Skipping execution.")
        return

    # Normalize extensions to ensure both `.R` and `.r` are treated the same
    matched_files = [
        file for file in available_files
        if os.path.basename(file).lower().endswith((".r", ".rmd")) and os.path.basename(file).lower() in [f.lower() for f in project_files]
        and "src_backup" not in file
    ]

    if not matched_files:
        log_message(project_id, "R EXECUTION", f"⚠️ None of the expected files from the CSV were found inside the container for project {project_id}. Skipping execution.")
        return

    log_message(project_id, "R EXECUTION", f"Found {len(matched_files)} R and Rmd files in {src_dir}. Executing them now...")

    execution_start = time.time()

    for file in matched_files:
        file_start = time.time()
        # remove the /data/ prefix
        file = file[len("/data/"):]
        if file.endswith((".R", ".r")):
            execute_r_file(container_name, file, log_file, project_id)
        elif file.endswith((".Rmd", ".rmd")):
            render_rmd_file(container_name, file, log_file, project_id)
        file_end = time.time()

    execution_end = time.time()

    # Log the total execution time
    log_message(project_id, "R EXECUTION", f"⏳ Total execution time for project {project_id}: {execution_end - execution_start:.2f} seconds", execution_log=True)

    log_message(project_id, "R EXECUTION", f"Execution completed for project {project_id}. Logs at {log_file}. Results stored in {RESULTS_FILE}")

def execute_r_scripts(project_id):
    """Executes R scripts in the container."""
    # Creates the CSV file with headers if it doesn't exist.
    if not os.path.isfile(RESULTS_FILE):
        with open(RESULTS_FILE, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Project ID", "R/Rmd Script", "Execution Status"])
        log_message(project_id, "R EXECUTION", f"✅ Created new execution results file: {RESULTS_FILE}")
    else:
        log_message(project_id, "R EXECUTION", f"📂 Execution results will be appended to: {RESULTS_FILE}")

    log_message(project_id, "R EXECUTION", f"Executing R scripts in the container for project ID: {project_id}")
    try:
        run_all_files_in_container(project_id)
        return True
    except Exception as e:
        log_message(project_id, "R EXECUTION", f"❌ Failed to execute R scripts: {e}")
        return False

if __name__ == "__main__":
    """Main entry point when script is run directly."""
    if len(sys.argv) < 2:
        print("Usage: python3 execute_files_in_container.py <PROJECT_ID> [<PROJECT_ID> ...] or provide a file with project IDs.")
        sys.exit(1)
        
    # Handle project IDs from a file or directly from input
    project_ids = []
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as file:
            project_ids = [line.strip() for line in file if line.strip()]
    else:
        project_ids = sys.argv[1:]
    
    for project_id in project_ids:
        execute_r_scripts(project_id)
