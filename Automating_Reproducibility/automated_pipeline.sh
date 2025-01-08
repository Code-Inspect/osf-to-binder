#!/bin/bash

BASE_DIR="/data/meet/pipeline"
REPO2DOCKER_DIR="/data/meet/repo2docker"
PYTHON_SCRIPT="/data/meet/pipeline/automation_pipeline.py"

setup_repo2docker_env() {
    echo "Setting up repo2docker environment..."
    if [ ! -d "$REPO2DOCKER_DIR" ]; then
        echo "Cloning repo2docker repository..."
        git clone https://github.com/jupyterhub/repo2docker.git "$REPO2DOCKER_DIR"
    fi

    cd "$REPO2DOCKER_DIR" || exit
    if [ ! -d "$REPO2DOCKER_DIR/bin" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .
    fi

    echo "Activating virtual environment..."
    source "$REPO2DOCKER_DIR/bin/activate"

    echo "Installing repo2docker and osfclient..."
    python3 -m pip install --upgrade pip setuptools
    python3 -m pip install .
    python3 -m pip install osfclient
}

clean_docker() {
    echo "Cleaning up Docker containers and images..."
    docker container ls -a | awk '{print $1}' | tail -n +2 | xargs -I {} docker container rm -f {} || true
    docker image prune -a -f || true
}

run_python_pipeline() {
    PROJECT_ID=$1

    if [ -z "$PROJECT_ID" ]; then
        echo "Error: Project ID is required."
        exit 1
    fi

    echo "Activating Python virtual environment..."
    source "$REPO2DOCKER_DIR/bin/activate"

    echo "Running the Python script..."
    python3 "$PYTHON_SCRIPT" "$PROJECT_ID"
    if [ $? -ne 0 ]; then
        echo "Error: Python script execution failed."
        exit 1
    fi
}

run_repo2docker_container() {
    PROJECT_ID=$1

    if [ -z "$PROJECT_ID" ]; then
        echo "Error: Project ID is required."
        exit 1
    fi

    PROJECT_DIR="$BASE_DIR/$PROJECT_ID/repo2docker"
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Error: Repo2docker directory for project '$PROJECT_ID' not found."
        exit 1
    fi

    echo "Building and running repo2docker container..."
    cd "$PROJECT_DIR" || exit

    # Run repo2docker and expose RStudio
    repo2docker --user-id=1000 --user-name=rstudio .
}

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <PROJECT_ID>"
    exit 1
fi

PROJECT_ID=$1

setup_repo2docker_env
clean_docker
run_python_pipeline "$PROJECT_ID"
run_repo2docker_container "$PROJECT_ID"
