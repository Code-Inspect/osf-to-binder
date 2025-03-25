#!/usr/bin/env python3

import os
import sys
import subprocess
import requests
from git import Repo
import time
import shutil
from osfclient.api import OSF
import zipfile
import glob
import logging
from datetime import datetime
import argparse

# Base directory
BASE_DIR = "Automating_Reproducibility"

# Global dictionary to store loggers
project_loggers = {}
project_execution_loggers = {}

def setup_logging(project_id, execution_log=False):
    """Set up logging for a specific project using a single log file."""
    # Return existing logger if already set up
    logger_dict = project_execution_loggers if execution_log else project_loggers
    if project_id in logger_dict:
        return logger_dict[project_id]

    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log file based on type
    log_file = os.path.join(logs_dir, f"{project_id}{'_execution' if execution_log else ''}.log")
    
    # Create a new logger for this project
    logger = logging.getLogger(f"{project_id}{'_execution' if execution_log else ''}")
    logger.setLevel(logging.INFO)
    
    # Only add handlers if they haven't been added yet
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler (only for non-execution logs)
        if not execution_log:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
        
        # Create formatters and add them to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        if not execution_log:
            console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        if not execution_log:
            logger.addHandler(console_handler)
    
    # Store the logger in our global dictionary
    logger_dict[project_id] = logger
    return logger

def log_message(project_id, stage, message, execution_log=False):
    """Log a message for a specific project and stage."""
    logger = setup_logging(project_id, execution_log)
    logger.info(f"[{stage}] {message}")

def run_flowr_dependency_query(project_path):
    """Extract dependencies using flowr_dependency_query.py if R or Rmd scripts exist."""
    dependency_file = os.path.join(project_path, "dependencies.txt")
    project_id = os.path.basename(project_path).replace("_repo", "")
    src_path = os.path.join(project_path, f"{project_id}_src")

    r_scripts = glob.glob(os.path.join(src_path, "**", "*.R"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.r"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.Rmd"), recursive=True) + \
                glob.glob(os.path.join(src_path, "**", "*.rmd"), recursive=True)

    if not r_scripts:
        log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ No R or Rmd scripts found in {src_path}. Skipping dependency extraction.")
        if os.path.exists(dependency_file):
            os.remove(dependency_file)
            log_message(project_id, "DEPENDENCY EXTRACTION", f"🗑️ Deleted '{dependency_file}' as no R or Rmd scripts were found.")
        return False

    log_message(project_id, "DEPENDENCY EXTRACTION", f"📦 Running flowr_dependency_query.py for {src_path}...")

    script_path = os.path.join(BASE_DIR, "flowr_dependency_query.py")
    command = [
        "uv", "run", "python3", script_path,
        "--input-dir", src_path,
        "--output-file", dependency_file
    ]

    try:
        subprocess.run(command, check=True)
        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted to {dependency_file}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ Failed to extract dependencies: {e}")
        return False

