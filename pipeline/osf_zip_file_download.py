import pandas as pd
import subprocess
from tqdm import tqdm
from utils import DOWNLOADS_DIR, METADATA_DIR, log_message


def download_project(project_id):
    log_message(project_id, "DOWNLOAD", f"Downloading project {project_id} from OSF...")
    url = f"https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/?zip="
    file_name = f"{DOWNLOADS_DIR}/{project_id}.zip"
    # the nc flag is used to skip the download if the file already exists (no clobber)
    result = subprocess.run(
        ["wget", "-nc", "-O", file_name, url], capture_output=True, text=True
    )
    if result.returncode == 0:
        log_message(project_id, "DOWNLOAD", f"✅ Download completed: {file_name}")
    else:
        log_message(project_id, "DOWNLOAD", f"❌ Download failed: {result.stderr}")


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


if __name__ == "__main__":
    download_all_projects()
