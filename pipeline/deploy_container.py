import os
import subprocess
import sys
import argparse
from utils import log_message, REPOS_DIR, LOGS_DIR

def check_project_exists(project_id):
    """Checks if the project directory exists and returns the path if it does."""
    project_path = os.path.join(REPOS_DIR, f"{project_id}_repo")
    if not os.path.exists(project_path):
        log_message(project_id, "CONTAINER BUILD", f"❌ Project directory not found at '{project_path}'")
        return None
    return project_path

def get_image_and_container_name(project_id):
    """Returns the image and container names for a project."""
    image_name = f"repo2docker-{project_id}"
    return image_name, image_name  # Using same name for both

def build_docker_image(project_id, project_path):
    """Builds a Docker image for the project using repo2docker."""
    image_name, _ = get_image_and_container_name(project_id)
    
    build_command = [
        "repo2docker",
        "--no-run",
        "--user-id", "1000",
        "--user-name", "rstudio",
        "--image-name", image_name,
        project_path
    ]
    
    log_message(project_id, "CONTAINER BUILD", "⚙️ Building Docker container...")
    
    try:
        repo2docker_log_file = os.path.join(LOGS_DIR, f"{project_id}_repo2docker.log")
        subprocess.run(build_command, check=True, stdout=open(repo2docker_log_file, "w"), stderr=subprocess.STDOUT)
        log_message(project_id, "CONTAINER BUILD", "✅ Container built successfully.")
        return image_name
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER BUILD", f"❌ Failed to build container: {e.returncode}")
        log_message(project_id, "CONTAINER BUILD", f"{' '.join(e.cmd)}")
        return None

def build_image(project_id):
    """Builds the docker image using repo2docker."""
    log_message(project_id, "CONTAINER BUILD", f"=== Building repository for project: {project_id} ===")
    
    try:
        project_path = check_project_exists(project_id)
        if not project_path:
            return False
            
        log_message(project_id, "CONTAINER BUILD", f"📦 Building repository...")
        
        image_name = build_docker_image(project_id, project_path)
        if image_name:
            return True
        return False
    except Exception as e:
        log_message(project_id, "CONTAINER BUILD", f"❌ Failed to build repository: {e}")
        return False
    
def run_container(project_id):
    """Runs the container for the project."""
    log_message(project_id, "CONTAINER RUN", f"=== Running container for project: {project_id} ===")
    
    project_path = check_project_exists(project_id)
    if not project_path:
        return False

    image_name, container_name = get_image_and_container_name(project_id)

    # Removes an existing container if it exists.
    try:
        subprocess.run(["docker", "rm", "-f", container_name], check=True)
        log_message(project_id, "CONTAINER RUN", f"🗑️ Removed existing container '{container_name}'.")
    except subprocess.CalledProcessError:
        log_message(project_id, "CONTAINER RUN", f"ℹ️ No existing container '{container_name}' found to remove.")
    
    # Run the container
    run_command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-v", f"{os.path.abspath(project_path)}:/data",
        image_name
    ]
    
    try:
        subprocess.run(run_command, check=True)
        log_message(project_id, "CONTAINER RUN", f"✅ Container '{container_name}' started successfully.")
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER RUN", f"❌ Failed to start container: {e.returncode}")
        log_message(project_id, "CONTAINER RUN", f"{' '.join(e.cmd)}")
        return False

def build_and_run(project_id, no_run=False):
    """Processes a project."""
    log_message(project_id, "CONTAINER BUILD", f"=== 🚀 Processing Project: '{project_id}' ===")
    try:
        if not build_image(project_id):
            log_message(project_id, "CONTAINER BUILD", f"⚠️ Failed to build repository.")
            return False
        log_message(project_id, "CONTAINER BUILD", f"✅ Repository built successfully.")
        if no_run:
            return True
        
        if not run_container(project_id):
            log_message(project_id, "CONTAINER RUN", f"⚠️ Failed to run container.")
            return False
        log_message(project_id, "CONTAINER RUN", f"✅ Container is running.")
        return True
    except Exception as e:
        log_message(project_id, "CONTAINER BUILD", f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and Run Repo2Docker Containers")
    parser.add_argument("--project-id", nargs='+', help="List of project IDs or path to a file containing project IDs")
    parser.add_argument("--no-run", action="store_true", help="Only build the image without running the container")

    args = parser.parse_args()

    # Handle project IDs from a file or directly from input
    project_ids = []
    if args.project_id:
        if len(args.project_id) == 1 and os.path.isfile(args.project_id[0]):
            with open(args.project_id[0], "r") as file:
                project_ids = [line.strip() for line in file if line.strip()]
        else:
            project_ids = args.project_id
    else:
        print("❌ No project IDs provided.")
        sys.exit(1)

    for project_id in project_ids:
        build_and_run(project_id, no_run=args.no_run)
