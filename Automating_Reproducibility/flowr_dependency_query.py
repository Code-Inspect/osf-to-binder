import json
import re
import os
import subprocess
import sys
import argparse
from utils import log_message, BASE_DIR


def parse_flowr_output(raw_output):
    """Parses the raw output from flowR to extract dependencies."""
    if "exit" in raw_output:
        raw_output = raw_output.split("exit", 1)[1].strip()

    json_match = re.search(r'({.*})', raw_output, re.DOTALL)
    if not json_match:
        print("No valid JSON found in the output.")
        return None

    json_str = json_match.group(1)

    try:
        dependencies = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    result = {
        "libraries": [
            lib["libraryName"] for lib in dependencies.get("dependencies", {}).get("libraries", [])
        ],
        "sourcedFiles": [
            file.get("file") for file in dependencies.get("dependencies", {}).get("sourcedFiles", [])
        ],
        "readData": [
            data.get("source") for data in dependencies.get("dependencies", {}).get("readData", [])
        ],
        "writtenData": [
            data.get("destination") for data in dependencies.get("dependencies", {}).get("writtenData", [])
        ],
    }
    return result

def run_docker_flowr(query, file_path, project_path):
    """Runs the Docker flowR query for a given R file."""
    abs_project_path = os.path.abspath(project_path)  # Ensure absolute path
    abs_file_path = os.path.abspath(file_path)  # Ensure absolute file path

    docker_command = [
        "docker", "run", "-i", "--rm",
        "-v", f"{abs_project_path}:/data",  # Use absolute path for mounting
        "eagleoutice/flowr"
    ]

    container_file_path = f"/data/{file_path}"

    query_command = f':query* "[{{ \\"type\\": \\"{query}\\" }}]" file://{container_file_path}'
    try:
        process = subprocess.Popen(
            docker_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=f"{query_command}\nexit\n")
        if stdout:
            print(f"Result for {container_file_path}: {stdout}")
            return stdout
        if stderr:
            print(f"Error: {stderr}")
            return None
    except Exception as e:
        print(f"Error running Docker command: {e}")
        return None

def aggregate_dependencies(project_path):
    """Aggregates dependencies across all R files in a project."""
    dependencies = {"libraries": set(), "sourcedFiles": set(), "readData": set(), "writtenData": set()}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".R"):
                relative_file_path = os.path.relpath(os.path.join(root, file), project_path)
                print(f"Processing {relative_file_path}...")
                raw_output = run_docker_flowr("dependencies", relative_file_path, project_path)
                if raw_output:
                    parsed_deps = parse_flowr_output(raw_output)
                    if parsed_deps:
                        dependencies["libraries"].update(parsed_deps["libraries"])
                        dependencies["sourcedFiles"].update(parsed_deps["sourcedFiles"])
                        dependencies["readData"].update(parsed_deps["readData"])
                        dependencies["writtenData"].update(parsed_deps["writtenData"])
    return dependencies

def generate_requirements_file(dependencies, output_file):
    """Generates a dependencies file for a project."""
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

    with open(output_file, "w") as f:
        f.write("# R libraries\n")
        for library in sorted(dependencies["libraries"]):
            f.write(f"{library}\n")

        if dependencies["sourcedFiles"]:
            f.write("\n# Sourced files\n")
            for file in sorted(dependencies["sourcedFiles"]):
                f.write(f"{file}\n")

        if dependencies["readData"]:
            f.write("\n# Data read\n")
            for data in sorted(dependencies["readData"]):
                f.write(f"{data}\n")

        if dependencies["writtenData"]:
            f.write("\n# Data written\n")
            for data in sorted(dependencies["writtenData"]):
                f.write(f"{data}\n")

    print(f"Dependencies file created: {output_file}")

def process_project(input_dir, output_file):
    """Processes a project to generate a dependencies file."""
    dependencies = aggregate_dependencies(input_dir)
    generate_requirements_file(dependencies, output_file)
    

# Main execution flow
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlowR Dependency Extractor")
    parser.add_argument("--input-dir", required=True, help="Input directory of the project")
    parser.add_argument("--output-file", required=True, help="Output file to save dependencies")

    args = parser.parse_args()

    print(f"Processing project: {args.input_dir}")
    process_project(args.input_dir, args.output_file)

    print("\nProject processed successfully.")
