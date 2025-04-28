# app/services/analysis_service.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from lifelines import KaplanMeierFitter, CoxPHFitter
from typing import Dict, Any

from app.api.endpoints.expression import expression_endpoints


class AnalysisService:

    def __init__(self):
        self.kmf = KaplanMeierFitter()
        self.cph = CoxPHFitter()
        self.le_hardy = LabelEncoder()

    async def prepare_survival_data(self, gene: str, tissue: str) -> pd.DataFrame:
        df_expr, _ = await expression_endpoints.get_expression_data([gene], tissue)
        df_expr["subject_id"] = (
            df_expr["sample_id"].str.split("-").str[:2].str.join("-")
        )
        df_expr = df_expr.groupby("subject_id", as_index=False).agg({gene: "mean"})
        metadata = await expression_endpoints.get_dataset_metadata("gtex_v8")
        df_meta = pd.DataFrame(metadata)
        df_meta["hardy_numeric"] = self.le_hardy.fit_transform(df_meta["hardyScale"])
        df_meta[["age_low", "age_high"]] = (
            df_meta["ageBracket"].str.split("-", expand=True).astype(int)
        )
        df_meta["time"] = (df_meta["age_low"] + df_meta["age_high"]) / 2
        df_data = df_expr.merge(
            df_meta, how="inner", left_on="subject_id", right_on="subjectId"
        )
        df_data["event"] = 1
        median_expr = df_data["gene"].median()
        df_data["group_by_median"] = np.where(
            df_data[gene] > median_expr, "High", "Low"
        )
        return df_data
