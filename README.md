# CodeInspector
Task 2.4: Browser-based Reproducibility and Evaluation

# Overview
CodeInspector provides researchers with an accessible, browser-based environment to ensure the reproducibility of statistical analyses. This project is part of a broader initiative aimed at enhancing the reproducibility of research by automating the evaluation of R-based statistical codes and their dependencies.

By leveraging Binder-ready repositories and Docker containers, researchers can execute enriched code directly within the browser, without needing to manually install dependencies. This service is powered by GESIS Notebooks, providing a seamless and efficient platform for reproducibility.

# Project Goals
**Dependency Resolution:** We resolve package dependencies from the R ecosystem and data dependencies, ensuring all requirements are fully specified.
Containerization: The resolved dependencies are integrated into Docker images, enabling browser-based code execution.
Evaluation: Code reproducibility is evaluated by:
Verifying all package and data dependencies are identified.
Checking that analyses are fully executable.
Confirming that the published codes reproduce the original results.
The project follows the FAIR principles (Findable, Accessible, Interoperable, Reusable), facilitating researchers' ability to investigate statistical analysis codes efficiently.

# Code Files and Dependencies
Each code file is paired with a Binder container, which includes:

**environment.yml:** Specifies the environment dependencies, ensuring reproducibility of the code.
postBuild: A script for downloading datasets and additional dependencies.
Data files: Automatically downloaded and linked during the setup process.
These containers allow the original code to be run without modification, ensuring faithful replication of the analysis.

### Code Reproducibility Tracker

| **Serial Number** | **File Name**                           | **Reproducibility Status** | **Issue/Obstacle**                                                                                                             |
|-------------------|-----------------------------------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| 1                 | Social Status and Life Satisfaction: The Role of Future Expectations  | $\textcolor{red}{\textsf{Not Reproducible}}$  | Dataset path is local and not accessible in Binder.                                                                                                              |
| 2                 | Social factors, pre-existing mental disorders and distress during COVID-19  | $\textcolor{red}{\textsf{Not Reproducible}}$  | Script errors due to title and author lines not commented out.                                                                                          |
| 3                 | BCCCD23 - Elements of Cognitive Pupillometry  | $\textcolor{red}{\textsf{Not Reproducible}}$             | Dataset path is local and the dataset is not programmatically downloaded.                                                                                                      |
| 4                 | Mapping Methods in Contemporary Political Science Research: An Analysis of Journal Publications (1998 - 2018) | $\textcolor{red}{\textsf{Not Reproducible}}$             | Dataset path is local and not available on OSF.                                                        |
| 5                 | Strengthening the Evidence in Exercise Sciences Initiative (SEES Initiative) | $\textcolor{yellow}{\textsf{Partially Reproducible}}$   | Histogram not possible.                                                                                                                           |
| 6                 | The energetics of uniquely human subsistence strategies  | $\textcolor{red}{\textsf{Not Reproducible}}$ | Dataset unavailable on OSF.           |
| 7                 | Supplemental materials for preprint: Detecting (non)parallel evolution in multidimensional spaces: angles, correlations, and eigenanalysis | $\textcolor{red}{\textsf{Not Reproducible}}$ | Dataset unavailable on OSF.                                                                      |
| 8                 | A systematic study into the factors that affect the predictive accuracy of multilevel VAR(1) models | $\textcolor{red}{\textsf{Not Reproducible}}$             | Difficulties while creating the binder container. The R script cannot be executed because the Binder container does not generate an environment with R or RStudio.                                                                                               |
| 9                 | Ongoing and future challenges of the network approach to psychopathology: From theoretical conjectures to clinical translations | $\textcolor{green}{\textsf{Reproducible}}$   | No issues.                                                                                         |
| 10                | Speed-Accuracy Tradeoffs In Decision Making: Perception Shifts And Goal Activation Bias Decision Thresholds  | $\textcolor{red}{\textsf{Not Reproducible}}$   | The function pmwgs is not found. This could be because the required package for pmwgs is missing or not installed properly.    |                                                                                                          
| 11                | Data and R code for: "Collaboration enhances career progression in academic science, especially for female researchers" | $\textcolor{red}{\textsf{Not Reproducible}}$ | The package r-egonet is not available in the current channels. Additionally, bibliometrix package installation is failing in Binder.   |                                                                                                                          
| 12                | 'Cultural Diversity in Unequal Societies Sustained Through Cross-Cultural Competence'| $\textcolor{green}{\textsf{Reproducible}}$ | No issues. |
| 13       | The influence of verb tense on mental simulation during literary reading | $\textcolor{red}{\textsf{Not Reproducible}}$ | Datasets are available but the script is attempting to load them from a local path, making it not reproducible in Binder. |

                                                                                                               
                                                                                                                                     

```diff
- test red
```

#### $\textcolor{red}{\textsf{Color test 2 .}}$

