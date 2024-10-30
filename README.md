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
| 1                 | [Social Status and Life Satisfaction: The Role of Future Expectations](https://github.com/Meet261/social_status_life_satisfaction)  | $\textcolor{red}{\textsf{Not Reproducible}}$              | Dataset path is local and not accessible in Binder.                                                                            |
| 2                 | [Social factors, pre-existing mental disorders and distress during COVID-19](https://github.com/Meet261/Social-Factors-COVID-19_Konrad)  | $\textcolor{red}{\textsf{Not Reproducible}}$                       | Script errors due to title and author lines not commented out.                                                               |
| 3                 | [BCCCD23 - Elements of Cognitive Pupillometry](https://github.com/Meet261/pupillometry_tutorial_calignano)  | $\textcolor{red}{\textsf{Not Reproducible}}$                              | Dataset path is local and the dataset is not programmatically downloaded.                                                                            |
| 4                 | [Mapping Methods in Contemporary Political Science Research: An Analysis of Journal Publications (1998 - 2018)](https://github.com/Meet261/AnalysisPost-PAP) | $\textcolor{red}{\textsf{Not Reproducible}}$                      | Dataset path is local and not available on OSF.                                                        |
| 5                 | [Strengthening the Evidence in Exercise Sciences Initiative (SEES Initiative)](https://github.com/Meet261/SRMA2019_analysis) | $\textcolor{yellow}{Partial\ Reproducible}$ | Histogram not possible.                                                                                       |
| 6                 | [The energetics of uniquely human subsistence strategies](https://osf.io/92e6c/) (File name: hadza_returns_model.R)  | $\textcolor{red}{\textsf{Not Reproducible}}$                        | Dataset (food_pro_data.csv) unavailable on OSF.           |
| 7                 | [Supplemental materials for preprint: Detecting (non)parallel evolution in multidimensional spaces: angles, correlations, and eigenanalysis](https://osf.io/6ukwg/) (Filename: stuart.R | $\textcolor{red}{\textsf{Not Reproducible}}$                         | Dataset unavailable on OSF.                                 |
| 8                 | [A systematic study into the factors that affect the predictive accuracy of multilevel VAR(1) models](https://github.com/Meet261/11682_Psi.PS.AR.Matrix) | $\textcolor{red}{\textsf{Not Reproducible}}$                            | Difficulties while creating the binder container. The R script cannot be executed because the Binder container does not generate an environment with R or RStudio.                                                                        |
| 9                 | [Ongoing and future challenges of the network approach to psychopathology: From theoretical conjectures to clinical translations](https://github.com/Meet261/Rcode_Figure2) | $\textcolor{green}{\textsf{Reproducible}}$                       | No issues.                                                |
| 10                | [Speed-Accuracy Tradeoffs In Decision Making: Perception Shifts And Goal Activation Bias Decision Thresholds](https://github.com/Meet261/Exp1-LBA-null)  | $\textcolor{red}{\textsf{Not Reproducible}}$               | The function pmwgs is not found. This could be because the required package for pmwgs is missing or not installed properly.    |                                                                                                          
| 11                | [Data and R code for: "Collaboration enhances career progression in academic science, especially for female researchers"](https://github.com/Meet261/Collaboration-boosts-career-progression_part-1) | $\textcolor{red}{\textsf{Not Reproducible}}$                       | The package r-egonet is not available in the current channels. Additionally, bibliometrix package installation is failing in Binder.   |                                                                                                                          
| 12                | [Cultural Diversity in Unequal Societies Sustained Through Cross-Cultural Competence](https://github.com/Meet261/Cultural-Diversity-in-Unequal-Societies-Sustained-Through-Cross-Cultural-Competence) | $\textcolor{green}{\textsf{Reproducible}}$                           | No issues. |
| 13       | [The influence of verb tense on mental simulation during literary reading](https://github.com/Meet261/13_The-influence-of-verb-tense-on-mental-simulation-during-literary-reading) | $\textcolor{red}{\textsf{Not Reproducible}}$                      | Datasets are available but the script is attempting to load them from a local path, making it not reproducible in Binder. |
| 14             | [Investigating the Communication-Induced Memory Bias in the Context of Third-Party Social Interactions](https://github.com/Meet261/14_Investigating-the-Communication-Induced-Memory-Bias-in-the-Context-of-Third-Party-Social) | $\textcolor{green}{\textsf{Reproducible}}$                   | No issues. |
| 15             | [Interpersonal motor synchrony in Autism: systematic review and meta-analysis](https://github.com/Meet261/15_Interpersonal-motor-synchrony-in-Autism-systematic-review-and-meta-analysis) | $\textcolor{red}{\textsf{Not Reproducible}}$                         | System dependency for librsvg-2.0 is required by the rsvg package that PRISMA2020 depends on. The issue here is that the installation of system packages like librsvg2-dev requires superuser privileges, which are not available in a Binder environment by default.|
| 16             | [The role of sensorimotor processes in social group contagion](https://github.com/Meet261/16_The-role-of-sensorimotor-processes-in-social-group-contagion)  | $\textcolor{red}{\textsf{Not Reproducible}}$                             | All libraries are getting installed successfully, but the dataset is loaded from a local path, making it inaccessible in the Binder environment. |
| 17             | [A Dictionary-Based Comparison of Autobiographies by People and Murderous Monsters](https://github.com/Meet261/17_A-Dictionary-Based-Comparison-of-Autobiographies-by-People-and-Murderous-Monsters) | $\textcolor{red}{\textsf{Not Reproducible}}$                   | The installation of the `devtools` package fails with errors related to missing shared objects (e.g., `libicui18n.so.58`), which prevents the rest of the script from running successfully. |
| 18              | [Data and code for Thompson et al. Chronology of early human impacts and ecosystem reorganisation in central Africa](https://github.com/Meet261/18_Data-and-code-for-Thompson-et-al.-Chronology-of-early-human-impacts-and-ecosystem-reorganisation) | $\textcolor{red}{\textsf{Not Reproducible}}$                        | The libraries are getting installed, but the dataset files `"20200722_lake_linterp.csv"` and `"20200722_char_linterp.csv"` are not available on OSF. |
| 19             | [Worsened self-rated health in the course of the COVID-19 pandemic among older adults in Europe](https://github.com/Meet261/19_Worsened-self-rated-health-in-the-course-of-the-COVID-19-pandemic-among-older-adults-in-Europe) | $\textcolor{red}{\textsf{Not Reproducible}}$                     | All libraries are getting installed successfully, but the dataset `share.RData`, `share8.RData`, and `share9.RData` are loaded from a local path, making it inaccessible in the Binder environment. |
| 20             | [A social motive selection model of choice in shared resource problems](https://github.com/Meet261/20_A-social-motive-selection-model-of-choice-in-shared-resource-problems) | $\textcolor{red}{\textsf{Not Reproducible}}$                            | All libraries are getting installed successfully, but the dataset `hungerAffectsSocialDecisions.csv` is loaded from a local path, making it inaccessible in the Binder environment. |
| 21                 | [A systematic study into the factors that affect the predictive accuracy of multilevel VAR(1) models](https://github.com/Meet261/21_A-systematic-study-into-the-factors-that-affect-the-predictive-accuracy-of-multilevel-VAR-1-) | $\textcolor{green}{\textsf{Reproducible}}$                     | No issue.                      |
| 22              | [Consonant co-occurrence classes and the feature-economy principle: Code and data](https://github.com/Meet261/22_Consonant-co-occurrence-classes-and-the-feature-economy-principle-Code-and-data) | $\textcolor{red}{\textsf{Not Reproducible}}$           | 1) Font Registration Issues: The script prompts for user input during the font registration process, which is not suitable for automated environments. 2) Cairo PDF Device Error: The script fails to start the cairo_pdf device, producing the error "unable to start device 'cairo_pdf'" due to output stream writing issues. 3) File Output Issues: Errors occurred during file writing, such as "could not open file 'img_new/basic_inventory_single_linkage.png'," preventing the proper output of plots and dendrograms.|
| 23             | [Do moral messages increase cooperation? Code and Data](https://github.com/Meet261/23_-Do-moral-messages-increase-cooperation-Code-and-Data) | $\textcolor{green}{\textsf{Reproducible}}$                 | No issue.       |
| 24             | [Social inequalities and loneliness as predictors of ageing well](https://github.com/Meet261/24_Social-inequalities-and-loneliness-as-predictors-of-ageing-well) | $\textcolor{red}{Not\ Reproducible}$             | Error in `.reconstruct_focal_terms(terms, model)`: object 'model3' not found.       |
| 25             | [Open Science in Marketing](https://github.com/Meet261/25_Open-Science-in-Marketing) | $\textcolor{green}{\textsf{Reproducible}}$               | No issue.       |



 

                                                                                                               
                                                                                                                                     

```diff
- test red
```

#### $\textcolor{red}{\textsf{Color test 2 .}}$


