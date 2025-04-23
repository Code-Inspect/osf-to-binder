import os
import re
import pandas as pd
from utils import LOGS_DIR, RESULTS_DIR, log_message


RESULTS_FILE = os.path.join(RESULTS_DIR, "execution_results.csv")  # CSV file at the base level

# Error categorization
code_error_keywords = [
    "does not exist", "unexpected", "cannot change working directory",
    "file choice cancelled", "invalid argument", "could not find function",
    "object .* not found", "rstudio not running", "cannot open file", "unable to open file",
    "invalid multibyte string", "dimnames", "set.", "cannot open compressed file", "failed to search directory",
    "folder already exists", "cannot find directory", "NA/NaN argument", "NAs introduced by coercion",
    "undefined columns selected", "invalid multibyte character", "argument .* is missing, with no default",
    "not an exported object from 'namespace", "unknown arguments", "unused arguments",
    "unable to install packages", "incompatible dimensions", "object of type .* is not subsettable",
    "semantic error in", "ill-typed arguments supplied to function",
    "stan_model", "rstan", "Error in stanc", "StanHeaders", "could not find function \"stanc\"",
    "can only print from a screen device", "number of items to replace is not a multiple of replacement length",
    "character argument expected", "labels appear to be misencoded", "can't select columns that don't exist",
    "argument is of length zero", "HTTP status code 410"
]

container_error_keywords = [
    "unable to load shared object", "cannot open shared object file",
    "no package called", "lazy loading failed", "package or namespace load failed",
    "package installation failed", "missing package",
    "unable to start data viewer", "cairo error 'error while writing to output stream'",
    "package .* required by .* could not be found"
]

# Simplified pattern mapping
error_patterns = {
    r"error in file.*?: cannot open the connection": "File Read Error - Cannot Open Connection",
    r"cannot open file .*\.r['\"]?": "Invalid File or Directory Path",
    r"cannot open file .*?: No such file or directory": "Invalid File or Directory Path",
    r"cannot change working directory": "Invalid File or Directory Path",
    r"does not exist": "Missing Object or Function",
    r"unable to open file: .*? ": "Missing Object or Function",
    r"object ['\"].*?['\"] not found": "Missing Object or Function",
    r"object '.*' not found": "Missing Object or Function",
    r"Failed to search directory .*no such file or directory": "Invalid File or Directory Path",
    r"Cannot find directory .*": "Invalid File or Directory Path",
    r"Error in setwd\(\) : argument .* is missing, with no default": "Syntax or Argument Error",
    r"character argument expected": "Syntax or Argument Error",
    r"unexpected": "Syntax or Argument Error",
    r"file choice cancelled": "File Selection Error",
    r"invalid argument": "Syntax or Argument Error",
    r"argument is of length zero": "Syntax or Argument Error",
    r"unable to load shared object": "Shared Library Load Error",
    r"lazy loading failed": "Package Installation Failure",
    r"package or namespace load failed": "Package Installation Failure",
    r"no package called ‘([^’]+)’": "Missing Package",
    r"Package [`‘']\w+[`’'] required for this function to work": "Missing Package",
    r"package [`‘'].*[`’'] required by [`‘'].*[`’'] could not be found": "Missing Package",
    r"unable to start data viewer": "System-Level Dependency Missing",
    r"cairo error 'error while writing to output stream'": "System-Level Dependency Missing",
    r"could not find function [\"']left_join[\"']": "Missing Object or Function",
    r"could not find function [\"'](\w+)[\"']": "Missing Object or Function",
    r"could not find function": "Missing Object or Function",
    r"rstudio not running": "RStudio Environment Error",
    r"invalid multibyte string": "Encoding/String Handling Error",
    r"dimnames.*not equal to array extent": "Data Structure Mismatch",
    r"run `set\.\w+\.folder\(<path>\)`": "Package Folder Configuration Required",
    r"cannot open compressed file .*?['\"], probable reason 'No such file or directory'": "Invalid File or Directory Path",
    r"Error: Folder \".*\" already exists\. Stopping here to avoid overwriting files\.": "Invalid File or Directory Path",
    r"NA/NaN argument": "Syntax or Argument Error",
    r"NAs introduced by coercion": "Syntax or Argument Error",
    r"undefined columns selected": "Data Structure Mismatch",
    r"Can't select columns that don't exist\.": "Data Structure Mismatch",
    r"invalid multibyte character in parser": "Encoding/String Handling Error",
    r"Error: '.*' is not an exported object from 'namespace:.*'": "Missing Object or Function",
    r"unknown arguments:.*": "Syntax or Argument Error",
    r"unused argument \(.+\)": "Syntax or Argument Error",
    r"unable to install packages": "Package Installation Failure",
    r"incompatible dimensions": "Data Structure Mismatch",
    r"object of type '.*' is not subsettable": "Data Structure Mismatch",
    r"semantic error in .*line \d+, column \d+": "Modeling Package Error (Stan)",
    r"ill-typed arguments supplied to function .*": "Modeling Package Error (Stan)",
    r"Error in stanc": "Modeling Package Error (Stan)",
    r"stan_model": "Modeling Package Error (Stan)",
    r"rstan version": "Modeling Package Error (Stan)",
    r"StanHeaders": "Modeling Package Error (Stan)",
    r"could not find function [\"']stanc[\"']": "Modeling Package Error (Stan)",
    r"can only print from a screen device": "PDF Generation Error - Requires Screen Device",
    r"number of items to replace is not a multiple of replacement length": "Data Structure Mismatch",
    r"HTTP status code 410": "External Dependency Missing",
    r"labels appear to be misencoded": "Encoding/String Handling Error",
}

def analyze_project_log(project_id):
    exec_log = os.path.join(LOGS_DIR, f"{project_id}_execution.log")
    if not os.path.exists(exec_log):
        print(f"⚠️ Log file not found for project {project_id}")
        return

    try:
        df = pd.read_csv(RESULTS_FILE)
    except pd.errors.EmptyDataError:
        print(f"⚠️ Results file exists but has no data. Skipping error analysis for project {project_id}")
        return

    df_project = df[df["Project ID"] == project_id]

    with open(exec_log, "r", encoding="utf-8") as f:
        log_content = f.read()

    for i, row in df_project.iterrows():
        file = row["R/Rmd Script"]
        status = row["Execution Status"]
        if status.lower() != "failed":
            df.loc[i, "Reason"] = "-"
            df.loc[i, "Error Message"] = "-"
            continue

        pattern = re.compile(rf"File: .*{re.escape(file)}.*?\n(.*?)Execution halted", re.DOTALL)
        match = pattern.search(log_content)

        if not match:
            df.loc[i, "Reason"] = "Code Issue"
            df.loc[i, "Error Message"] = "Unknown Error"
            continue

        error_text = match.group(1).strip()

        reason = "Code Issue"
        for kw in container_error_keywords:
            if kw.lower() in error_text.lower():
                reason = "Container Issue"
                break

        short_error = "Unknown Error"
        for regex, label in error_patterns.items():
            if re.search(regex, error_text, re.IGNORECASE):
                short_error = label
                break

        df.loc[i, "Reason"] = reason
        df.loc[i, "Error Message"] = short_error

    df.to_csv(RESULTS_FILE, index=False)
    log_message(project_id, "ERROR ANALYSIS", f"🔍 Error analysis updated execution results for {project_id}.")

