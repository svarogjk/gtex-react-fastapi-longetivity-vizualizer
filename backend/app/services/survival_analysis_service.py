# app/services/analysis_service.py
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
from typing import Dict, Any
from app.utils.helpers import logger
from app.api.endpoints.expression import expression_endpoints


class SurvivalAnalysisService:

    def __init__(self):
        self.kmf = KaplanMeierFitter()
        self.cph = CoxPHFitter()

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
        n_cutpoints = min(len(gene_values), 100)
        percentiles = np.linspace(min_prop * 100, max_prop * 100, n_cutpoints)
        potential_cutpoints = np.percentile(gene_values, percentiles)
        results = []
        min_group_size = max(2, int(len(df) * min_prop))
        for cutpoint in potential_cutpoints:
            is_high = df[gene_col] > cutpoint
            high_num = is_high.sum()
            low_num = len(df) - high_num
            if high_num < min_group_size or low_num < min_group_size:
                continue
            high_idx = df.index[is_high]
            low_idx = df.index[~is_high]
            high_times = df.loc[high_idx, time_col]
            high_events = df.loc[high_idx, event_col]
            low_times = df.loc[low_idx, time_col]
            low_events = df.loc[low_idx, event_col]
            lr_result = logrank_test(high_times, low_times, high_events, low_events)
            if method == "logrank":
                stat_value = -lr_result.p_value
            else:
                stat_value = lr_result.test_statistic
            results.append((cutpoint, stat_value, lr_result.p_value))
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        best_result = sorted_results[0]
        if best_result[2] > 0.05:  # p-value threshold
            logger.info(
                f"No statistically significant cutpoint found (best p-value: {best_result[2]:.4f}), using median instead"
            )
            median_value = float(df[gene_col].median())
            return (
                median_value,
                None,
                1.0,
            )  # Return median with p-value=1 to indicate fallback

        return best_result[0], best_result[1], best_result[2]

    async def prepare_survival_data(self, gene: str, tissue: str) -> pd.DataFrame:
        df_expr, _ = await expression_endpoints.get_expression_data([gene], tissue)
        df_meta = await expression_endpoints.get_sample_metadata("gtex_v8", tissue)
        df_data = pd.concat([df_expr, df_meta], axis=1)
        df_data["event"] = 1
        optimal_cutpoint, test_stat, p_value = self.find_optimal_cutpoint(
            df_data, gene, time_col="time", event_col="event", method="maxstat"
        )
        if p_value == 1.0:  # This indicates we're using the fallback median
            cutpoint_value = optimal_cutpoint  # This is actually the median
            cutpoint_type = "median"
            logger.info(f"Using median as cutpoint for {gene}: {cutpoint_value}")
        else:
            cutpoint_value = optimal_cutpoint
            cutpoint_type = "optimal"
        df_data["expression_group"] = np.where(
            df_data[gene] > cutpoint_value, "High", "Low"
        )
        df_data["cutpoint_value"] = cutpoint_value
        df_data["cutpoint_type"] = cutpoint_type
        return df_data

    async def perform_kaplan_meier_analysis(
        self, gene: str, tissue: str
    ) -> Dict[str, Any]:
        """
        Perform Kaplan-Meier survival analysis based on gene expression levels
        using optimal cutpoint stratification
        """
        df = await self.prepare_survival_data(gene, tissue)
        cutpoint_value = float(df["cutpoint_value"].iloc[0])
        cutpoint_type = df["cutpoint_type"].iloc[0]
        high_expr_mask = df["expression_group"] == "High"
        low_expr_mask = df["expression_group"] == "Low"
        results = {
            "metadata": {
                "gene": gene,
                "tissue": tissue,
                "sample_count": len(df),
                "high_expr_count": sum(high_expr_mask),
                "low_expr_count": sum(low_expr_mask),
                "median_expression": float(df[gene].median()),
                "cutpoint": {
                    "value": cutpoint_value,
                    "type": cutpoint_type,
                    "high_expression_definition": f"> {cutpoint_value:.4f} TPM",
                    "low_expression_definition": f"≤ {cutpoint_value:.4f} TPM",
                    "percent_high": float((df[gene] > cutpoint_value).mean() * 100),
                    "percent_low": float((df[gene] <= cutpoint_value).mean() * 100),
                },
            }
        }

        self.kmf.fit(
            df.loc[high_expr_mask, "time"],
            df.loc[high_expr_mask, "event"],
            label="High Expression",
        )
        high_expr_survival = self.kmf.survival_function_.reset_index()
        high_expr_survival.columns = ["time", "survival_probability"]
        results["high_expression"] = {
            "survival_curve": high_expr_survival.to_dict(orient="records"),
            "median_survival": (
                float(self.kmf.median_survival_time_)
                if hasattr(self.kmf, "median_survival_time_")
                else None
            ),
            "min_time": (
                float(high_expr_survival["time"].min())
                if not high_expr_survival.empty
                else None
            ),
            "max_time": (
                float(high_expr_survival["time"].max())
                if not high_expr_survival.empty
                else None
            ),
        }
        self.kmf.fit(
            df.loc[low_expr_mask, "time"],
            df.loc[low_expr_mask, "event"],
            label="Low Expression",
        )
        low_expr_survival = self.kmf.survival_function_.reset_index()
        low_expr_survival.columns = ["time", "survival_probability"]

        results["low_expression"] = {
            "survival_curve": low_expr_survival.to_dict(orient="records"),
            "median_survival": (
                float(self.kmf.median_survival_time_)
                if hasattr(self.kmf, "median_survival_time_")
                else None
            ),
            "min_time": (
                float(low_expr_survival["time"].min())
                if not low_expr_survival.empty
                else None
            ),
            "max_time": (
                float(low_expr_survival["time"].max())
                if not low_expr_survival.empty
                else None
            ),
        }
        results["statistical_analysis"] = {}

        high_times = df.loc[high_expr_mask, "time"]
        high_events = df.loc[high_expr_mask, "event"]
        low_times = df.loc[low_expr_mask, "time"]
        low_events = df.loc[low_expr_mask, "event"]
        logrank_result = logrank_test(high_times, low_times, high_events, low_events)
        results["statistical_analysis"]["logrank_test"] = {
            "p_value": float(logrank_result.p_value),
            "test_statistic": float(logrank_result.test_statistic),
            "is_significant": logrank_result.p_value < 0.05,
        }
        # Cox Proportional Hazard models
        df["gene_expression"] = df[gene]
        df["high_expression_group"] = high_expr_mask.astype(int)
        df["sex_male"] = (df["sex"] == "male").astype(int)
        self.cph.fit(
            df[["time", "event", "gene_expression", "sex_male", "hardy_numeric"]],
            duration_col="time",
            event_col="event",
        )
        continuous_cox_summary = self.cph.summary
        cph_binary = CoxPHFitter()
        cph_binary.fit(
            df[["time", "event", "high_expression_group", "sex_male", "hardy_numeric"]],
            duration_col="time",
            event_col="event",
        )
        binary_cox_summary = cph_binary.summary
        results["statistical_analysis"]["cox_models"] = {
            "continuous_expression": {
                "gene_expression_coef": float(
                    continuous_cox_summary.loc["gene_expression", "coef"]
                ),
                "gene_expression_p_value": float(
                    continuous_cox_summary.loc["gene_expression", "p"]
                ),
                "gene_expression_hazard_ratio": float(
                    np.exp(continuous_cox_summary.loc["gene_expression", "coef"])
                ),
                "gene_expression_is_significant": float(
                    continuous_cox_summary.loc["gene_expression", "p"]
                )
                < 0.05,
                "covariates": {
                    "sex_male": {
                        "coef": float(continuous_cox_summary.loc["sex_male", "coef"]),
                        "p_value": float(continuous_cox_summary.loc["sex_male", "p"]),
                        "hazard_ratio": float(
                            np.exp(continuous_cox_summary.loc["sex_male", "coef"])
                        ),
                    },
                    "hardy_numeric": {
                        "coef": float(
                            continuous_cox_summary.loc["hardy_numeric", "coef"]
                        ),
                        "p_value": float(
                            continuous_cox_summary.loc["hardy_numeric", "p"]
                        ),
                        "hazard_ratio": float(
                            np.exp(continuous_cox_summary.loc["hardy_numeric", "coef"])
                        ),
                    },
                },
                "model_quality": {
                    "concordance": float(self.cph.concordance_index_),
                    "log_likelihood": float(self.cph.log_likelihood_),
                    "aic": float(self.cph.AIC_),
                },
            },
            "binary_expression_group": {
                "high_expression_group_coef": float(
                    binary_cox_summary.loc["high_expression_group", "coef"]
                ),
                "high_expression_group_p_value": float(
                    binary_cox_summary.loc["high_expression_group", "p"]
                ),
                "high_expression_group_hazard_ratio": float(
                    np.exp(binary_cox_summary.loc["high_expression_group", "coef"])
                ),
                "high_expression_group_is_significant": float(
                    binary_cox_summary.loc["high_expression_group", "p"]
                )
                < 0.05,
                "covariates": {
                    "sex_male": {
                        "coef": float(binary_cox_summary.loc["sex_male", "coef"]),
                        "p_value": float(binary_cox_summary.loc["sex_male", "p"]),
                        "hazard_ratio": float(
                            np.exp(binary_cox_summary.loc["sex_male", "coef"])
                        ),
                    },
                    "hardy_numeric": {
                        "coef": float(binary_cox_summary.loc["hardy_numeric", "coef"]),
                        "p_value": float(binary_cox_summary.loc["hardy_numeric", "p"]),
                        "hazard_ratio": float(
                            np.exp(binary_cox_summary.loc["hardy_numeric", "coef"])
                        ),
                    },
                },
                "model_quality": {
                    "concordance": float(cph_binary.concordance_index_),
                    "log_likelihood": float(cph_binary.log_likelihood_),
                    "aic": float(cph_binary.AIC_),
                },
            },
        }
        gene_effect = continuous_cox_summary.loc["gene_expression", "coef"]
        is_significant = continuous_cox_summary.loc["gene_expression", "p"] < 0.05

        if is_significant:
            if gene_effect < 0:
                interpretation = f"Higher expression of {gene} is significantly associated with improved survival outcomes."
            else:
                interpretation = f"Higher expression of {gene} is significantly associated with worse survival outcomes."
        else:
            interpretation = f"Expression of {gene} does not show a statistically significant association with survival in this tissue."

        results["interpretation"] = interpretation
        return results

    async def analyze_gene_set_survival(
        self, genes: list[str], tissue: str
    ) -> dict[str, Any]:
        """
        Perform survival analysis on a set of genes
        """
        results = {}
        for gene in genes:
            gene_result = await self.perform_kaplan_meier_analysis(gene, tissue)
            results[gene] = gene_result
        significant_genes_continuous = []
        significant_genes_binary = []
        protective_genes = []
        risk_genes = []
        for gene, data in results.items():
            if (
                "statistical_analysis" in data
                and "cox_models" in data["statistical_analysis"]
                and "continuous_expression"
                in data["statistical_analysis"]["cox_models"]
                and "gene_expression_is_significant"
                in data["statistical_analysis"]["cox_models"]["continuous_expression"]
                and data["statistical_analysis"]["cox_models"]["continuous_expression"][
                    "gene_expression_is_significant"
                ]
            ):

                significant_genes_continuous.append(gene)
                coef = data["statistical_analysis"]["cox_models"][
                    "continuous_expression"
                ]["gene_expression_coef"]
                if coef < 0:
                    protective_genes.append(gene)
                else:
                    risk_genes.append(gene)
            if (
                "statistical_analysis" in data
                and "cox_models" in data["statistical_analysis"]
                and "binary_expression_group"
                in data["statistical_analysis"]["cox_models"]
                and "high_expression_group_is_significant"
                in data["statistical_analysis"]["cox_models"]["binary_expression_group"]
                and data["statistical_analysis"]["cox_models"][
                    "binary_expression_group"
                ]["high_expression_group_is_significant"]
            ):
                significant_genes_binary.append(gene)
            cutpoint_info = {}
        for gene, data in results.items():
            if "metadata" in data and "cutpoint" in data["metadata"]:
                cutpoint_info[gene] = {
                    "value": data["metadata"]["cutpoint"]["value"],
                    "type": data["metadata"]["cutpoint"]["type"],
                }
        summary = {
            "total_genes_analyzed": len(genes),
            "successful_analyses": sum(1 for gene, data in results.items()),
            "significant_genes": {
                "continuous_model": significant_genes_continuous,
                "continuous_count": len(significant_genes_continuous),
                "binary_model": significant_genes_binary,
                "binary_count": len(significant_genes_binary),
            },
            "functional_groups": {
                "protective_genes": protective_genes,
                "risk_genes": risk_genes,
            },
            "cutpoints": cutpoint_info,
            "tissue": tissue,
        }
        return {"gene_results": results, "summary": summary}
