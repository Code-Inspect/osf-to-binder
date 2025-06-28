# OSF-to-Binder

OSF-to-Binder is a tool for automatically building reproducible repositories from the source code of scientific publications. It analyzes the code, adds dependencies, builds a Binder-ready repository, and executes the code in the project. Detailed results of running the tool are available in the [code-inspect-binder](https://github.com/code-inspect-binder) organization.

## Project Structure

```
osf-to-binder/
├── pipeline/          # Analysis pipeline code
├── repos/             # Created binder-ready repositories
├── results/           # Code execution results
├── logs/              # Log files from analysis runs
├── metadata/          # Metadata and analysis configurations
├── downloads/         # Storage for downloaded osf files
├── pyproject.toml     # Project dependencies
└── uv.lock            # Locked dependency versions
```

## Prerequisites

- `uv` python package manager
- Git LFS (https://git-lfs.com/)
- Docker

## Installation

1. Install `uv` (if not already installed):
```bash
# On macOS with Homebrew
brew install uv

# On Linux/Windows, follow instructions at:
# https://docs.astral.sh/uv/getting-started/installation/
```

2. Clone the repository:
```bash
git clone https://github.com/Code-Inspect/osf-to-binder
cd osf-to-binder
```

## Usage

1. Configure your analysis settings in the `metadata` directory
2. Run the analysis pipeline:
```bash
uv run pipeline/run.py <project_id>  # Process a single project

# OR

uv run pipeline/run.py metadata/project_ids.txt  # Process multiple projects from a file
```

The tool will:
- Download and unzip OSF project files
- Extract dependencies from R scripts using `flowR`
- Create a docker container using `repo2docker`
- Build and run Docker containers
- Execute R scripts in the container
- Log all operations and results

## Optional: FlowR-Enabled Repositories

This version of the repository has the **[flowR Addin](https://github.com/flowr-analysis/rstudio-addin-flowr)** preinstalled. flowR allows visual design and execution of data analysis workflows within RStudio, supporting better reproducibility and modular analysis pipelines.

### How to Enable FlowR

Use the `--flowr` flag during pipeline execution:

```bash
uv run pipeline/run.py <project_id> --flowr

# OR

uv run pipeline/run.py metadata/project_ids.txt --flowr
```

When enabled, the pipeline will:

- Create a modified version of the repository with a `-f` suffix (e.g., `osf_<project_id>-f/`)
- Installs the flowR addin automatically in interactive RStudio sessions
- Name Docker image and container as `repo2docker-<project_id>-f`
- Push the image to DockerHub under the same `-f` suffix

---

## Citation

If you use this repository or refer to this work, please cite:
```
@inproceedings{Saju2025Computational,
  title     = {Computational Reproducibility of R Code Supplements on {OSF}},
  author    = {Saju, Lorraine and Holtdirk, Tobias and Mangroliya, Meetkumar Pravinbhai and Bleier, Arnim},
  booktitle = {R2CASS 2025: Social Science Meets Web Data: Reproducible and Reusable Computational Approaches, Workshop Proceedings of the 19th International AAAI Conference on Web and Social Media},
  year      = {2025},
  doi       = {10.36190/2025.49},
  publisher = {Association for the Advancement of Artificial Intelligence}
}
```

This work was funded by the German Research Foundation (DFG) under project No. 504226141.
