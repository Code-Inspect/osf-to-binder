import os
import subprocess
import sys
import argparse
from git import Repo
from utils import log_message, BASE_DIR

def build_and_run_container(project_id, repo_only=False, build_and_run=False):
    """Builds and runs the repo2docker container for a project."""
    project_path = os.path.join(BASE_DIR, f"{project_id}_repo")
    if not os.path.exists(project_path):
        print(f"❌ Error: Project directory for project '{project_id}' not found at '{project_path}'")
        return None

    image_name = f"repo2docker-{project_id}-test"
    container_name = image_name

    # Build the container
    build_command = [
        "repo2docker",
        "--no-run",
        "--user-id", "1000",
        "--user-name", "rstudio",
        "--image-name", image_name,
        project_path
    ]
    log_message(project_id, "CONTAINER SETUP", "⚙️ Building Docker container...")

    if repo_only:
        print(f"📦 Building repository for project '{project_id}'...")
        try:
            subprocess.run(build_command, check=True)
            print(f"✅ Repository built successfully for project '{project_id}'.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: Failed to build the repository for project '{project_id}'.")
            print(f"Command: {' '.join(e.cmd)} | Return Code: {e.returncode}")
        return None

    if build_and_run:
        print(f"🚀 Building and running container for project '{project_id}'...")
        try:
            subprocess.run(build_command, check=True)
            log_message(project_id, "CONTAINER BUILD", "✅ Container built successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: Failed to build the container for project '{project_id}'.")
            print(f"Command: {' '.join(e.cmd)} | Return Code: {e.returncode}")
            return None

        # Remove existing container if exists
        try:
            subprocess.run(["docker", "rm", "-f", container_name], check=True)
            print(f"🗑️ Removed existing container '{container_name}'.")
        except subprocess.CalledProcessError:
            print(f"ℹ️ No existing container '{container_name}' found to remove.")

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
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: Failed to start the container for project '{project_id}'.")
            print(f"Command: {' '.join(e.cmd)} | Return Code: {e.returncode}")
            log_message(project_id, "CONTAINER ERROR", f"❌ Error during Docker operation: {e}")
            return None

        return container_name

def process_projects(project_ids, repo_only=False, build_and_run=False):
    """Processes multiple projects."""
    for project_id in project_ids:
        print(f"\n=== 🚀 Processing Project: '{project_id}' ===")
        try:
            container_name = build_and_run_container(project_id, repo_only, build_and_run)
            if container_name:
                print(f"✅ Container '{container_name}' is running for project '{project_id}'.")
            else:
                print(f"⚠️ Skipped running the container for project '{project_id}'.")
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
