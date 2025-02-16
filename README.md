# gtex-react-fastapi-longetivity-vizualizer
The longetivity research where the data is taken from gtex db, processed with fastapi and visualized with react


The application provides:

Data Integration:


Fetches gene expression data from GTEx portal
Processes and standardizes the data
Handles API errors and rate limiting


Analysis Features:


Gene expression analysis across tissues
Survival analysis with Kaplan-Meier curves
Longevity predictions using Random Forest
Pathway enrichment analysis


Visualization:


Interactive charts for gene expression
Survival curves
Feature importance plots
Tissue-specific expression patterns

All pages should have the same structure: left panel with dropdown inputs and main panel with results 

1. Survival analysis
On the left panel there should be four steps for selection:
1. Gene selection
2. Tissue selection - Depends on the Gene selection and includes only tissues that contain the gene 
3. Dataset selection - Depends on the Gene and Tissue
4. Target variable selection where the target variable is a column from dataset metadata that contains from 2 to 10
unique values.
