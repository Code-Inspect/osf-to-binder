import pandas as pd
import subprocess
from tqdm import tqdm
from utils import DOWNLOADS_DIR, METADATA_DIR, log_message

def download_project(project_id):
    log_message(project_id, "DOWNLOAD", f"Downloading project {project_id} from OSF...")
    url = f"https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/?zip="
    file_name = f"{DOWNLOADS_DIR}/{project_id}.zip"
    # the nc flag is used to skip the download if the file already exists (no clobber)
    subprocess.run(["wget", "-nc", "-O", file_name, url])

def download_all_projects():
    df = pd.read_csv(f"{METADATA_DIR}/project_id_r_code_file.csv")
    for project_id in tqdm(df["Project ID"].dropna().unique()):
        download_project(project_id)

if __name__ == "__main__":
    download_all_projects() 