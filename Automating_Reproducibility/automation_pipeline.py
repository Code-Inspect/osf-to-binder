import os
import sys
import subprocess
import requests
from git import Repo
import time
from utils import log_message


BASE_DIR = "/data/meet/pipeline"

def run_flowr_dependency_query(project_path):
    """Extract dependencies using flowr_dependency_query.py."""
    dependency_file = os.path.join(project_path, "dependencies.txt")
    print(f"Running flowr_dependency_query.py for {project_path}...")

    script_path = "/data/meet/pipeline/flowr_dependency_query.py"
    command = [
        "uv", "run", "python3", script_path,
        "--input-dir", project_path,
        "--output-file", dependency_file
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Dependencies extracted to {dependency_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error running flowr_dependency_query.py: {e}")
        return False

    return True

def download_file(file, download_path):
    file_path = os.path.join(download_path, file.name)
    print(f"Downloading file '{file.name}' to {file_path}...")
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    with open(file_path, 'wb') as f:
        file.write_to(f)
    print(f"Downloaded '{file.name}' successfully.")

def download_folder(folder, download_path):
    folder_path = os.path.join(download_path, folder.name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    print(f"Downloading folder '{folder.name}' to {folder_path}...")

    for file in folder.files:
        download_file(file, folder_path)

    for subfolder in folder.folders:
        download_folder(subfolder, folder_path)

import time
from osfclient.api import OSF
import requests

def download_project(project_id, download_directory):
    osf = OSF()

    # Attempt to fetch the project with retry logic for 429 errors
    retries = 3  # Number of times to retry
    wait_time = 20  # Wait time between retries

    for attempt in range(retries):
        try:
            project = osf.project(project_id)
            storage = project.storage('osfstorage')
            break  # Exit the loop if successful

        except requests.exceptions.HTTPError as e:
            # Handle HTTPError specifically
            if e.response.status_code == 429:
                print(f"🚨 Rate limit hit for project '{project_id}'. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)  # Wait before retrying
            else:
                print(f"❌ HTTP error for project '{project_id}': {e.response.status_code}")
                return None

        except Exception as e:
            # Catch any other exceptions
            print(f"❌ Unexpected error processing project '{project_id}': {e}")
            return None
    else:
        print(f"❌ Failed to download project '{project_id}' after {retries} attempts.")
        return None

    # Proceed if project is downloaded successfully
    project_path = os.path.join(download_directory, project_id)
    os.makedirs(project_path, exist_ok=True)

    print(f"📥 Starting download of all contents in project '{project_id}'...")
    for folder in storage.folders:
        download_folder(folder, project_path)
    for file in storage.files:
        download_file(file, project_path)

    print("✅ Project download completed.")
    return project_path

def create_github_repo(repo_name):
    token = "Write ypur Github token here"   #Make sure to give your Github accessibility token with required permissions.
    headers = {"Authorization": f"token {token}"}
    payload = {"name": repo_name, "private": False}
    response = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
    if response.status_code == 201:
        print(f"GitHub repository '{repo_name}' created successfully.")
    elif response.status_code == 422:  # Already exists
        print(f"GitHub repository '{repo_name}' already exists.")
    else:
        print(f"Failed to create GitHub repository: {response.json()}")
        sys.exit(1)

def create_repo2docker_files(project_dir, project_id):
    repo_name = f"osf_{project_id}"
    github_repo_url = f"https://github.com/Meet261/{repo_name}.git"

    # Create GitHub repository
    create_github_repo(repo_name)

    repo2docker_path = os.path.join(project_dir, "repo2docker")
    os.makedirs(repo2docker_path, exist_ok=True)

    # Move all project files into the repo2docker directory
    for file_name in os.listdir(project_dir):
        file_path = os.path.join(project_dir, file_name)
        if file_name != "repo2docker":
            os.rename(file_path, os.path.join(repo2docker_path, file_name))

    # Create dependencies.txt if not present
    dependencies_file = os.path.join(repo2docker_path, "dependencies.txt")
    if not os.path.exists(dependencies_file):
        print(f"No dependencies.txt found for {project_dir}. Skipping dependency handling.")
        return
    # Extract dependencies
    dependencies = []
    with open(dependencies_file, "r") as f:
        is_r_libraries_section = False
        for line in f:
            line = line.strip()
            if line.startswith("# R libraries"):
                is_r_libraries_section = True
                continue
            elif line.startswith("#") and is_r_libraries_section:
                break
            elif is_r_libraries_section and line:
                dependencies.append(line)

    # Create DESCRIPTION file
    description_path = os.path.join(repo2docker_path, "DESCRIPTION")
    with open(description_path, "w") as desc:
        desc.write("Package: repo2dockerProject\n")
        desc.write("Type: Package\n")
        desc.write("Title: Repo2Docker Project\n")
        desc.write("Version: 1.0\n")
        desc.write("Authors@R: c(person(\"Maintainer\", \"Example\", email = \"maintainer@example.com\", role = c(\"aut\", \"cre\")))\n")
        desc.write("Description: Automatically generated DESCRIPTION file for Repo2Docker.\n")
        desc.write("License: MIT\n")
        desc.write("Imports: ")
        for dep in dependencies:
            desc.write(f"{dep}, ")
        desc.write("\n")

    # Create postBuild file
    postbuild_path = os.path.join(repo2docker_path, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write("#!/bin/bash\n")
        postbuild.write("\n")
        postbuild.write("# Update system and install required libraries\n")
       # postbuild.write("apt-get update && apt-get install -y libglpk-dev libxml2-dev libssl-dev\n")
       # postbuild.write("\n")
        
        # Install R-remotes version 2.5.0
        postbuild.write("# Install R-remotes version 2.5.0\n")
        postbuild.write("R -e \"install.packages('remotes', repos = 'http://cran.us.r-project.org', type = 'source')\"\n")
        postbuild.write("R -e \"remotes::install_version('remotes', version = '2.5.0', repos = 'http://cran.us.r-project.org')\"\n")
        postbuild.write("\n")

        # Install FlowR
        postbuild.write("# Install FlowR\n")
        postbuild.write("R -e \"remotes::install_github('flowr-analysis/rstudio-addin-flowr')\"\n")

    os.chmod(postbuild_path, 0o755)

    # Create pyproject.toml
    pyproject_path = os.path.join(repo2docker_path, "pyproject.toml")
    with open(pyproject_path, "w") as pyproject:
        pyproject.write("[project]\n")
        pyproject.write(f'name = "osf_{project_id}"\n')
        pyproject.write("version = \"0.1.0\"\n")
        pyproject.write("description = \"Repo2Docker project for OSF\"\n")
        pyproject.write("readme = \"README.md\"\n")
        pyproject.write("requires-python = \">=3.12\"\n")
        pyproject.write("\n[dependencies]\n")
        pyproject.write("gitpython = \">=3.1.30\"\n")

    # Create README.md with a container start button
    readme_path = os.path.join(repo2docker_path, "README.md")
    with open(readme_path, "w") as readme:
        readme.write(f"# {repo_name}\n")
        readme.write("This repository was automatically generated for use with repo2docker.\n\n")
        readme.write("## How to Launch\n")
        readme.write(f"[![Binder](https://mybinder.org/badge_logo.svg)](https://notebooks.gesis.org/binder/v2/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n")
        readme.write("## Start Container Locally\n")
        readme.write("To start the container locally:\n\n")
        readme.write("```bash\n")
        readme.write(f"docker run -p 8888:8888 --name {repo_name} -d {repo_name}\n")
        readme.write("```\n")

    # Initialize Git repository and push to GitHub
    print(f"Initializing Git repository for {repo2docker_path}...")
    repo = Repo.init(repo2docker_path)
    if "origin" not in [remote.name for remote in repo.remotes]:
        repo.create_remote("origin", github_repo_url)

    try:
        repo.git.add(all=True)
        repo.index.commit("Initial commit for repo2docker project")
        repo.git.checkout("-B", "main")
        repo.remotes.origin.push(refspec="main:main", force=True)
        print(f"Repo2docker files created and pushed to {github_repo_url}.")
    except Exception as e:
        print(f"Error pushing to GitHub: {e}")
        sys.exit(1)

def process_project(project_id):
    try:
        log_message(project_id, "PROJECT INIT", f"🚀 Starting processing for project '{project_id}'")

        project_path = download_project(project_id, BASE_DIR)
        log_message(project_id, "DOWNLOAD", "✅ Project downloaded successfully.")

        run_flowr_dependency_query(project_path)
        log_message(project_id, "DEPENDENCY EXTRACTION", "✅ Dependencies extracted successfully.")

        create_repo2docker_files(project_path, project_id)
        log_message(project_id, "REPO2DOCKER SETUP", "✅ Repo2Docker files created successfully.")

    except Exception as e:
        log_message(project_id, "ERROR", f"❌ Error occurred: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 automation_pipeline.py <OSF_PROJECT_ID> [<OSF_PROJECT_ID> ...] or <project_ids.txt>")
        sys.exit(1)

    project_ids = []

    # Check if input is a file with project IDs
    if os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as file:
            project_ids = [line.strip() for line in file if line.strip()]
    else:
        project_ids = sys.argv[1:]

    for project_id in project_ids:
        print(f"\nProcessing project: {project_id}")
        process_project(project_id)

if __name__ == "__main__":
    main()
