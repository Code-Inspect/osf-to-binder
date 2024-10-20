# Load necessary libraries
if (!require("haven")) {
    install.packages("haven", repos = "http://cran.us.r-project.org")
}
if (!require("httr")) {
    install.packages("httr", repos = "http://cran.us.r-project.org")
}

# Function to download and save the dataset
import_and_save_data <- function(file_path = "data/StadyL_Study2.sav") {
    # Create data directory if it doesn't exist
    if (!dir.exists("data")) {
        dir.create("data")
    }

    # Define the URL of the dataset
    data_url <- "https://osf.io/r4wg2/download"

    # Download the dataset if not already saved
    if (!file.exists(file_path)) {
        response <- GET(data_url)
        
        # Check if the file type is correct (SPSS .sav file)
        if (http_type(response) == "application/octet-stream") {
            # Save the file to the local path
            writeBin(content(response, "raw"), file_path)
            message("Data has been downloaded and saved to: ", file_path)
        } else {
            stop("The file downloaded is not in SPSS .sav format. Please check the source URL.")
        }
    } else {
        message("Data already exists at: ", file_path)
    }

    # Load the dataset into R using haven and return it
    data <- haven::read_sav(file_path)
    return(data)
}
