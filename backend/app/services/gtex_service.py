import pandas as pd
import numpy as np
import requests
from typing import List
from fastapi import HTTPException


class GTExService:
    def __init__(self):
        self.base_url = "https://gtexportal.org/rest/v1"

    async def get_expression_data(self, genes: List[str], tissue: str) -> pd.DataFrame:
        """Fetch and process GTEx expression data"""
        try:
            response = requests.post(
                f"{self.base_url}/expression/medianGeneExpression",
                headers={"Accept": "application/json"},
                json={
                    "geneId": genes,
                    "tissueSiteDetailId": tissue,
                    "datasetId": "gtex_v8",
                },
            )
            response.raise_for_status()

            # Convert to DataFrame
            df = pd.DataFrame(response.json()["data"])
            return df

        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=str(e))

    def process_expression_data(self, df: pd.DataFrame) -> dict:
        """Process expression data and return statistics"""
        if df.empty:
            return {}

        return {
            "summary": {
                "mean": df["expression"].mean(),
                "median": df["expression"].median(),
                "std": df["expression"].std(),
            },
            "expression_by_gene": df.groupby("gene")["expression"]
            .agg(["mean", "median", "std"])
            .to_dict("index"),
        }
