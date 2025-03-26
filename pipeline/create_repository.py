import os
import requests
from git import Repo
from osfclient.api import OSF
from utils import log_message

def create_github_repo(repo_name):
    """Creates a GitHub repository."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        log_message(repo_name, "GITHUB", "❌ GitHub access token not found in environment variables.")
        return False

    headers = {"Authorization": f"token {token}"}
    payload = {"name": repo_name, "private": False}
    response = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
    
    if response.status_code == 201:
        log_message(repo_name, "GITHUB", f"✅ GitHub repository '{repo_name}' created successfully.")
        return True
    elif response.status_code == 422:
        log_message(repo_name, "GITHUB", f"ℹ️ GitHub repository '{repo_name}' already exists.")
        return True
    else:
        log_message(repo_name, "GITHUB", f"❌ Failed to create GitHub repository: {response.json()}")
        return False

def create_repo2docker_files(project_dir, project_id, add_github_repo=False):
    """Creates necessary repo2docker files in the project directory."""
    repo_name = f"osf_{project_id}"
    dependencies_file = os.path.join(project_dir, "dependencies.txt")

    if not os.path.exists(dependencies_file):
        log_message(project_id, "REPO2DOCKER", f"⚠️ No dependencies.txt found in {project_dir}. Skipping dependency handling.")
        return False
    
    log_message(project_id, "REPO2DOCKER", f"✅ dependencies.txt found at {dependencies_file}. Proceeding with repo2docker setup.")
     
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
        for dep in dependencies:
            desc.write(f"{dep}, ")
        desc.write("\n")
 
    os.remove(dependencies_file)

    postbuild_path = os.path.join(project_dir, "postBuild")
    with open(postbuild_path, "w") as postbuild:
        postbuild.write("#!/bin/bash\n\n")
        postbuild.write("# Update system and install required libraries\n")
        postbuild.write("# Install R-remotes version 2.5.0\n")
        postbuild.write("R -e \"install.packages('remotes', repos = 'http://cran.us.r-project.org', type = 'source')\"\n")
        postbuild.write("R -e \"remotes::install_version('remotes', version = '2.5.0', repos = 'http://cran.us.r-project.org')\"\n")
        postbuild.write("\n")
        postbuild.write("# Install FlowR\n")
        postbuild.write("R -e \"remotes::install_github('flowr-analysis/rstudio-addin-flowr')\"\n")

    os.chmod(postbuild_path, 0o755)

    osf = OSF()
    try:
        project = osf.project(project_id)
        project_title = project.title
        project_description = project.description or "No description provided."
    except Exception as e:
        log_message(project_id, "REPO2DOCKER", f"⚠️ Error fetching project details from OSF: {e}. Using default README content.")
        project_title = repo_name
        project_description = "This repository was automatically generated for use with repo2docker."

    readme_path = os.path.join(project_dir, "README.md")
    with open(readme_path, "w") as readme:
        readme.write(f"# Automated reproducibility test for the OSF project, {project_id}\n\n")
        readme.write("--- \n")
        readme.write(f"## OSF Project metadata: \n")
        readme.write(f"{project_title}\n\n")
        readme.write(f"{project_description}\n\n")
        readme.write("--- \n")
        readme.write(
            f"This repository was auto-generated as part of testing reproducibility of open science projects hosted on OSF. Original OSF page: [https://osf.io/{project_id}/](https://osf.io/{project_id}/)\n\n")
        readme.write(f"The contents of the folder {project_id}_src was cloned from the OSF project on 12-03-2025. The files, DESCRIPTION and postBuild has been added automatically inorder to make this project Binder ready.\n\n")
        readme.write("## How to Launch\n")
        readme.write(
            f"🚀 **Click below to launch the project on MyBinder:**  \n[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n")
        readme.write(
            f"🚀 **Click below to launch the project on the NFDI JupyterHub:**  \n[![NFDI](https://nfdi-jupyter.de/images/nfdi_badge.svg)](https://hub.nfdi-jupyter.de/r2d/gh/Meet261/{repo_name}/HEAD?urlpath=rstudio)\n\n")
        readme.write("## Start Container Locally\n")
        readme.write("To start the container locally:\n\n")
        readme.write("```bash\n")
        readme.write(f"docker run -p 8888:8888 --name {repo_name}-test -d {repo_name}-test\n")
        readme.write("```\n\n")
        readme.write(
            "This repository demonstrates how a project from OSF can be containerized and tested using Binder. We facilitate a one-click launch of the OSF project, allowing anyone to browse, execute the code, and verify or compare the results from the associated research paper. This aligns with the objectives of the **CodeInspector project**, where we aim to enable **browser-based reproducibility and evaluation of open science projects**.\n\n")
        readme.write(
            "By integrating **OSF** and **Binder**, we aim to enhance transparency and reproducibility in computational social science and beyond. This repository serves as an example of how research projects can be packaged and shared in a fully executable, browser-based environment.\n\n")
        readme.write("--- \n\n")
        readme.write("This work was funded by the German Research Foundation (DFG) under project No. 504226141.")

    if add_github_repo:
        if not create_github_repo(repo_name):
            return False

        github_repo_url = f"https://github.com/Meet261/{repo_name}.git"
        log_message(project_id, "GITHUB", f"Initializing Git repository for {project_dir}...")
        
        try:
            repo = Repo.init(project_dir)
            if "origin" not in [remote.name for remote in repo.remotes]:
                repo.create_remote("origin", github_repo_url)

            repo.git.add(all=True)
            repo.index.commit("Initial commit for repo2docker project")
            repo.git.checkout("-B", "main")
            repo.remotes.origin.push(refspec="main:main", force=True)
            log_message(project_id, "GITHUB", f"✅ Repo2docker files created and pushed to {github_repo_url}.")
            return True
        except Exception as e:
            log_message(project_id, "GITHUB", f"❌ Error pushing to GitHub: {e}")
            return False

    return True

