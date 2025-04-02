import os
import requests
from git import Repo
from osfclient.api import OSF
from utils import log_message
from utils import LOGS_DIR


# Define log path inside the logs directory
MISSING_LOG_PATH = os.path.join(LOGS_DIR, "missing_packages.log")

def get_latest_r_package_version(package_name):
    """Fetch latest R package version from CRAN and log if not found."""
    try:
        cran_resp = requests.get(f"https://crandb.r-pkg.org/{package_name}")
        if cran_resp.status_code == 200:
            return cran_resp.json().get("Version")
        else:
            with open(MISSING_LOG_PATH, "a") as log:
                log.write(f"{package_name} - not found on CRAN\n")
    except Exception as e:
        with open(MISSING_LOG_PATH, "a") as log:
            log.write(f"{package_name} - CRAN check failed: {str(e)}\n")
    
    return None
    
def create_github_repo(repo_name):
    """Creates a GitHub repository."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        log_message(repo_name, "REPO2DOCKER SETUP", "❌ GitHub access token not found in environment variables.")
        return False

    headers = {"Authorization": f"token {token}"}
    payload = {"name": repo_name, "private": False}
    response = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
    
    if response.status_code == 201:
        log_message(repo_name, "REPO2DOCKER SETUP", f"✅ GitHub repository '{repo_name}' created successfully.")
        return True
    elif response.status_code == 422:
        log_message(repo_name, "REPO2DOCKER SETUP", f"ℹ️ GitHub repository '{repo_name}' already exists.")
        return True
    else:
        log_message(repo_name, "REPO2DOCKER SETUP", f"❌ Failed to create GitHub repository: {response.json()}")
        return False

def create_repo2docker_files(project_dir, project_id, add_github_repo=False):
    """Creates necessary repo2docker files in the project directory."""
    repo_name = f"osf_{project_id}"
    dependencies_file = os.path.join(project_dir, "dependencies.txt")

    if not os.path.exists(dependencies_file):
        log_message(project_id, "REPO2DOCKER SETUP", f"⚠️ No dependencies.txt found in {project_dir}. Skipping dependency handling.")
        return False
    
    log_message(project_id, "REPO2DOCKER SETUP", f"✅ dependencies.txt found at {dependencies_file}. Proceeding with repo2docker setup.")
     
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

    # Fetch versions
    dependencies_with_versions = []
    for pkg in dependencies:
        version = get_latest_r_package_version(pkg)
        if version:
            dependencies_with_versions.append(f"{pkg} (== {version})")
        else:
            log_message(project_id, "REPO2DOCKER SETUP", f"⚠️ Could not fetch version for package: {pkg}. Adding without version.")
            dependencies_with_versions.append(pkg)
 
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
        if dependencies_with_versions:
            desc.write(",\n    ".join(dependencies_with_versions))
            desc.write("\n")
 
    os.remove(dependencies_file)

    # postbuild_path = os.path.join(project_dir, "postBuild")
    # with open(postbuild_path, "w") as postbuild:
    #     postbuild.write("#!/bin/bash\n\n")
    #     postbuild.write("# Update system and install required libraries\n")
    #     postbuild.write("# Install R-remotes version 2.5.0\n")
    #     postbuild.write("R -e \"install.packages('remotes', repos = 'http://cran.us.r-project.org', type = 'source')\"\n")
    #     postbuild.write("R -e \"remotes::install_version('remotes', version = '2.5.0', repos = 'http://cran.us.r-project.org')\"\n")
    #     postbuild.write("\n")
    #     postbuild.write("# Install FlowR\n")
    #     postbuild.write("R -e \"remotes::install_github('flowr-analysis/rstudio-addin-flowr')\"\n")
    #
    # os.chmod(postbuild_path, 0o755)

    osf = OSF()
    try:
        project = osf.project(project_id)
        project_title = project.title
        project_description = project.description or "No description provided."
    except Exception as e:
        log_message(project_id, "REPO2DOCKER SETUP", f"⚠️ Error fetching project details from OSF: {e}. Using default README content.")
        project_title = repo_name
        project_description = "This repository was automatically generated for use with repo2docker."

    readme_path = os.path.join(project_dir, "README.md")
    with open(readme_path, "w") as readme:
        # readme.write(f"# Binderised version of the OSF project - {project_id}\n\n")
        readme.write(f"# Executable Environment for OSF Project [{project_id}](https://osf.io/{project_id}/)\n\n")
        readme.write("---\n")
        readme.write("## OSF Project Metadata:\n\n")
        readme.write(f"**Project Title:** {project_title}\n\n")
        readme.write(f"**Project Description:**\n> {project_description}\n\n")
        readme.write(f"**Original OSF Page:** [https://osf.io/{project_id}/](https://osf.io/{project_id}/)\n\n")
        readme.write("---\n\n")
        readme.write(
            "This repository was automatically generated as part of a project to test the reproducibility of open science projects hosted on the Open Science Framework (OSF).\n\n"
        )
        readme.write(
            f"**Important Note:** The contents of the `{project_id}_src` folder were cloned from the OSF project on **12-03-2025**. Any changes made to the original OSF project after this date will not be reflected in this repository.\n\n"
        )
        readme.write(
            "The `DESCRIPTION` file was automatically added to make this project Binder-ready. For more information on how R-based OSF projects are containerized, please refer to the `osf-to-binder` GitHub repository: [https://github.com/Code-Inspect/osf-to-binder](https://github.com/Code-Inspect/osf-to-binder)\n\n"
        )
        readme.write("## How to Launch:\n\n")
        readme.write("**Launch in your Browser:**\n\n")
        readme.write(
            f"🚀 **MyBinder:** [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n"
        )
        readme.write(
            "   * This will launch the project in an interactive RStudio environment in your web browser.\n"
            "   * Please note that Binder may take a few minutes to build the environment.\n\n"
        )
        readme.write(
            f"🚀 **NFDI JupyterHub:** [![NFDI](https://nfdi-jupyter.de/images/nfdi_badge.svg)](https://hub.nfdi-jupyter.de/r2d/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n"
        )
        readme.write("   * This will launch the project in an interactive RStudio environment on the NFDI JupyterHub platform.\n\n")

        readme.write(f"**Access Downloaded Data:**\n")
        readme.write(f"The downloaded data from the OSF project is located in the `{project_id}_src` folder.\n\n")

    if add_github_repo:
        if not create_github_repo(repo_name):
            return False

        github_repo_url = f"https://github.com/Meet261/{repo_name}.git"
        log_message(project_id, "REPO2DOCKER SETUP", f"Initializing Git repository for {project_dir}...")
        
        try:
            repo = Repo.init(project_dir)
            if "origin" not in [remote.name for remote in repo.remotes]:
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

