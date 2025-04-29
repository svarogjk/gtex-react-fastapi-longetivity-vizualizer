# app/services/analysis_service.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
from typing import Dict, Any
from app.utils.helpers import logger
from app.api.endpoints.expression import expression_endpoints


class SurvivalAnalysisService:

    def __init__(self):
        self.kmf = KaplanMeierFitter()
        self.cph = CoxPHFitter()
        self.le_hardy = LabelEncoder()

    def find_optimal_cutpoint(
        self,
        df,
        gene_col,
        time_col="time",
        event_col="event",
        method="maxstat",
        min_prop=0.1,
        max_prop=0.9,
    ):
        """
        Find the optimal cutpoint for gene expression that best separates survival curves

        Parameters:
        df: DataFrame containing the data
        gene_col: Column containing gene expression values
        time_col: Column containing survival times
        event_col: Column containing event indicators (0=censored, 1=event)
        method: Method to use ('logrank' or 'maxstat')
        min_prop: Minimum proportion of samples in either group
        max_prop: Maximum proportion of samples in either group

        Returns:
        optimal_cutpoint: The optimal cutpoint value
        statistic: The test statistic at the optimal cutpoint
        p_value: The p-value at the optimal cutpoint
        """
        gene_values = np.unique(df[gene_col].dropna())
        if len(gene_values) < 5:
            logger.warning(
                f"Too few distinct values ({len(gene_values)}) for optimal cutpoint, using median instead"
            )
            median_value = float(df[gene_col].median())
            return (
                median_value,
                None,
                1.0,
            )  # Return median with p-value=1 to indicate fallback

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