def download_file(file, base_path, project_id, sub_path):
    """Downloads a file while preserving its directory structure."""
    file_path = os.path.join(base_path, f"{project_id}_src", sub_path, file.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    log_message(project_id, "DOWNLOAD", f"📥 Downloading '{file.name}' to {file_path}...")
    with open(file_path, 'wb') as f:
        file.write_to(f)
    log_message(project_id, "DOWNLOAD", f"✅ Downloaded '{file.name}' successfully.")

def download_folder(folder, base_path, project_id, sub_path=""):
    """Recursively downloads a folder and maintains directory structure."""
    folder_path = os.path.join(base_path, f"{project_id}_src", sub_path, folder.name)
    os.makedirs(folder_path, exist_ok=True)

    log_message(project_id, "DOWNLOAD", f"📁 Downloading folder '{folder.name}' to {folder_path}...")

    for file in folder.files:
        download_file(file, base_path, project_id, os.path.join(sub_path, folder.name))

    for subfolder in folder.folders:
        download_folder(subfolder, base_path, project_id, os.path.join(sub_path, folder.name))

def download_project(project_id, download_directory):
    """Downloads an OSF project, preserving directory structure."""
    project_path = os.path.join(download_directory, f"{project_id}_repo")
    project_id_clean = project_id.replace("_repo", "")
    src_path = os.path.join(project_path, f"{project_id_clean}_src")

    if os.path.exists(src_path):
        log_message(project_id, "DOWNLOAD", f"⏭️ Project '{project_id}' already exists at {src_path}. Skipping download.")
        return project_path

    osf = OSF()
    retries = 3
    wait_time = 20

    for attempt in range(retries):
        try:
            project = osf.project(project_id)
            storage = project.storage('osfstorage')
            break
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                log_message(project_id, "DOWNLOAD", f"🚨 Rate limit hit. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                log_message(project_id, "DOWNLOAD", f"❌ HTTP error: {e.response.status_code}")
                return None
        except Exception as e:
            log_message(project_id, "DOWNLOAD", f"❌ Unexpected error: {e}")
            return None
    else:
        log_message(project_id, "DOWNLOAD", f"❌ Failed to download project after {retries} attempts.")
        return None

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(src_path, exist_ok=True)

    log_message(project_id, "DOWNLOAD", f"📥 Starting download of all contents in project '{project_id}'...")

    for folder in storage.folders:
        download_folder(folder, project_path, project_id_clean)

    log_message(project_id, "DOWNLOAD", "✅ Project download completed.")
    return project_path

def unzip_project(project_id, download_directory):
    """Unzips a project from the download directory."""
    zip_file = os.path.join("downloads", f"{project_id}.zip")
    project_path = os.path.join(download_directory, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")

    if os.path.exists(src_path) and os.listdir(src_path):
        log_message(project_id, "DOWNLOAD", f"⏭️ Project '{project_id}' already exists at {src_path}. Skipping download.")
        return project_path
    
    if not os.path.exists(zip_file):
        log_message(project_id, "DOWNLOAD", f"❌ Zip file not found at '{zip_file}'. Falling back to OSF download.")
        return download_project(project_id, download_directory)
    
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(src_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        log_message(project_id, "DOWNLOAD", f"📦 Extracting {zip_file} to {src_path}...")
        zip_ref.extractall(src_path)
    
    return project_path

def create_github_repo(repo_name):
    """Creates a GitHub repository."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        log_message(repo_name, "GITHUB", "❌ GitHub access token not found in environment variables.")
        return False

    headers = {"Authorization": f"token {token}"}
    payload = {"name": repo_name, "private": False}
    response = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
    
    if response.status_code == 201:
        log_message(repo_name, "GITHUB", f"✅ GitHub repository '{repo_name}' created successfully.")
        return True
    elif response.status_code == 422:
        log_message(repo_name, "GITHUB", f"ℹ️ GitHub repository '{repo_name}' already exists.")
        return True
    else:
        log_message(repo_name, "GITHUB", f"❌ Failed to create GitHub repository: {response.json()}")
        return False

def create_repo2docker_files(project_dir, project_id, add_github_repo=False):
    """Creates necessary repo2docker files in the project directory."""
    repo_name = f"osf_{project_id}"
    dependencies_file = os.path.join(project_dir, "dependencies.txt")

    if not os.path.exists(dependencies_file):
        log_message(project_id, "REPO2DOCKER", f"⚠️ No dependencies.txt found in {project_dir}. Skipping dependency handling.")
        return False
    
    log_message(project_id, "REPO2DOCKER", f"✅ dependencies.txt found at {dependencies_file}. Proceeding with repo2docker setup.")
     
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
 
    os.remove(dependencies_file)

    postbuild_path = os.path.join(project_dir, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write("#!/bin/bash\n\n")
        postbuild.write("# Update system and install required libraries\n")
        postbuild.write("# Install R-remotes version 2.5.0\n")
        postbuild.write("R -e \"install.packages('remotes', repos = 'http://cran.us.r-project.org', type = 'source')\"\n")
        postbuild.write("R -e \"remotes::install_version('remotes', version = '2.5.0', repos = 'http://cran.us.r-project.org')\"\n")
        postbuild.write("\n")
        postbuild.write("# Install FlowR\n")
        postbuild.write("R -e \"remotes::install_github('flowr-analysis/rstudio-addin-flowr')\"\n")

    os.chmod(postbuild_path, 0o755)

    osf = OSF()
    try:
        project = osf.project(project_id)
        project_title = project.title
        project_description = project.description or "No description provided."
    except Exception as e:
        log_message(project_id, "REPO2DOCKER", f"⚠️ Error fetching project details from OSF: {e}. Using default README content.")
        project_title = repo_name
        project_description = "This repository was automatically generated for use with repo2docker."

    readme_path = os.path.join(project_dir, "README.md")
    with open(readme_path, "w") as readme:
        readme.write(f"# Automated reproducibility test for the OSF project, {project_id}\n\n")
        readme.write("--- \n")
        readme.write(f"## OSF Project metadata: \n")
        readme.write(f"{project_title}\n\n")
        readme.write(f"{project_description}\n\n")
        readme.write("--- \n")
        readme.write(
            f"This repository was auto-generated as part of testing reproducibility of open science projects hosted on OSF. Original OSF page: [https://osf.io/{project_id}/](https://osf.io/{project_id}/)\n\n")
        readme.write(f"The contents of the folder {project_id}_src was cloned from the OSF project on 12-03-2025. The files, DESCRIPTION and postBuild has been added automatically inorder to make this project Binder ready.\n\n")
        readme.write("## How to Launch\n")
        readme.write(
            f"🚀 **Click below to launch the project on MyBinder:**  \n[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n")
        readme.write(
            f"🚀 **Click below to launch the project on the NFDI JupyterHub:**  \n[![NFDI](https://nfdi-jupyter.de/images/nfdi_badge.svg)](https://hub.nfdi-jupyter.de/r2d/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n")
        readme.write("## Start Container Locally\n")
        readme.write("To start the container locally:\n\n")
        readme.write("```bash\n")
        readme.write(f"docker run -p 8888:8888 --name {repo_name}-test -d {repo_name}-test\n")
        readme.write("```\n\n")
        readme.write(
            "This repository demonstrates how a project from OSF can be containerized and tested using Binder. We facilitate a one-click launch of the OSF project, allowing anyone to browse, execute the code, and verify or compare the results from the associated research paper. This aligns with the objectives of the **CodeInspector project**, where we aim to enable **browser-based reproducibility and evaluation of open science projects**.\n\n")
        readme.write(
            "By integrating **OSF** and **Binder**, we aim to enhance transparency and reproducibility in computational social science and beyond. This repository serves as an example of how research projects can be packaged and shared in a fully executable, browser-based environment.\n\n")
        readme.write("--- \n\n")
        readme.write("This work was funded by the German Research Foundation (DFG) under project No. 504226141.")

    if add_github_repo:
        if not create_github_repo(repo_name):
            return False

        github_repo_url = f"https://github.com/Meet261/{repo_name}.git"
        log_message(project_id, "GITHUB", f"Initializing Git repository for {project_dir}...")
        
        try:
            repo = Repo.init(project_dir)
            if "origin" not in [remote.name for remote in repo.remotes]:
                repo.create_remote("origin", github_repo_url)

            repo.git.add(all=True)
            repo.index.commit("Initial commit for repo2docker project")
            repo.git.checkout("-B", "main")
            repo.remotes.origin.push(refspec="main:main", force=True)
            log_message(project_id, "GITHUB", f"✅ Repo2docker files created and pushed to {github_repo_url}.")
            return True
        except Exception as e:
            log_message(project_id, "GITHUB", f"❌ Error pushing to GitHub: {e}")
            return False

    return True

def build_repository(project_id):
    """Builds the repository using repo2docker."""
    log_message(project_id, "BUILD", f"=== Building repository for project: {project_id} ===")
    try:
        subprocess.run(["python3", os.path.join(BASE_DIR, "run_code_in_container.py"), "--project-id", project_id, "--repo-only"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "BUILD", f"❌ Failed to build repository: {e}")
        return False

def run_container(project_id):
    """Runs the container for the project."""
    log_message(project_id, "CONTAINER", f"=== Running container for project: {project_id} ===")
    try:
        subprocess.run(["python3", os.path.join(BASE_DIR, "run_code_in_container.py"), "--project-id", project_id, "--build-and-run"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "CONTAINER", f"❌ Failed to run container: {e}")
        return False

def execute_r_scripts(project_id):
    """Executes R scripts in the container."""
    log_message(project_id, "R_EXECUTION", f"Executing R scripts in the container for project ID: {project_id}")
    try:
        subprocess.run(["python3", os.path.join(BASE_DIR, "execute_r_files_in_container.py"), project_id], check=True)
        return True
    except subprocess.CalledProcessError as e:
        log_message(project_id, "R_EXECUTION", f"❌ Failed to execute R scripts: {e}")
        return False

def process_project(project_id):
    """Processes a project with all necessary steps."""
    start_time = time.time()
    log_message(project_id, "PROJECT INIT", f"🚀 Starting processing for project '{project_id}'")

    try:
        # Step 1: Download/Unzip Project
        project_download_start = time.time()
        project_path = unzip_project(project_id, BASE_DIR)

        if not project_path:
            log_message(project_id, "DOWNLOAD", f"❌ Failed to download/unzip project '{project_id}'. Skipping further processing.")
            return False

        project_download_end = time.time()
        log_message(project_id, "DOWNLOAD", f"✅ Project downloaded and unzipped successfully in {project_download_end - project_download_start:.2f} seconds.")

        # Step 2: Dependency Extraction
        dep_extraction_start = time.time()
        if not run_flowr_dependency_query(project_path):
            log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ Failed to extract dependencies for project '{project_id}'. Skipping container setup.")
            return False

        dep_extraction_end = time.time()
        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted successfully in {dep_extraction_end - dep_extraction_start:.2f} seconds.")

        # Step 3: Container Setup
        container_setup_start = time.time()
        if not create_repo2docker_files(project_path, project_id):
            log_message(project_id, "REPO2DOCKER SETUP", f"❌ Failed to create repo2docker files for project '{project_id}'.")
            return False

        container_setup_end = time.time()
        log_message(project_id, "REPO2DOCKER SETUP", f"✅ Repo2Docker files created successfully in {container_setup_end - container_setup_start:.2f} seconds.")

        # Step 4: Build Repository
        if not build_repository(project_id):
            return False

        # Step 5: Run Container
        if not run_container(project_id):
            return False

        # Step 6: Execute R Scripts
        if not execute_r_scripts(project_id):
            return False

        total_time = time.time() - start_time
        log_message(project_id, "TOTAL TIME", f"⏳ Total processing time: {total_time:.2f} seconds.")
        return True

    except Exception as e:
        log_message(project_id, "ERROR", f"❌ Error occurred: {e}")
        return False

def setup_environment():
    """Sets up the Python environment using uv."""
    print("Setting up the environment using uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to sync environment using uv: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Process OSF projects for reproducibility testing.')
    parser.add_argument('input', help='OSF project ID or file containing project IDs')
    parser.add_argument('--github', action='store_true', help='Create GitHub repositories for the projects')
    args = parser.parse_args()

    if not setup_environment():
        sys.exit(1)

    project_ids = []
    if os.path.isfile(args.input):
        with open(args.input, "r") as file:
            project_ids = [line.strip() for line in file if line.strip()]
    else:
        project_ids = [args.input]

    success_count = 0
    for project_id in project_ids:
        if process_project(project_id):
            success_count += 1

    # Log summary to each project's log file
    for project_id in project_ids:
        log_message(project_id, "SUMMARY", f"Processed {len(project_ids)} projects. {success_count} successful, {len(project_ids) - success_count} failed.")

if __name__ == "__main__":
    main() 