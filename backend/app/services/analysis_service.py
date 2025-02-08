import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
from sklearn.preprocessing import StandardScaler


class AnalysisService:
    def analyze_survival(self, df: pd.DataFrame, gene: str) -> dict:
        """Perform survival analysis for a specific gene"""
        kmf = KaplanMeierFitter()

        # Split by median expression
        median_expr = df[gene].median()
        high_expr = df[gene] > median_expr

        # Fit survival curves
        kmf.fit(
            df.loc[high_expr, "time"],
            df.loc[high_expr, "event"],
            label="High Expression",
        )
        high_surv = kmf.survival_function_

        kmf.fit(
            df.loc[~high_expr, "time"],
            df.loc[~high_expr, "event"],
            label="Low Expression",
        )
        low_surv = kmf.survival_function_

        return {
            "high_expression": high_surv.reset_index().to_dict("records"),
            "low_expression": low_surv.reset_index().to_dict("records"),
        }

    def analyze_expression_patterns(self, df: pd.DataFrame) -> dict:
        """Analyze expression patterns across samples"""
        return {
            "distribution": {
                "quantiles": df["expression"].quantile([0.25, 0.5, 0.75]).to_dict(),
                "mean": df["expression"].mean(),
                "std": df["expression"].std(),
            },
            "genes": {
                gene: df[df["gene"] == gene]["expression"].describe().to_dict()
                for gene in df["gene"].unique()
            },
        }
