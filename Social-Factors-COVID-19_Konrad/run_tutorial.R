# Loading necessary libraries
library(httr)     # For downloading files from URLs
library(readr)    # For reading the data

# Define the URL of the dataset
url <- "https://osf.io/r8gmc/download"

# Define the file path where the dataset will be saved
destfile <- "data_Konrad_etal.csv"

# Download the file
download.file(url, destfile, method = "curl")

# Check if the file was downloaded successfully
if (file.exists(destfile)) {
  print("Dataset downloaded successfully.")
  
  # Load the dataset to verify the content (optional step)
  data <- read_csv(destfile)
  print(head(data))
} else {
  print("Failed to download the dataset.")
}
