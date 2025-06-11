import os
import requests
from git import Repo
from osfclient.api import OSF
from utils import log_message
from utils import LOGS_DIR
import time
import shutil
    
DOCKERHUB_USERNAME = "meet261"

def create_github_repo(repo_name, org="code-inspect-binder"):
    """Creates a GitHub repository under the specified organization."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        log_message(repo_name, "REPO2DOCKER SETUP", "❌ GitHub access token not found in environment variables.")
        return False

    headers = {"Authorization": f"token {token}"}
    payload = {"name": repo_name, "private": False, "auto_init": True}
    url = f"https://api.github.com/orgs/{org}/repos"
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        log_message(repo_name, "REPO2DOCKER SETUP", f"✅ GitHub repository '{repo_name}' created successfully.")
        return True
    elif response.status_code == 422:
        log_message(repo_name, "REPO2DOCKER SETUP", f"ℹ️ GitHub repository '{repo_name}' already exists.")
        return True
    else:
        log_message(repo_name, "REPO2DOCKER SETUP", f"❌ Failed to create GitHub repository: {response.json()}")
        return False
    
def fetch_osf_metadata(project_id, retries=5, delay=5):
    """Fetches OSF project title and description with retry logic."""
    osf = OSF()
    for attempt in range(retries):
        try:
            project = osf.project(project_id)
            title = project.title
            description = project.description or "No description provided."
            return title, description
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))  # exponential backoff
            else:
                log_message(project_id, "REPO2DOCKER SETUP", f"⚠️ OSF API failed after {retries} attempts: {e}")
                return f"osf_{project_id}", "This repository was automatically generated for use with repo2docker."


def create_repo2docker_files(project_dir, project_id, add_github_repo=False, flowr_enabled=False):
    """Creates necessary repo2docker files in the project directory."""
    repo_suffix = "-f" if flowr_enabled else ""
    repo_name = f"osf_{project_id}{repo_suffix}"
    dependencies_file = os.path.join(project_dir, "dependencies.txt")

    if not os.path.exists(dependencies_file):
        log_message(project_id, "REPO2DOCKER SETUP", f"⚠️ No dependencies.txt found in {project_dir}. Skipping dependency handling.")
        return False
    
    log_message(project_id, "REPO2DOCKER SETUP", f"✅ dependencies.txt found at {dependencies_file}. Proceeding with repo2docker setup.")
     
    dependencies = []
    with open(dependencies_file, "r",encoding="utf-8") as f:
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
    with open(description_path, "w", encoding="utf-8") as desc:
        desc.write("Package: repo2dockerProject\n")
        desc.write("Type: Package\n")
        desc.write("Title: Executable OSF Environment\n")
        desc.write("Version: 1.0\n")
        desc.write("Authors@R: c(person(\"Maintainer\", \"Example\", email = \"maintainer@example.com\", role = c(\"aut\", \"cre\")))\n")
        desc.write("Description: Automatically generated DESCRIPTION file for Repo2Docker.\n")
        desc.write(f"License: See license and authorship information at https://osf.io/{project_id}/\n")
        desc.write("Imports: ")
        for dep in dependencies:
            desc.write(f"{dep}, ")
        desc.write("\n")
 
    os.remove(dependencies_file)

    # 🧠 Use robust metadata retrieval with fallback
    project_title, project_description = fetch_osf_metadata(project_id)

    readme_path = os.path.join(project_dir, "README.md")
    with open(readme_path, "w",encoding="utf-8" ) as readme:
        # readme.write(f"# Binderised version of the OSF project - {project_id}\n\n")
        readme.write(f"# Executable Environment for OSF Project [{project_id}](https://osf.io/{project_id}/)\n\n")
        readme.write("This repository was automatically generated as part of a project to test the reproducibility of open science projects hosted on the Open Science Framework (OSF).\n\n"
        )
        readme.write(f"**Project Title:** {project_title}\n\n")
        readme.write(f"**Project Description:**\n> {project_description}\n\n")
        readme.write(f"**Original OSF Page:** [https://osf.io/{project_id}/](https://osf.io/{project_id}/)\n\n")
        readme.write("---\n\n")
        readme.write(
            f"**Important Note:** The contents of the `{project_id}_src` folder were cloned from the OSF project on **12-03-2025**. Any changes made to the original OSF project after this date will not be reflected in this repository.\n\n"
        )
        readme.write(
            "The `DESCRIPTION` file was automatically added to make this project Binder-ready. For more information on how R-based OSF projects are containerized, please refer to the `osf-to-binder` GitHub repository: [https://github.com/Code-Inspect/osf-to-binder](https://github.com/Code-Inspect/osf-to-binder)\n\n"
        )

        if flowr_enabled:
            readme.write("## flowR Integration\n\n")
            readme.write("This version of the repository has the **[flowR Addin](https://github.com/flowr-analysis/rstudio-addin-flowr)** preinstalled. ")
            readme.write("flowR allows visual design and execution of data analysis workflows within RStudio, supporting better reproducibility and modular analysis pipelines.\n\n")
            readme.write("To use flowR, open the project in RStudio and go to `Addins` > `flowR`.\n\n")

        readme.write("## How to Launch:\n\n")
        readme.write("**Launch in your Browser:**\n\n")
        readme.write(
            f"🚀 **MyBinder:** [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/code-inspect-binder/{repo_name}/HEAD?urlpath=rstudio)\n\n"
        )
        readme.write(
            "   * This will launch the project in an interactive RStudio environment in your web browser.\n"
            "   * Please note that Binder may take a few minutes to build the environment.\n\n"
        )
        readme.write(
            f"🚀 **NFDI JupyterHub:** [![NFDI](https://nfdi-jupyter.de/images/nfdi_badge.svg)](https://hub.nfdi-jupyter.de/r2d/gh/code-inspect-binder/{repo_name}/HEAD?urlpath=rstudio)\n\n"
        )
        readme.write("   * This will launch the project in an interactive RStudio environment on the NFDI JupyterHub platform.\n\n")

        readme.write(f"**Access Downloaded Data:**\n")
        readme.write(f"The downloaded data from the OSF project is located in the `{project_id}_src` folder.\n\n")
        readme.write("## Run via Docker for Long-Term Reproducibility\n\n")
        readme.write("In addition to launching this project using Binder or NFDI JupyterHub, you can reproduce the environment locally using Docker. This is especially useful for long-term access, offline use, or high-performance computing environments.\n\n")
        readme.write("### Pull the Docker Image\n\n")
        suffix = "-f" if flowr_enabled else ""
        readme.write("```bash\n")
        readme.write(f"docker pull {DOCKERHUB_USERNAME}/repo2docker-{project_id}{suffix}:latest\n")
        readme.write("```\n\n")

        readme.write("### Launch RStudio Server\n\n")
        readme.write("Run the container (with a name, e.g. `rstudio-dev`):\n")

        suffix = "-f" if flowr_enabled else ""
        readme.write("```bash\n")
        readme.write(f"docker run -it --name rstudio-dev --platform linux/amd64 -p 8888:8787 --user root {DOCKERHUB_USERNAME}/repo2docker-{project_id}{suffix} bash\n")
        readme.write("```\n\n")

        readme.write("Inside the container, start RStudio Server with no authentication:\n")
        readme.write("```bash\n")
        readme.write("/usr/lib/rstudio-server/bin/rserver --www-port 8787 --auth-none=1\n")
        readme.write("```\n\n")

        readme.write("Then, open your browser and go to: [http://localhost:8888](http://localhost:8888)\n\n")

        readme.write("> **Note:** If you're running the container on a remote server (e.g., via SSH), replace `localhost` with your server's IP address.\n")
        readme.write("> For example: `http://<your-server-ip>:8888`\n\n")

        if flowr_enabled:
            readme.write("## Looking for the Base Version?\n\n")
            readme.write("For the original Binder-ready repository **without flowR**, visit:\n")
            readme.write(f"[osf_{project_id}](https://github.com/code-inspect-binder/osf_{project_id})\n\n")

    if flowr_enabled:
        rprofile_path = os.path.join(project_dir, ".Rprofile")
        with open(rprofile_path, "w", encoding="utf-8") as rprofile:
            rprofile.write("""if (interactive() && Sys.getenv(\"RSTUDIO\") == \"1\") {
    message(\"Scheduling flowR addin installation...\")
    later::later(function() {
        message(\"Installing flowR addin...\")
        try(rstudioaddinflowr:::install_node_addin(), silent = FALSE)
    }, delay = 2)
}
""")

        postbuild_path = os.path.join(project_dir, "postBuild")
        with open(postbuild_path, "w", encoding="utf-8") as postbuild:
            postbuild.write("#!/bin/bash\n\n")
            postbuild.write("echo \"Installing flowR addin...\"\n\n")
            postbuild.write("Rscript -e \"install.packages('remotes', repos = 'https://cloud.r-project.org')\"\n\n")
            postbuild.write("Rscript -e \"if (Sys.getenv('GITHUB_ACCESS_TOKEN') != '') Sys.setenv(GITHUB_PAT = Sys.getenv('GITHUB_ACCESS_TOKEN')); remotes::install_github('flowr-analysis/rstudio-addin-flowr@v0.1.2')\"\n")

        os.chmod(postbuild_path, 0o775)

    if add_github_repo:
        if not create_github_repo(repo_name, org="code-inspect-binder"):
            return False

        github_repo_url = f"https://github.com/code-inspect-binder/{repo_name}.git"
        log_message(project_id, "REPO2DOCKER SETUP", f"Initializing Git repository for {project_dir}...")
        
        try:
            git_dir = os.path.join(project_dir, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)

            repo = Repo.init(project_dir)
            repo.create_remote("origin", github_repo_url)

            repo.git.add(all=True)
            repo.index.commit("Initial commit for repo2docker project")
            repo.git.checkout("-B", "main")
            repo.remotes.origin.push(refspec="main:main", force=True)
            log_message(project_id, "REPO2DOCKER SETUP", f"✅ Repo2docker files created and pushed to {github_repo_url}.")
            return True
        
        except Exception as e:
            log_message(project_id, "REPO2DOCKER SETUP", f"❌ Error pushing to GitHub: {e}")
            return False

    return True

