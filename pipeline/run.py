import os
import time
import zipfile
import glob
import argparse
from utils import REPOS_DIR, DOWNLOADS_DIR, log_message
from deploy_container import build_and_run
from create_repository import create_repo2docker_files
from execute_r_files_in_container import run_all_files_in_container, create_csv_file
from flowr_dependency_query import extract_dependencies
from osf_zip_file_download import download_project

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
    
    try:
        extract_dependencies(input_dir=src_path, output_file=dependency_file)
        log_message(project_id, "DEPENDENCY EXTRACTION", f"✅ Dependencies extracted to {dependency_file}")
        return True
    except Exception as e:
        log_message(project_id, "DEPENDENCY EXTRACTION", f"❌ Failed to extract dependencies: {e}")
        return False

def unzip_project(project_id):
    """Unzips a project from the download directory."""
    zip_file = os.path.join(DOWNLOADS_DIR, f"{project_id}.zip")
    project_path = os.path.join(REPOS_DIR, f"{project_id}_repo")
    src_path = os.path.join(project_path, f"{project_id}_src")

    if os.path.exists(project_path) and os.listdir(project_path):
        log_message(project_id, "DOWNLOAD", f"⏭️ Project '{project_id}' already exists at {project_path}. Skipping download and extraction.")
        return project_path
    
    if not os.path.exists(zip_file):
        download_project(project_id)
    
    os.makedirs(project_path, exist_ok=False)
    os.makedirs(src_path, exist_ok=False)
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        log_message(project_id, "DOWNLOAD", f"📦 Extracting {zip_file} to {src_path}...")
        zip_ref.extractall(src_path)
    
    return project_path

def execute_r_scripts(project_id):
    """Executes R scripts in the container."""
    log_message(project_id, "R_EXECUTION", f"Executing R scripts in the container for project ID: {project_id}")
    try:
        create_csv_file()
        run_all_files_in_container(project_id)
        return True
    except Exception as e:
        log_message(project_id, "R_EXECUTION", f"❌ Failed to execute R scripts: {e}")
        return False


def process_project(project_id):
    """Processes a project with all necessary steps."""
    start_time = time.time()
    log_message(project_id, "PROJECT INIT", f"🚀 Starting processing for project '{project_id}'")

    try:
        # Step 1: Download/Unzip Project
        project_download_start = time.time()
        project_path = unzip_project(project_id)

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

        # Step 4: Build and Run Container
        if not build_and_run(project_id):
            return False

        # Step 5: Execute R Scripts
        if not execute_r_scripts(project_id):
            return False

        total_time = time.time() - start_time
        log_message(project_id, "TOTAL TIME", f"⏳ Total processing time: {total_time:.2f} seconds.")
        return True

    except Exception as e:
        log_message(project_id, "ERROR", f"❌ Error occurred: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Process OSF projects for reproducibility testing.')
    parser.add_argument('input', help='OSF project ID or file containing project IDs')
    parser.add_argument('--github', action='store_true', help='Create GitHub repositories for the projects')
    args = parser.parse_args()

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