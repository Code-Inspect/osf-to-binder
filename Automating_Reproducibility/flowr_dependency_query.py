import json
import re
import os
import subprocess

def parse_flowr_output(raw_output):
    """Parses the raw output from flowR to extract dependencies."""
    if "exit" in raw_output:
        raw_output = raw_output.split("exit", 1)[1].strip()

    # Extract JSON part
    json_match = re.search(r'({.*})', raw_output, re.DOTALL)
    if not json_match:
        print("No valid JSON found in the output.")
        return None

    json_str = json_match.group(1)

    # Parse JSON
    try:
        dependencies = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    # Extract relevant data
    result = {
        "libraries": [
            lib["libraryName"] for lib in dependencies.get("dependencies", {}).get("libraries", [])
        ],
        "sourcedFiles": [
            file["file"] for file in dependencies.get("dependencies", {}).get("sourcedFiles", [])
        ],
        "readData": [
            data["source"] for data in dependencies.get("dependencies", {}).get("readData", [])
        ],
        "writtenData": [
            data["destination"] for data in dependencies.get("dependencies", {}).get("writtenData", [])
        ],
    }

    return result

def run_docker_flowr(query, file_path):
    """Runs the Docker flowR query for a given R file."""
    docker_command = [
        "docker", "run", "-i", "--rm",
        "-v", "/data/meet/pipeline/hzncs:/data",
        "eagleoutice/flowr"
    ]

    # Adjust file path for the Docker container
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
                # Adjust file path relative to the project root
                relative_file_path = os.path.relpath(os.path.join(root, file), project_path)
                print(f"Processing {relative_file_path}...")
                raw_output = run_docker_flowr("dependencies", relative_file_path)
                if raw_output:
                    parsed_deps = parse_flowr_output(raw_output)
                    if parsed_deps:
                        dependencies["libraries"].update(parsed_deps["libraries"])
                        dependencies["sourcedFiles"].update(parsed_deps["sourcedFiles"])
                        dependencies["readData"].update(parsed_deps["readData"])
                        dependencies["writtenData"].update(parsed_deps["writtenData"])
    return dependencies

def generate_requirements_file(dependencies, output_file="dependencies.txt"):
    """Generates a dependencies file for a project."""
    if not dependencies:
        print("No dependencies to write.")
        return

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

# Main execution flow
def process_project(project_path, output_file="dependencies.txt"):
    """Processes a single project to generate a dependencies file."""
    dependencies = aggregate_dependencies(project_path)
    generate_requirements_file(dependencies, output_file)

# Example: Process a single project directory
project_path = "/data/meet/pipeline/hzncs"
output_file = os.path.join(project_path, "dependencies.txt")
process_project(project_path, output_file)