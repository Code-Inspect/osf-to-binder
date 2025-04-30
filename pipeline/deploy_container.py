import os
import subprocess
import sys
import argparse
from git import Repo, GitCommandError
from utils import log_message, LOGS_DIR, get_project_path

DOCKERHUB_USERNAME = "meet261"

def check_project_exists(project_id):
    """Checks if the project directory exists and returns the path if it does."""
    project_path = get_project_path(project_id)
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


def check_docker_daemon(project_id):
    """Checks if the Docker daemon is running before proceeding."""
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        log_message(project_id, "DOCKER CHECK", "❌ Docker daemon is not running. Please start Docker.")
        return False


def push_image_to_dockerhub(project_id, push=True):
    """Pushes the image to Docker Hub if push=True."""
    if not push:
        log_message(project_id, "DOCKER PUSH", f"ℹ️ Skipping Docker push as 'push' flag is False.")
        return False

    if not check_docker_daemon(project_id):
        return False

    local_image = f"repo2docker-{project_id}"
    remote_image = f"{DOCKERHUB_USERNAME}/repo2docker-{project_id}"

    log_message(project_id, "DOCKER PUSH", f"🔁 Attempting to push image to Docker Hub: {remote_image}")

    try:
        subprocess.run(["docker", "tag", local_image, remote_image], check=True)
        log_message(project_id, "DOCKER PUSH", f"✅ Tagged image as {remote_image}")
        subprocess.run(["docker", "push", remote_image], check=True)
        log_message(project_id, "DOCKER PUSH", f"🚀 Pushed image to Docker Hub: {remote_image}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "DOCKER PUSH", f"❌ Failed to push image: {e}")
        return False


def build_image(project_id, push=False, dockerhub_username=None):
    """Builds the docker image using repo2docker."""
    log_message(project_id, "CONTAINER BUILD", f"=== Building repository for project: {project_id} ===")

    try:
        project_path = check_project_exists(project_id)
        if not project_path:
            return False

        log_message(project_id, "CONTAINER BUILD", f"📦 Building repository...")

        image_name = build_docker_image(project_id, project_path)
        if image_name:
            if push and dockerhub_username:
                push_image_to_dockerhub(project_id, dockerhub_username)
            return True
        return False
    except Exception as e:
        log_message(project_id, "CONTAINER BUILD", f"❌ Failed to build repository: {e}")
        return False


def run_container(project_id):
    """Runs the container for the project and logs R version and date to runtime.txt."""
    log_message(project_id, "CONTAINER RUN", f"=== Running container for project: {project_id} ===")

    project_path = check_project_exists(project_id)
    if not project_path:
        return False

    image_name, container_name = get_image_and_container_name(project_id)

    try:
        subprocess.run(["docker", "rm", "-f", container_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_message(project_id, "CONTAINER RUN", f"🗑️ Removed existing container '{container_name}'.")
    except subprocess.CalledProcessError:
        log_message(project_id, "CONTAINER RUN", f"ℹ️ No existing container '{container_name}' found to remove.")

    container_command = ["tail", "-f", "/dev/null"]

    run_command = [
        "docker", "run", "-d",
        "--name", container_name,
        "--user", "root",
        "-v", f"{os.path.abspath(project_path)}:/data",
        image_name
    ] + container_command

    try:
        subprocess.run(run_command, check=True)
        log_message(project_id, "CONTAINER RUN", f"✅ Container '{container_name}' started successfully.")
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER RUN", f"❌ Failed to start container: {e.returncode}")
        log_message(project_id, "CONTAINER RUN", f"{' '.join(e.cmd)}")
        return False

    container_r_command = (
        "rver <- paste0(R.version$major, '.', R.version$minor); "
        "today <- '2025-04-11'; "
        "cat(paste0('r-', rver, '-', today), file='/data/runtime.txt')"
    )

    try:
        subprocess.run(["docker", "exec", container_name, "Rscript", "-e", container_r_command], check=True)
        log_message(project_id, "CONTAINER RUN", "✅ runtime.txt written successfully inside the container.")
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER RUN", f"❌ Failed to write runtime.txt: {e}")

# Commit runtime.txt to GitHub
    runtime_path = os.path.join(project_path, "runtime.txt")
    if os.path.exists(runtime_path):
        with open(runtime_path) as f:
            content = f.read().strip()
        log_message(project_id, "CONTAINER RUN", f"📄 runtime.txt content:\n{content}")

        try:
            repo = Repo(project_path)

            # Create remote if missing
            if "origin" not in [remote.name for remote in repo.remotes]:
                github_repo_url = f"https://github.com/code-inspect-binder/osf_{project_id}.git"
                repo.create_remote("origin", github_repo_url)

            repo.git.add("runtime.txt")

            if repo.is_dirty():
                repo.index.commit("Add runtime.txt generated by container")
                repo.git.push("--set-upstream", "origin", "main")
                log_message(project_id, "CONTAINER RUN", "✅ runtime.txt committed and pushed to GitHub.")
            else:
                log_message(project_id, "CONTAINER RUN", "ℹ️ No changes to commit for runtime.txt.")
        except GitCommandError as e:
            log_message(project_id, "CONTAINER RUN", f"❌ Git error: {e}")
        except Exception as e:
            log_message(project_id, "CONTAINER RUN", f"❌ Failed to push runtime.txt to GitHub: {e}")
    else:
        log_message(project_id, "CONTAINER RUN", "⚠️ runtime.txt not found after container execution.")

    return True


def build_and_run(project_id, no_run=False, push=True, dockerhub_username=None):
    """Processes a project."""
    log_message(project_id, "CONTAINER BUILD", f"=== 🚀 Processing Project: '{project_id}' ===")

    if not check_docker_daemon(project_id):
        return False

    try:
        if not build_image(project_id, push=push, dockerhub_username=dockerhub_username):
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
    parser.add_argument("project_id", nargs="+", help="Single project ID or file containing multiple IDs")
    parser.add_argument("--no-run", action="store_true", help="Only build the image without running the container")

    args = parser.parse_args()

    if len(args.project_id) == 1 and os.path.isfile(args.project_id[0]):
        with open(args.project_id[0]) as f:
            project_ids = [line.strip() for line in f if line.strip()]
    else:
        project_ids = args.project_id

    for project_id in project_ids:
        build_and_run(project_id, no_run=args.no_run, push=True)
