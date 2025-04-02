import os
import subprocess
import sys
import argparse
from utils import log_message, LOGS_DIR, get_project_path

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
    
def parse_installed_versions(log_file_path):
    packages = {}
    with open(log_file_path, "r") as f:
        for line in f:
            if "==" in line:
                pkg, version = line.strip().split("==")
                packages[pkg.strip()] = version.strip()
    return packages

def update_description_with_versions(project_id, version_dict):
    """Cleanly replaces the Imports section in DESCRIPTION with versioned packages."""
    description_path = os.path.join(get_project_path(project_id), "DESCRIPTION")
    if not os.path.exists(description_path):
        log_message(project_id, "VERSION UPDATE", f"⚠️ DESCRIPTION file not found at {description_path}")
        return

    with open(description_path, "r") as f:
        lines = f.readlines()

    updated_lines = []
    in_imports = False
    imports_buffer = []

    for line in lines:
        stripped = line.strip()

        # Start of Imports (one-line or multi-line)
        if stripped.startswith("Imports:"):
            in_imports = True

            # Handle one-line imports
            inline_imports = stripped.replace("Imports:", "").strip()
            if inline_imports:
                imports_buffer = [pkg.strip().rstrip(",") for pkg in inline_imports.split(",") if pkg.strip()]
            continue

        # Inside a multi-line Imports block
        elif in_imports:
            if stripped == "" or not stripped[0].isalpha():
                in_imports = False
                continue
            imports_buffer.append(stripped.rstrip(","))
            continue

        updated_lines.append(line)

    # Create the cleaned Imports section with versions
    if imports_buffer:
        updated_lines.append("Imports:\n")
        for pkg in imports_buffer:
            version = version_dict.get(pkg)
            if version:
                updated_lines.append(f"    {pkg} (== {version}),\n")
            else:
                updated_lines.append(f"    {pkg},\n")
        # Remove trailing comma
        if updated_lines[-1].strip().endswith(","):
            updated_lines[-1] = updated_lines[-1].rstrip(",\n") + "\n"

    with open(description_path, "w") as f:
        f.writelines(updated_lines)

    log_message(project_id, "VERSION UPDATE", f"✅ Cleaned and updated Imports section in: {description_path}")

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
    """Runs the container for the project, logs R package versions, and updates DESCRIPTION."""
    log_message(project_id, "CONTAINER RUN", f"=== Running container for project: {project_id} ===")

    project_path = check_project_exists(project_id)
    if not project_path:
        return False

    image_name, container_name = get_image_and_container_name(project_id)

    # Remove any existing container
    try:
        subprocess.run(["docker", "rm", "-f", container_name], check=True)
        log_message(project_id, "CONTAINER RUN", f"🗑️ Removed existing container '{container_name}'.")
    except subprocess.CalledProcessError:
        log_message(project_id, "CONTAINER RUN", f"ℹ️ No existing container '{container_name}' found to remove.")

    # Run container in detached mode
    run_command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-v", f"{os.path.abspath(project_path)}:/data",
        image_name
    ]

    try:
        subprocess.run(run_command, check=True)
        log_message(project_id, "CONTAINER RUN", f"✅ Container '{container_name}' started successfully.")
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER RUN", f"❌ Failed to start container: {e.returncode}")
        log_message(project_id, "CONTAINER RUN", f"{' '.join(e.cmd)}")
        return False

    # Paths for logging
    host_log_path = os.path.join(LOGS_DIR, f"{project_id}_package_versions.log")
    container_log_path = "/tmp/pkg_versions.log"
    container_r_script_path = "/tmp/log_versions.R"
    local_r_script_path = os.path.join(LOGS_DIR, f"{project_id}_log_versions.R")

    # Create R script to log installed packages
    r_script = f"""
sink('{container_log_path}')
ip <- installed.packages()
cat("Installed R Package Versions:\\n\\n")
for (pkg in rownames(ip)) {{
  cat(sprintf('%s == %s\\n', pkg, ip[pkg, 'Version']))
}}
sink()
"""
    with open(local_r_script_path, "w") as f:
        f.write(r_script)

    try:
        # Copy R script into the container
        subprocess.run(["docker", "cp", local_r_script_path, f"{container_name}:{container_r_script_path}"], check=True)

        # Run the R script inside the container
        subprocess.run(["docker", "exec", container_name, "Rscript", container_r_script_path], check=True)

        # Copy the version log file back to host
        subprocess.run(["docker", "cp", f"{container_name}:{container_log_path}", host_log_path], check=True)

        log_message(project_id, "CONTAINER RUN", f"📦 Retrieved package log from container to: {host_log_path}")
        os.remove(local_r_script_path)
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER RUN", f"⚠️ Failed to retrieve package versions: {e}")
        return False

    # Update DESCRIPTION file using parsed version log
    if os.path.exists(host_log_path):
        version_dict = parse_installed_versions(host_log_path)
        update_description_with_versions(project_id, version_dict)

    return True

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
