import os
import sys
import subprocess
import requests
from git import Repo
import time
import shutil
from osfclient.api import OSF
from utils import log_message, BASE_DIR
import zipfile
import os
import subprocess
import glob

def run_flowr_dependency_query(project_path):
    """Extract dependencies using flowr_dependency_query.py if R or Rmd scripts exist."""
    dependency_file = os.path.join(project_path, "dependencies.txt")
    project_id = os.path.basename(project_path).replace("_repo", "")
    src_path = os.path.join(project_path, f"{project_id}_src")

    # 🔍 Check if any R/r/Rmd/rmd scripts exist in the project folder
    r_scripts = glob.glob(os.path.join(src_path, "**", "*.R"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.r"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.Rmd"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.rmd"), recursive=True)

    if not r_scripts:
        print(f"❌ No R or Rmd scripts found in {src_path}. Skipping dependency extraction.")
        
        # If a dependency file was created before, remove it
        if os.path.exists(dependency_file):
            os.remove(dependency_file)
            print(f"🗑️ Deleted '{dependency_file}' as no R or Rmd scripts were found.")
        
        log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ No R or Rmd scripts found. Dependency extraction skipped.")
        return False

    print(f"📦 Running flowr_dependency_query.py for {src_path}...")

    script_path = f"{BASE_DIR}/flowr_dependency_query.py"
    command = [
        "uv", "run", "python3", script_path,
        "--input-dir", src_path,
        "--output-file", dependency_file
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ Dependencies extracted to {dependency_file}")
        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running flowr_dependency_query.py: {e}")
        log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ Failed to extract dependencies: {e}")
        return False

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
    project_id_clean = project_id.replace("_repo", "")  # Ensure project_id is clean
    src_path = os.path.join(project_path, f"{project_id_clean}_src")

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
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        print(f"📦 Extracting {zip_file} to {src_path}...")
        zip_ref.extractall(src_path)
    
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
    """
    Creates necessary repo2docker files in the project_dir.
    Skips creating DESCRIPTION if it already exists.
    """

    repo_name = f"osf_{project_id}"
    # Files go directly in the project_dir (which is now {project_id}_repo)
    dependencies_file = os.path.join(project_dir, "dependencies.txt")  # Now outside repo2docker

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
 
     # delete the dependencies.txt file
    os.remove(dependencies_file)

    # Create postBuild file directly in project_dir
    postbuild_path = os.path.join(project_dir, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write("#!/bin/bash\n\n")
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

def process_project(project_id):
    """Processes a project while logging execution times."""
    try:
        log_message(project_id, "PROJECT INIT", f"🚀 Starting processing for project '{project_id}'")

        start_time = time.time()

        # Step 1: Download/Unzip Project
        project_download_start = time.time()
        project_path = unzip_project(project_id, BASE_DIR)
        # project_path = download_project(project_id, BASE_DIR)

        if project_path:
            project_download_end = time.time()
            log_message(project_id, "DOWNLOAD", f"✅ Project downloaded and unzipped successfully in {project_download_end - project_download_start:.2f} seconds.")
        else:
            log_message(project_id, "DOWNLOAD", f"❌ Failed to download/unzip project '{project_id}'. Skipping further processing.")
            return  # ❌ Abort if download/unzip fails

        # Step 2: Dependency Extraction
        dep_extraction_start = time.time()
        dependency_success = run_flowr_dependency_query(project_path)
        dep_extraction_end = time.time()

        if not dependency_success:
            log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ Failed to extract dependencies for project '{project_id}'. Skipping container setup.")
            return  # ❌ Abort if dependency extraction fails

        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted successfully in {dep_extraction_end - dep_extraction_start:.2f} seconds.")

        # Step 3: Container Setup (Only runs if dependency extraction was successful)
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
