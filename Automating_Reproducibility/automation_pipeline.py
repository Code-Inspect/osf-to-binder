#!/usr/bin/env python3

import os
import sys
import subprocess
from osfclient.api import OSF

BASE_DIR = "/data/meet/pipeline"

POSTBUILD_CONTENT = """#!/bin/bash

# Install remotes package in R
R -e "if (!requireNamespace('remotes', quietly = TRUE)) install.packages('remotes', repos = 'http://cran.us.r-project.org')"

# Install FlowR from GitHub using remotes
R -e "remotes::install_github('flowr-analysis/rstudio-addin-flowr')"

# Install additional R packages not covered in `environment.yml`
Rscript -e "if (!requireNamespace('qgraph', quietly = TRUE)) install.packages('qgraph', repos = 'http://cran.us.r-project.org')"
"""


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

def download_project(project_id, download_directory):
    osf = OSF()
    project = osf.project(project_id)
    storage = project.storage('osfstorage')

    project_path = os.path.join(download_directory, project_id)
    if not os.path.exists(project_path):
        os.makedirs(project_path)

    print(f"Starting download of all contents in project '{project_id}'...")
    for folder in storage.folders:
        download_folder(folder, project_path)
    for file in storage.files:
        download_file(file, project_path)
    print("Project download completed.")

    return project_path

def run_flowr_dependency_query(project_path):
    dependency_file = os.path.join(project_path, "dependencies.txt")
    print("Running flowr_dependency_query.py...")

    script_path = "/data/meet/pipeline/flowr_dependency_query.py"
    command = [
        "python3", script_path,
        "--input-dir", project_path,
        "--output-file", dependency_file
    ]

    subprocess.run(command, check=True)
    print(f"Dependencies extracted to {dependency_file}")

def create_repo2docker_files(project_dir):
    repo2docker_path = os.path.join(project_dir, "repo2docker")
    os.makedirs(repo2docker_path, exist_ok=True)

    # Move all project files into the repo2docker directory
    for file_name in os.listdir(project_dir):
        file_path = os.path.join(project_dir, file_name)
        if file_name != "repo2docker" and os.path.isfile(file_path):
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

    # Create environment.yml
    environment_yml_path = os.path.join(repo2docker_path, "environment.yml")
    with open(environment_yml_path, "w") as env_yml:
        env_yml.write("name: r-environment\n")
        env_yml.write("channels:\n")
        env_yml.write("  - defaults\n")
        env_yml.write("  - conda-forge\n")
        env_yml.write("dependencies:\n")
        env_yml.write("  - r-base=4.3\n")
        env_yml.write("  - r-essentials\n")
        env_yml.write("  - r-devtools\n")
        for dep in dependencies:
            env_yml.write(f"  - r-{dep}\n")

    # Create postBuild
    postbuild_path = os.path.join(repo2docker_path, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write(POSTBUILD_CONTENT)
    os.chmod(postbuild_path, 0o755)

    print(f"Repo2docker files created in {repo2docker_path}")


def process_project(project_id):
    project_path = download_project(project_id, BASE_DIR)
    run_flowr_dependency_query(project_path)
    create_repo2docker_files(project_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 automation_pipeline.py <OSF_PROJECT_ID>")
        sys.exit(1)

    project_id = sys.argv[1]
    process_project(project_id)
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
