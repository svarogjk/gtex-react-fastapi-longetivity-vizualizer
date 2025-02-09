# app/services/analysis_service.py
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any


class AnalysisService:
    def analyze_survival(self, df: pd.DataFrame, gene: str) -> Dict[str, Any]:
        """Perform survival analysis"""
        kmf = KaplanMeierFitter()

        # Split by median expression
        median_expr = df[gene].median()
        high_expr = df[gene] > median_expr

        results = {}

        # High expression group
        kmf.fit(
            df.loc[high_expr, "time"],
            df.loc[high_expr, "event"],
            label="High Expression",
        )
        results["high_expression"] = {
            "survival": kmf.survival_function_.to_dict(),
            "median": kmf.median_survival_time_,
        }

        # Low expression group
        kmf.fit(
            df.loc[~high_expr, "time"],
            df.loc[~high_expr, "event"],
            label="Low Expression",
        )
        results["low_expression"] = {
            "survival": kmf.survival_function_.to_dict(),
            "median": kmf.median_survival_time_,
        }

        return results

    def analyze_expression_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze expression patterns"""
        return {
            "distribution": df["expression"].describe().to_dict(),
            "correlations": df.pivot(columns="gene", values="expression")
            .corr()
            .to_dict(),
        }
