import pandas as pd
import requests
from tqdm import tqdm
from utils import DOWNLOADS_DIR, METADATA_DIR, log_message, get_zip_file_path, get_project_path, get_src_path
import os
import zipfile


def download_project(project_id):
    log_message(project_id, "DOWNLOAD", f"Downloading project {project_id} from OSF...")
    url = f"https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/?zip="
    file_name = f"{DOWNLOADS_DIR}/{project_id}.zip"

    # Skip if file already exists
    if os.path.exists(file_name):
        log_message(project_id, "DOWNLOAD", f"File already exists: {file_name}")
        return

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Download with progress bar
        with open(file_name, "wb") as f:
            with tqdm(
                desc=f"Downloading {project_id}",
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
                leave=True,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:  # filter out keep-alive new chunks
                        size = f.write(chunk)
                        pbar.update(size)

        log_message(project_id, "DOWNLOAD", f"✅ Download completed: {file_name}")
    except BaseException as e:
        # remove the uncomplete zip file
        if os.path.exists(file_name):
            os.remove(file_name)
        if isinstance(e, requests.exceptions.RequestException):
            # continue the program
            log_message(project_id, "DOWNLOAD", f"❌ Download failed: {str(e)}")
        else:
            # Re-raise the exception to stop the program
            raise 


def download_all_projects():
    project_ids = (
        pd.read_csv(f"{METADATA_DIR}/project_id_r_code_file.csv")["Project ID"]
        .dropna()
        .unique()
    )
    print(f"Downloading {len(project_ids)} projects...")
    for project_id in tqdm(project_ids):
        download_project(project_id)
    print("All downloads completed.")


def unzip_project(project_id):
    """Unzips a project from the download directory. Downloads the project if it doesn't exist."""
    zip_file = get_zip_file_path(project_id)
    project_path = get_project_path(project_id)
    src_path = get_src_path(project_id)

    if os.path.exists(src_path) and os.listdir(src_path):
        log_message(project_id, "DOWNLOAD", f"⏭️ Project '{project_id}' already exists at {src_path}. Skipping download and extraction.")
        return project_path
    
    if not os.path.exists(zip_file):
        download_project(project_id)
    
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(src_path, exist_ok=False)
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        log_message(project_id, "DOWNLOAD", f"📦 Extracting {zip_file} to {src_path}...")
        zip_ref.extractall(src_path)
    
    return project_path

if __name__ == "__main__":
    download_all_projects()
