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

| **File Name**                           | **Reproducibility Status** | **Issue/Obstacle**                                                                                                             |
|-----------------------------------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `stadyl_analyses.R`                     | $\textcolor{red}{\textsf{Not Reproducible}}$                 | Dataset path is local and not accessible in Binder.                                                                            |
| `Social_Factors_COVID-19_Konrad.R`      | <span style="color: red;">Not Reproducible</span>            | Script errors due to title and author lines not commented out.                                                                  |
| `pupillometry_tutorial_calignano.R`     | <span style="color: red;">Not Reproducible</span>            | Dataset path is local and the dataset is not programmatically downloaded.                                                      |
| `Analysis Post-PAP.R`                   | <span style="color: red;">Not Reproducible</span>            | Dataset path is local and not available on OSF.                                                                                |
| `SRMA2019_analyses.R`                   | <span style="color: yellow;">Partial Reproducible</span>     | Histogram not possible.                                                                                                            |
| `hadza_returns_model.R`                 | <span style="color: red;">Not Reproducible</span>            | Dataset unavailable on OSF.                                                                                                        |
| `stuart.R`                              | <span style="color: red;">Not Reproducible</span>            | Dataset unavailable on OSF.                                                                                                        |
| ` Psi.PS.AR.Matrix.R`                   | <span style="color: red;">Not Reproducible</span>            | Difficulties while crating the binder container.                                                                                |
| `Rcode_Figure2.R`                       | <span style="color: green;">Reproducible</span>              |
                                                                                                 |
|`Exp1-LBA-null`                          | 
|`Collaboration boosts career progression_part 1.R` | 


```diff
- test red
```

#### $\textcolor{red}{\textsf{Color test 2 .}}$

