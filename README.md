# OSF-to-Binder

OSF-to-Binder is a tool for automatically building reproducible repositories from source-code of scientific publications. It automatically analyzes the code, adds dependencies, builds a binder-ready repository and executes the code in the project.

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


---

This work was funded by the German Research Foundation (DFG) under project No. 504226141.
