import os
import subprocess
import sys
from utils import log_message, BASE_DIR


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

def execute_r_file(container_name, r_file, log_file):
    """Executes an R file inside the container."""
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
        else:
            log.write("Execution Failed:\n")
            log.write(result.stderr + "\n")
        log.write("=" * 40 + "\n")

def render_rmd_file(container_name, rmd_file, log_file):
    """Renders an Rmd file inside the container."""
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
        else:
            log.write("Rendering Failed:\n")
            log.write(result.stderr + "\n")
        log.write("=" * 40 + "\n")

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
            execute_r_file(container_name, file, log_file)
        elif file.endswith(".Rmd"):
            render_rmd_file(container_name, file, log_file)

    print(f"Execution completed. Check the log file at {log_file}")

def process_projects(project_ids):
    """Processes multiple projects."""
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
