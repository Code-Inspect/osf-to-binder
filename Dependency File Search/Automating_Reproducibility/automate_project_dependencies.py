#!/usr/bin/env python3

import os
import subprocess
from osfclient.api import OSF

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

    # Download all files in the folder
    for file in folder.files:
        download_file(file, folder_path)

    # Recursively download all subfolders
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

    # Assuming flowr_dependency_query.py is in the same folder as the script
    script_path = "/data/meet/pipeline/flowr_dependency_query.py"
    command = [
        "python3", script_path,
        "--input-dir", project_path,
        "--output-file", dependency_file
    ]

    subprocess.run(command, check=True)
    print(f"Dependencies extracted to {dependency_file}")

def main():
    project_id = input("Enter the OSF project ID: ").strip()
    base_directory = "/data/meet/pipeline"  # Change as needed

    # Step 1: Download the project contents
    project_path = download_project(project_id, base_directory)

    # Step 2: Run FlowR Dependency Query
    run_flowr_dependency_query(project_path)

    print(f"Process completed. Dependencies saved to {project_path}/dependencies.txt")

if __name__ == "__main__":
    main()
