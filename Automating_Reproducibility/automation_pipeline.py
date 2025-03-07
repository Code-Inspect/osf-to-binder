import os
import sys
import subprocess
import requests
from git import Repo
import time
from osfclient.api import OSF
from utils import log_message, BASE_DIR
import zipfile
def run_flowr_dependency_query(project_path):
    """Extract dependencies using flowr_dependency_query.py."""
    dependency_file = os.path.join(project_path, "dependencies.txt")
    project_id = os.path.basename(project_path).replace("_repo", "")
    src_path = os.path.join(project_path, f"{project_id}_src")
    
    print(f"Running flowr_dependency_query.py for {src_path}...")

    script_path = f"{BASE_DIR}/flowr_dependency_query.py"
    command = [
        "uv", "run", "python3", script_path,
        "--input-dir", src_path,
        "--output-file", dependency_file
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Dependencies extracted to {dependency_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error running flowr_dependency_query.py: {e}")
        return False

    return True

def download_file(file, base_path, sub_path):
    """Downloads a file while preserving its directory structure inside '{project_id}_src'."""
    file_path = os.path.join(base_path, f"{os.path.basename(base_path)}_src", sub_path, file.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Create necessary directories

    print(f"📥 Downloading '{file.name}' to {file_path}...")
    with open(file_path, 'wb') as f:
        file.write_to(f)
    print(f"✅ Downloaded '{file.name}' successfully.")

def download_folder(folder, base_path, sub_path=""):
    """Recursively downloads a folder and maintains directory structure inside '{project_id}_src'."""
    folder_path = os.path.join(base_path, f"{os.path.basename(base_path)}_src", sub_path, folder.name)
    os.makedirs(folder_path, exist_ok=True)  # Ensure the folder structure is created

    print(f"📁 Downloading folder '{folder.name}' to {folder_path}...")

    for file in folder.files:
        download_file(file, base_path, os.path.join(sub_path, folder.name))

    for subfolder in folder.folders:
        download_folder(subfolder, base_path, os.path.join(sub_path, folder.name))

def download_project(project_id, download_directory):
    """
    Downloads an OSF project, preserving directory structure inside '{project_id}_src'.
    Skips downloading if the project already exists.
    """
    project_path = os.path.join(download_directory, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")

    # **Skip download if the project already exists**
    if os.path.exists(src_path):
        print(f"⏭️ Project '{project_id}' already exists at {src_path}. Skipping download.")
        return project_path  # Return the existing path

    osf = OSF()

    # Retry logic for rate limits
    retries = 3
    wait_time = 20

    for attempt in range(retries):
        try:
            project = osf.project(project_id)
            storage = project.storage('osfstorage')
            break  # Exit loop if successful
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"🚨 Rate limit hit for project '{project_id}'. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ HTTP error for project '{project_id}': {e.response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Unexpected error processing project '{project_id}': {e}")
            return None
    else:
        print(f"❌ Failed to download project '{project_id}' after {retries} attempts.")
        return None

    # Create project folder structure
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(src_path, exist_ok=True)

    print(f"📥 Starting download of all contents in project '{project_id}'...")

    for folder in storage.folders:
        download_folder(folder, project_path)

    #for file in storage.files:
    #    download_file(file, project_path, "")

    print("✅ Project download completed.")
    return project_path


def unzip_project(project_id, download_directory):
    """Unzips a project from the download directory to the base directory with new folder structure."""
    zip_file = os.path.join("downloads", f"{project_id}.zip")
    project_path = os.path.join(download_directory, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")

    # **Skip download if the project already exists**
    if os.path.exists(src_path) and os.listdir(src_path):  # Check if directory exists AND is not empty
        print(f"⏭️ Project '{project_id}' already exists at {src_path}. Skipping download.")
        return project_path  # Return the existing path
    
    # Check if zip file exists
    if not os.path.exists(zip_file):
        print(f"❌ Error: Zip file for project '{project_id}' not found at '{zip_file}'")
        # Fall back to OSF download if zip doesn't exist
        return download_project(project_id, download_directory)
    
    # Create project folder structure
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(src_path, exist_ok=True)
    
    # Extract to a temporary location first
    temp_extract_path = os.path.join(download_directory, f"temp_{project_id}")
    os.makedirs(temp_extract_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            print(f"📦 Extracting {zip_file} to {temp_extract_path}...")
            zip_ref.extractall(temp_extract_path)
        
        # Move contents from repo2docker folder to src folder
        temp_repo2docker_path = os.path.join(temp_extract_path, project_id, "repo2docker")
        
        # Check if the expected path exists
        if os.path.exists(temp_repo2docker_path):
            # Use subprocess for better handling of directory contents copying
            print(f"📂 Moving contents from {temp_repo2docker_path} to {src_path}...")
            subprocess.run(["cp", "-r", f"{temp_repo2docker_path}/.", src_path], check=True)
            print(f"✅ Moved contents to {src_path}")
        else:
            # Try to find any content in the extracted folder
            print(f"⚠️ Expected path {temp_repo2docker_path} not found. Searching for content...")
            
            # List all directories in the temp folder to help debug
            print(f"📂 Contents of {temp_extract_path}:")
            for root, dirs, files in os.walk(temp_extract_path):
                print(f"  Directory: {root}")
                for d in dirs:
                    print(f"    Subdir: {d}")
                for f in files:
                    print(f"    File: {f}")
            
            # Try to find any content and move it
            found_content = False
            for root, dirs, files in os.walk(temp_extract_path):
                if files:  # If we find any files
                    print(f"📂 Found files in {root}, moving to {src_path}...")
                    subprocess.run(["cp", "-r", f"{root}/.", src_path], check=True)
                    found_content = True
                    break
            
            if not found_content:
                print(f"❌ No content found in extracted zip for project '{project_id}'")
                # Fall back to OSF download
                return download_project(project_id, download_directory)
    except Exception as e:
        print(f"❌ Error extracting zip file: {e}")
        # Fall back to OSF download
        return download_project(project_id, download_directory)
    finally:
        # Clean up temporary directory
        subprocess.run(["rm", "-rf", temp_extract_path])
    
    # Verify the src directory has content
    if os.path.exists(src_path) and not os.listdir(src_path):
        print(f"⚠️ Source directory {src_path} is empty after extraction. Falling back to OSF download.")
        return download_project(project_id, download_directory)
    
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

def create_repo2docker_files(project_dir, project_id, add_github_repo=False):
    """Creates necessary repo2docker files in the parent folder."""

    repo_name = f"osf_{project_id}"
    # Files go directly in the project_dir (which is now {project_id}_repo)
    dependencies_file = os.path.join(project_dir, "dependencies.txt")  # Now outside repo2docker

    # Ensure the dependencies.txt is in the correct location
    if not os.path.exists(dependencies_file):
        print(f"⚠️ No dependencies.txt found in {project_dir}. Skipping dependency handling.")
        return

    print(f"✅ dependencies.txt found at {dependencies_file}. Proceeding with repo2docker setup.")
    
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

    # Create DESCRIPTION file directly in project_dir
    description_path = os.path.join(project_dir, "DESCRIPTION")
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

    # Create postBuild file directly in project_dir
    postbuild_path = os.path.join(project_dir, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write("#!/bin/bash\n")
        postbuild.write("\n")
        postbuild.write("# Update system and install required libraries\n")
        
        # Install R-remotes version 2.5.0
        postbuild.write("# Install R-remotes version 2.5.0\n")
        postbuild.write("R -e \"install.packages('remotes', repos = 'http://cran.us.r-project.org', type = 'source')\"\n")
        postbuild.write("R -e \"remotes::install_version('remotes', version = '2.5.0', repos = 'http://cran.us.r-project.org')\"\n")
        postbuild.write("\n")

        # Install FlowR
        postbuild.write("# Install FlowR\n")
        postbuild.write("R -e \"remotes::install_github('flowr-analysis/rstudio-addin-flowr')\"\n")

    os.chmod(postbuild_path, 0o755)

    # Create pyproject.toml directly in project_dir
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    with open(pyproject_path, "w") as pyproject:
        pyproject.write("[project]\n")
        pyproject.write(f'name = "osf_{project_id}"\n')
        pyproject.write("version = \"0.1.0\"\n")
        pyproject.write("description = \"Repo2Docker project for OSF\"\n")
        pyproject.write("readme = \"README.md\"\n")
        pyproject.write("requires-python = \">=3.12\"\n")
        pyproject.write("\n[dependencies]\n")
        pyproject.write("gitpython = \">=3.1.30\"\n")

    # Create README.md with a container start button directly in project_dir
    readme_path = os.path.join(project_dir, "README.md")
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

    if add_github_repo:
        # Initialize Git repository and push to GitHub
        github_repo_url = f"https://github.com/Meet261/{repo_name}.git"

        # Create GitHub repository
        create_github_repo(repo_name)

        print(f"Initializing Git repository for {project_dir}...")
        repo = Repo.init(project_dir)
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

import time

def process_project(project_id):
    """Processes a project while logging execution times."""
    try:
        log_message(project_id, "PROJECT INIT", f"🚀 Starting processing for project '{project_id}'")

        start_time = time.time()

        # Step 1: Download Project
        project_download_start = time.time()
        # project_path = download_project(project_id, BASE_DIR)
        project_path = unzip_project(project_id, BASE_DIR)
        project_download_end = time.time()

        log_message(project_id, "DOWNLOAD", f"✅ Project downloaded successfully in {project_download_end - project_download_start:.2f} seconds.")

        # Step 2: Dependency Extraction
        dep_extraction_start = time.time()
        run_flowr_dependency_query(project_path)
        dep_extraction_end = time.time()

        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted successfully in {dep_extraction_end - dep_extraction_start:.2f} seconds.")

        # Step 3: Container Setup
        container_setup_start = time.time()
        create_repo2docker_files(project_path, project_id)
        container_setup_end = time.time()

        log_message(project_id, "REPO2DOCKER SETUP", f"✅ Repo2Docker files created successfully in {container_setup_end - container_setup_start:.2f} seconds.")

        total_time = time.time() - start_time
        log_message(project_id, "TOTAL TIME", f"⏳ Total time from download to container setup: {total_time:.2f} seconds.")

    except Exception as e:
        log_message(project_id, "ERROR", f"❌ Error occurred: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 automation_pipeline.py <OSF_PROJECT_ID> [<OSF_PROJECT_ID> ...] or <project_ids.txt>")
        sys.exit(1)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    print(f"Logs will be written to: {logs_dir}")

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
