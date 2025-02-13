import os
import subprocess
import sys
import csv
import shutil
from utils import log_message, BASE_DIR

CSV_FILE = os.path.join(BASE_DIR, "execution_results.csv")  # CSV file at the base level

def create_csv_file():
    """Creates the CSV file with headers if it doesn't exist."""
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Project ID", "R/Rmd Script", "Execution Status"])
        print(f"✅ Created new execution results file: {CSV_FILE}")
    else:
        print(f"📂 Execution results will be appended to: {CSV_FILE}")


def log_execution_to_csv(project_id, file_name, status):
    """Logs execution results to a global CSV file."""
    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([project_id, file_name, status])

    print(f"✅ Logged execution result for {file_name} in {CSV_FILE}")


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
            print(f"Error listing {ext} files in {directory}: {result.stderr}")
        else:
            files.extend(result.stdout.strip().split("\n"))

    return [file for file in files if file]


def backup_repo2docker(project_id):
    """Backs up the entire repo2docker folder using Python file operations."""
    project_path = os.path.join(BASE_DIR, project_id, "repo2docker")
    backup_path = os.path.join(BASE_DIR, project_id, "repo2docker_backup")

    print(f"📂 Creating backup of {project_path} in {backup_path}, excluding execution_log.txt...")

    # Ensure the source folder exists
    if not os.path.exists(project_path):
        print(f"❌ Error: repo2docker directory '{project_path}' not found!")
        return

    # Ensure the backup directory exists, or create it
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)  # Remove old backup if it exists
    os.makedirs(backup_path)

    # Copy all files except `execution_log.txt`
    for item in os.listdir(project_path):
        src_item = os.path.join(project_path, item)
        dest_item = os.path.join(backup_path, item)
        
        # Skip execution_log.txt
        if item == "execution_log.txt":
            continue
        
        if os.path.isdir(src_item):
            shutil.copytree(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)

    print(f"✅ Backup completed at {backup_path}")

def restore_repo2docker(project_id):
    """Restores the entire repo2docker folder using Python file operations."""
    project_path = os.path.join(BASE_DIR, project_id, "repo2docker")
    backup_path = os.path.join(BASE_DIR, project_id, "repo2docker_backup")

    print(f"♻️ Restoring {project_path} from {backup_path}, keeping execution_log.txt intact...")

    # Ensure the backup exists
    if not os.path.exists(backup_path):
        print(f"⚠️ No backup found! Skipping restore step.")
        return

    # Ensure the project directory exists, or create it
    if os.path.exists(project_path):
        # Remove everything except `execution_log.txt`
        for item in os.listdir(project_path):
            if item == "execution_log.txt":
                continue
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    else:
        os.makedirs(project_path)

    # Restore files from the backup
    for item in os.listdir(backup_path):
        src_item = os.path.join(backup_path, item)
        dest_item = os.path.join(project_path, item)
        
        if os.path.isdir(src_item):
            shutil.copytree(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)

    print(f"✅ Restore completed, execution_log.txt remains unchanged.")

def execute_r_file(container_name, r_file, log_file, project_id):
    """Executes an R file inside the container, backs up, and restores repo2docker while keeping logs intact."""
    
    # Backup the entire repo2docker directory before execution
    backup_repo2docker(project_id)

    print(f"Executing {r_file} in container {container_name}...")
    command = [
        "docker", "exec", container_name,
        "Rscript", r_file
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with open(log_file, "a") as log:
        log.write(f"File: {r_file}\n")
        if result.returncode == 0:
            log.write("Execution Successful:\n")
            log.write(result.stdout + "\n")
            execution_status = "Successful"
        else:
            log.write("Execution Failed:\n")
            log.write(result.stderr + "\n")
            execution_status = "Failed"
        log.write("=" * 40 + "\n")

    # Restore the entire repo2docker directory after execution, keeping logs
    restore_repo2docker(project_id)

    # Append result to CSV
    log_execution_to_csv(project_id, r_file, execution_status)

def render_rmd_file(container_name, rmd_file, log_file, project_id):
    """Renders an Rmd file inside the container, manages backup and restores output files while keeping logs intact."""
    
    # Backup the entire repo2docker directory before execution
    backup_repo2docker(project_id)

    print(f"Rendering {rmd_file} in container {container_name}...")
    
    render_command = (
        f"R -e \"rmarkdown::render('{rmd_file}', output_dir='/data/repo2docker')\""
    )
    command = ["docker", "exec", container_name, "bash", "-c", render_command]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with open(log_file, "a") as log:
        log.write(f"File: {rmd_file}\n")
        if result.returncode == 0:
            log.write("Rendering Successful:\n")
            log.write(result.stdout + "\n")
            execution_status = "Successful"
        else:
            log.write("Rendering Failed:\n")
            log.write(result.stderr + "\n")
            execution_status = "Failed"
        log.write("=" * 40 + "\n")

    # Restore the entire repo2docker directory after execution, keeping execution_log.txt intact
    restore_repo2docker(project_id)

    # Append result to CSV
    log_execution_to_csv(project_id, rmd_file, execution_status)

def run_all_files_in_container(project_id):
    """Automates the process of running R and Rmd files inside the container."""
    container_name = f"repo2docker-{project_id}"
    log_file = os.path.join(BASE_DIR, project_id, "execution_log.txt")

    # Ensure the container is running
    try:
        inspect_command = [
            "docker", "inspect", "-f", "{{.State.Running}}", container_name
        ]
        result = subprocess.run(inspect_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if "true" not in result.stdout:
            print(f"Container {container_name} is not running.")
            return
    except subprocess.CalledProcessError:
        print(f"Container {container_name} is not running.")
        return

    # List and execute R and Rmd files only from the repo2docker folder
    repo2docker_dir = "/data/repo2docker"
    files = list_files(container_name, directory=repo2docker_dir, extensions=[".R", ".Rmd"])
    if not files:
        print(f"No R or Rmd files found in {repo2docker_dir} for container {container_name}.")
        return

    print(f"Found {len(files)} R and Rmd files in {repo2docker_dir}. Executing them now...")
    for file in files:
        if file.endswith(".R"):
            execute_r_file(container_name, file, log_file, project_id)
        elif file.endswith(".Rmd"):
            render_rmd_file(container_name, file, log_file, project_id)

    print(f"Execution completed for project {project_id}. Logs at {log_file}. Results stored in {CSV_FILE}")

def process_projects(project_ids):
    """Processes multiple projects sequentially, ensuring results are logged incrementally."""
    create_csv_file()  # Ensure the CSV file is created only once at the start

    for project_id in project_ids:
        print(f"\n=== Processing Project: {project_id} ===")
        try:
            run_all_files_in_container(project_id)
        except Exception as e:
            print(f"❌ Error processing project '{project_id}': {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 execute_files_in_container.py <PROJECT_ID> [<PROJECT_ID> ...] or provide a file with project IDs.")
        sys.exit(1)

    # Check if input is a file containing project IDs
    if os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as file:
            project_ids = [line.strip() for line in file if line.strip()]
    else:
        project_ids = sys.argv[1:]

    process_projects(project_ids)
