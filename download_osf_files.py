import pandas as pd
import subprocess
from tqdm import tqdm

df = pd.read_csv("statcodesearch_pckg_urls.csv")

for source_url in tqdm(df.Source.dropna().unique()):
    id = source_url.split("/")[-2]
    print(id)
    url = f"https://files.osf.io/v1/resources/{id}/providers/osfstorage/?zip="
    file_name = f"downloads/{id}.zip"
    # the nc flag is used to skip the download if the file already exists (no clobber)
    subprocess.run(["wget", "-nc", "-O", file_name, url])
