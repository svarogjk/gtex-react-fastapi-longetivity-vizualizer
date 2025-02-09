import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api"


# Test Expression Analysis
def test_expression_endpoint():
    # Get expression data for specific genes in blood tissue
    response = requests.get(
        f"{BASE_URL}/expression/genes/WHOLE_BLOOD",
        params={"genes": ["SIRT1", "FOXO3", "CDKN2A"], "tissue": "WHOLE_BLOOD"},
    )
    print("Expression Analysis Results:")
    print(json.dumps(response.json(), indent=2))


# Test Survival Analysis
def test_survival_endpoint():
    # Get survival analysis for SIRT1
    response = requests.get(f"{BASE_URL}/survival/SIRT1")
    print("\nSurvival Analysis Results:")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    test_expression_endpoint()
    test_survival_endpoint()
