# Clean the R environment
rm(list = ls())

# Install the required packages if they are not already installed
required_packages <- c("dplyr", "naniar", "plyr", "mgcv", "itsadug", "sjPlot")

# Install missing packages
installed_packages <- installed.packages()
for (pkg in required_packages) {
  if (!(pkg %in% installed_packages)) {
    install.packages(pkg)
  }
}

# Load the required libraries
library(dplyr)
library(naniar)
library(plyr)
library(mgcv)
library(itsadug)
library(sjPlot)

# Set working directory - Update this to your actual working directory
#setwd("~Downloads")

# Download the dataset from OSF if it's not available locally
dataset_path <- "dataset_tutorial.csv"
if (!file.exists(dataset_path)) {
  download.file("https://osf.io/6ke4y/download", destfile = dataset_path)
}

# The environment is now ready to run the original code
print("Environment setup complete. You can now run the original code.")
