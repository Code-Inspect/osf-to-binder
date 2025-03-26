import os
import subprocess
import sys
import argparse
from utils import log_message, REPOS_DIR

def check_project_exists(project_id):
    """Checks if the project directory exists and returns the path if it does."""
    project_path = os.path.join(REPOS_DIR, f"{project_id}_repo")
    if not os.path.exists(project_path):
        print(f"❌ Error: Project directory for project '{project_id}' not found at '{project_path}'")
        return None
    return project_path

def get_image_and_container_name(project_id):
    """Returns the image and container names for a project."""
    image_name = f"repo2docker-{project_id}-test"
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
    
    log_message(project_id, "CONTAINER SETUP", "⚙️ Building Docker container...")
    
    try:
        subprocess.run(build_command, check=True)
        log_message(project_id, "CONTAINER BUILD", "✅ Container built successfully.")
        return image_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Failed to build the container for project '{project_id}'.")
        print(f"Command: {' '.join(e.cmd)} | Return Code: {e.returncode}")
        return None

def remove_existing_container(container_name):
    """Removes an existing container if it exists."""
    try:
        subprocess.run(["docker", "rm", "-f", container_name], check=True)
        print(f"🗑️ Removed existing container '{container_name}'.")
    except subprocess.CalledProcessError:
        print(f"ℹ️ No existing container '{container_name}' found to remove.")

def run_docker_container(project_id, image_name, project_path):
    """Runs a Docker container from the built image."""
    _, container_name = get_image_and_container_name(project_id)
    
    # Remove existing container if exists
    remove_existing_container(container_name)
    
    # Run the container
    run_command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-v", f"{os.path.abspath(project_path)}:/data",
        image_name
    ]
    
    try:
        subprocess.run(run_command, check=True)
        print(f"✅ Container '{container_name}' started successfully for project '{project_id}'.")
        log_message(project_id, "CONTAINER RUN", "✅ Container is running.")
        return container_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Failed to start the container for project '{project_id}'.")
        print(f"Command: {' '.join(e.cmd)} | Return Code: {e.returncode}")
        log_message(project_id, "CONTAINER ERROR", f"❌ Error during Docker operation: {e}")
        return None

def build_repository(project_id):
    """Builds the repository using repo2docker."""
    log_message(project_id, "BUILD", f"=== Building repository for project: {project_id} ===")
    
    try:
        project_path = check_project_exists(project_id)
        if not project_path:
            return False
            
        print(f"📦 Building repository for project '{project_id}'...")
        
        # Use the build_docker_image function instead of duplicating the build command
        image_name = build_docker_image(project_id, project_path)
        if image_name:
            print(f"✅ Repository built successfully for project '{project_id}'.")
            return True
        return False
    except Exception as e:
        log_message(project_id, "BUILD", f"❌ Failed to build repository: {e}")
        return False
    
def run_container(project_id):
    """Runs the container for the project."""
    log_message(project_id, "CONTAINER", f"=== Running container for project: {project_id} ===")
    
    try:
        project_path = check_project_exists(project_id)
        if not project_path:
            return False
            
        print(f"🚀 Building and running container for project '{project_id}'...")
        
        # Build the image
        image_name = build_docker_image(project_id, project_path)
        if not image_name:
            return False
            
        # Run the container
        container_name = run_docker_container(project_id, image_name, project_path)
        return container_name is not None
    except Exception as e:
        log_message(project_id, "CONTAINER", f"❌ Failed to run container: {e}")
        return False

def process_projects(project_ids, repo_only=False, build_and_run=False):
    """Processes multiple projects."""
    for project_id in project_ids:
        print(f"\n=== 🚀 Processing Project: '{project_id}' ===")
        try:
            if repo_only:
                success = build_repository(project_id)
                if success:
                    print(f"✅ Repository built successfully for project '{project_id}'.")
                else:
                    print(f"⚠️ Failed to build repository for project '{project_id}'.")
            elif build_and_run:
                success = run_container(project_id)
                if success:
                    print(f"✅ Container is running for project '{project_id}'.")
                else:
                    print(f"⚠️ Failed to run container for project '{project_id}'.")
        except Exception as e:
            print(f"❌ Unexpected error for project '{project_id}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and Run Repo2Docker Containers")
    parser.add_argument("--project-id", nargs='+', help="List of project IDs or path to a file containing project IDs")
    parser.add_argument("--repo-only", action="store_true", help="Only build the repository without running the container")
    parser.add_argument("--build-and-run", action="store_true", help="Build and run the container")

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
        print("❌ Error: No project IDs provided.")
        sys.exit(1)

    # Process projects
    process_projects(project_ids, repo_only=args.repo_only, build_and_run=args.build_and_run)
