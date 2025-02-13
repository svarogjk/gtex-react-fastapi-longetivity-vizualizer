from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from fastapi import HTTPException
from app.utils.helpers import logger
from app.server_cache.cache_manager import cache
import httpx
from asyncio import gather


class ExpressionEndpoints:
    def __init__(self):
        self.base_url = "https://gtexportal.org/api/v2"
        self.headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        self.timeout = 30.0
        self.dataset = "gtex_v8"
        self.max_retries = 3

        # Define longevity-related genes and pathways
        self.longevity_genes = {
            "SIRT1",
            "SIRT2",
            "SIRT3",
            "SIRT4",
            "SIRT5",
            "SIRT6",
            "SIRT7",
            "FOXO1",
            "FOXO3",
            "FOXO4",
            "CDKN2A",
            "CDKN2B",
            "TERT",
            "APOE",
            "IGF1",
            "IGF1R",
            "MTOR",
            "AMPK",
            "PGC1A",
            "KLOTHO",
        }

        # Valid tissues from GTEx v8
        self.valid_tissues = {
            "WHOLE_BLOOD": "Whole_Blood",
            "LIVER": "Liver",
            "MUSCLE": "Muscle_Skeletal",
            "BRAIN": "Brain_Cortex",
            "HEART": "Heart_Left_Ventricle",
            # Add more tissue mappings as needed
        }

    async def _make_request(
        self, client: httpx.AsyncClient, url: str, params: Dict = None
    ) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await client.get(url, params=params, headers=self.headers)
                logger.info(f"Full URL: {response.url}")

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None
                elif response.status_code == 422:
                    logger.error(f"Invalid request: {response.text}")
                    return None
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        continue
                logger.error(
                    f"Request failed: {response.status_code} - {response.text}"
                )
                return None
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
        return None

    @cache.memoize(timeout=3600)
    async def get_gencode_id(self, gene_symbol: str) -> Optional[str]:
        """Get Gencode ID for a gene symbol including version"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/reference/gene"
            params = {"geneId": gene_symbol, "format": "json"}

            data = await self._make_request(client, url, params)
            if not data or "data" not in data or not data["data"]:
                return None

            gene_data = data["data"][0]
            gencode_id = gene_data.get("gencodeId")
            logger.info(f"Found Gencode ID for {gene_symbol}: {gencode_id}")
            return gencode_id

    @cache.memoize(timeout=3600)
    async def get_expression_data(
        self, genes: List[str], tissue: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch gene expression data for multiple genes"""
        try:
            normalized_tissue = self.valid_tissues.get(tissue.upper(), tissue)

            # Get Gencode IDs for all genes
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                gencode_tasks = [self.get_gencode_id(gene) for gene in genes]
                gencode_ids = await gather(*gencode_tasks)

                # Filter out None values and create gene mapping
                valid_genes = [
                    (gene, gid) for gene, gid in zip(genes, gencode_ids) if gid
                ]

                if not valid_genes:
                    logger.warning("No valid Gencode IDs found")
                    return pd.DataFrame(), pd.DataFrame()

                # Make request for expression data
                url = f"{self.base_url}/expression/geneExpression"
                params = {
                    "gencodeId": [gid for _, gid in valid_genes],
                    "tissueSiteDetailId": [normalized_tissue],
                    "datasetId": self.dataset,
                    "format": "json",
                }

                data = await self._make_request(client, url, params)

                if data and "data" in data:
                    expression_data = data["data"]
                    expression_dict = {}
                    metadata_dict = None

                    # Process each gene's data
                    for entry in expression_data:
                        gene_symbol = entry.get("geneSymbol")
                        expression_values = entry.get("data", [])
                        expression_dict[gene_symbol] = expression_values

                        # Store metadata from first entry
                        if metadata_dict is None:
                            metadata_dict = {
                                "tissue": normalized_tissue,
                                "dataset_id": entry.get("datasetId"),
                                "ontology_id": entry.get("ontologyId"),
                                "unit": entry.get("unit"),
                            }

                    if expression_dict:
                        # Create expression DataFrame
                        df_expr = pd.DataFrame(expression_dict)
                        df_expr.index = [
                            f"GTEX_SAMPLE_{i+1:04d}" for i in range(len(df_expr))
                        ]
                        df_expr.index.name = "sample_id"
                        df_expr = df_expr.reset_index()

                        # Create metadata DataFrame
                        df_meta = pd.DataFrame(
                            [
                                {**metadata_dict, "sample_id": sample_id}
                                for sample_id in df_expr["sample_id"]
                            ]
                        )

                        return df_expr, df_meta

                logger.warning("No expression data received")
                return pd.DataFrame(), pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting expression data: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    @cache.memoize(timeout=3600)
    async def analyze_longevity_patterns(self, genes: List[str], tissue: str) -> Dict:
        """Analyze expression patterns in context of longevity"""
        try:
            df_expr, df_meta = await self.get_expression_data(genes, tissue)

            if df_expr.empty:
                return {"status": "error", "message": "No expression data available"}

            # Identify longevity-related genes
            longevity_genes = set(genes) & self.longevity_genes

            # Calculate correlations
            gene_cols = [col for col in df_expr.columns if col != "sample_id"]
            correlations = df_expr[gene_cols].corr().round(3)

            # Calculate basic statistics
            stats = {}
            for gene in gene_cols:
                stats[gene] = {
                    "mean": float(df_expr[gene].mean()),
                    "std": float(df_expr[gene].std()),
                    "median": float(df_expr[gene].median()),
                    "is_longevity_related": gene in self.longevity_genes,
                }

            # Perform pathway analysis if longevity genes present
            pathway_analysis = {}
            if longevity_genes:
                # Example pathway scores (simplified)
                pathways = {
                    "aging": longevity_genes & {"SIRT1", "FOXO3", "CDKN2A"},
                    "stress_response": longevity_genes & {"FOXO3", "SIRT1"},
                    "metabolism": longevity_genes & {"AMPK", "MTOR", "IGF1R"},
                }

                for pathway, genes in pathways.items():
                    if genes:
                        pathway_analysis[pathway] = {
                            "genes": list(genes),
                            "score": len(genes) / len(longevity_genes),
                        }

            return {
                "status": "success",
                "data": {
                    "longevity_analysis": {
                        "longevity_genes_found": list(longevity_genes),
                        "pathway_analysis": pathway_analysis,
                        "gene_stats": stats,
                        "correlations": correlations.to_dict(),
                    },
                    "metadata": {
                        "tissue": tissue,
                        "total_genes": len(genes),
                        "longevity_genes_count": len(longevity_genes),
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error in longevity analysis: {str(e)}")
            return {"status": "error", "message": str(e)}

    @cache.memoize(timeout=3600)
    async def get_available_tissues(self) -> Dict[str, List[str]]:
        """Get list of available tissues with categories"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/reference/tissue"
                data = await self._make_request(
                    client, url, {"datasetId": self.dataset}
                )

                if not data or "data" not in data:
                    return {"tissues": [], "categories": {}}

                tissues = data["data"]

                # Organize tissues by category
                categories = {}
                tissue_list = []

                for tissue in tissues:
                    tissue_id = tissue.get("tissueSiteDetailId")
                    category = tissue.get("tissueSiteDetail", "Other")

                    if tissue_id:
                        tissue_list.append(tissue_id)
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(tissue_id)

                return {"tissues": sorted(tissue_list), "categories": categories}

        except Exception as e:
            logger.error(f"Error getting tissues: {str(e)}")
            return {"tissues": [], "categories": {}}

    @cache.memoize(timeout=3600)
    async def get_tissue_expression_summary(self, gene: str) -> Dict:
        """Get expression summary across all tissues for a gene"""
        try:
            tissues = await self.get_available_tissues()
            tissue_list = tissues["tissues"][:5]  # Limit to 5 tissues for example

            results = []
            for tissue in tissue_list:
                df_expr, _ = await self.get_expression_data([gene], tissue)
                if not df_expr.empty and gene in df_expr.columns:
                    results.append(
                        {
                            "tissue": tissue,
                            "mean_expression": float(df_expr[gene].mean()),
                            "median_expression": float(df_expr[gene].median()),
                            "std_expression": float(df_expr[gene].std()),
                        }
                    )

            return {
                "status": "success",
                "data": {"gene": gene, "tissue_expression": results},
            }

        except Exception as e:
            logger.error(f"Error getting tissue expression summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def process_expression_data(
        self, df_expr: pd.DataFrame, df_meta: pd.DataFrame
    ) -> Dict:
        """Process expression data and generate response"""
        if df_expr.empty or df_meta.empty:
            return {
                "status": "no_data",
                "message": "No expression data found",
                "data": {"expression": [], "metadata": []},
            }

        # Calculate summary statistics
        gene_stats = {}
        for gene in [col for col in df_expr.columns if col != "sample_id"]:
            gene_stats[gene] = {
                "mean": float(df_expr[gene].mean()),
                "median": float(df_expr[gene].median()),
                "std": float(df_expr[gene].std()),
                "min": float(df_expr[gene].min()),
                "max": float(df_expr[gene].max()),
                "is_longevity_related": gene in self.longevity_genes,
            }

        # Calculate gene correlations
        genes = [col for col in df_expr.columns if col != "sample_id"]
        correlations = {}
        if len(genes) > 1:
            corr_matrix = df_expr[genes].corr().round(3)
            correlations = corr_matrix.to_dict()

        return {
            "status": "success",
            "message": "Expression data retrieved successfully",
            "data": {
                "expression": df_expr.to_dict(orient="records"),
                "metadata": df_meta.to_dict(orient="records"),
                "summary": {
                    "n_samples": len(df_meta),
                    "n_genes": len(genes),
                    "tissue": df_meta["tissue"].iloc[0],
                    "unit": df_meta["unit"].iloc[0],
                    "gene_stats": gene_stats,
                    "correlations": correlations,
                },
            },
        }


expression_endpoints = ExpressionEndpoints()
