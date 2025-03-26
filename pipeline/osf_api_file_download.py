import os
import time
import requests
from utils import log_message
from osfclient import OSF

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
