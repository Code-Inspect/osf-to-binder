#!/bin/bash

# Base directory
BASE_DIR="Automating_Reproducibility"

# Python script paths
PIPELINE_SCRIPT="$BASE_DIR/automation_pipeline.py"
RUN_CONTAINER_SCRIPT="$BASE_DIR/run_code_in_container.py"
EXECUTE_R_SCRIPT="$BASE_DIR/execute_r_files_in_container.py"

# Function to clean Docker containers and images
clean_docker() {
    echo "Cleaning up Docker containers and images..."
    docker container ls -a -q | xargs -r docker container rm -f || true
    docker image prune -a -f || true
}

run_pipeline() {
    local PROJECT_ID=$1
    echo "Running Python script $PIPELINE_SCRIPT for project ID: $PROJECT_ID"
    python3 "$PIPELINE_SCRIPT" "$PROJECT_ID"
    if [ $? -ne 0 ]; then
        echo "❌ Error: Pipeline execution failed for project '$PROJECT_ID'."
        exit 1
    fi
}

build_repository() {
    local PROJECT_ID=$1
    echo "=== Building repository for project: $PROJECT_ID ==="
    python3 "$RUN_CONTAINER_SCRIPT" --project-id "$PROJECT_ID" --repo-only
}

run_container() {
    local PROJECT_ID=$1
    echo "=== Running container for project: $PROJECT_ID ==="
    python3 "$RUN_CONTAINER_SCRIPT" --project-id "$PROJECT_ID" --build-and-run
}

# Function to execute R scripts in the container
execute_r_scripts() {
    local PROJECT_ID=$1
    echo "Executing R scripts in the container for project ID: $PROJECT_ID"
    python3 "$EXECUTE_R_SCRIPT" "$PROJECT_ID"
    if [ $? -ne 0 ]; then
        echo "Error: R script execution failed for project $PROJECT_ID."
        return 1
    fi
}

# Function to process each project
process_project() {
    local PROJECT_ID=$1
    local logs_dir="$BASE_DIR/logs"
    mkdir -p "$logs_dir"
    local project_log_file="$logs_dir/${PROJECT_ID}_pipeline.log"
    echo "Processing project: $PROJECT_ID"

    # Record start time
    local start_time=$(date +%s)

    clean_docker
    run_pipeline "$PROJECT_ID" || return 1
    build_repository "$PROJECT_ID" || return 1
    run_container "$PROJECT_ID" || return 1
    execute_r_scripts "$PROJECT_ID" || return 1

    echo "Pipeline execution completed successfully for project: $PROJECT_ID"

    # Record end time and calculate total duration
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    # Append total time to execution_log.txt inside the logs folder
    echo "⏳ Total execution time for project $PROJECT_ID: $total_time seconds" | tee -a "$project_log_file"
}

# Main script execution
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <PROJECT_ID> or $0 <file_with_project_ids.txt>"
    exit 1
fi

# Set up environment with uv
echo "Setting up the environment using uv..."
uv sync || { echo "Error: Failed to sync environment using uv."; exit 1; }
source .venv/bin/activate

# Check if the argument is a file or a single project ID
INPUT=$1

if [ -f "$INPUT" ]; then
    echo "Processing project IDs from file: $INPUT"
    while IFS= read -r PROJECT_ID || [ -n "$PROJECT_ID" ]; do
        if [ -n "$PROJECT_ID" ]; then
            process_project "$PROJECT_ID"
        fi
    done < "$INPUT"
else
    process_project "$INPUT"
fi

echo "All project processing completed successfully."
