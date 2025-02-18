from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np
from fastapi import HTTPException
from app.utils.helpers import logger
from app.server_cache.cache_manager import cache
from app.services.search_service import SearchService
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
            "WHOLE_BLOOD": "Whole Blood",
            "LIVER": "Liver",
            "MUSCLE_SKELETAL": "Skeletal Muscle",
            "BRAIN_CORTEX": "Brain Cortex",
            "HEART_LEFT_VENTRICLE": "Heart Left Ventricle",
            "LUNG": "Lung",
            "KIDNEY_CORTEX": "Kidney Cortex",
            "ADIPOSE_SUBCUTANEOUS": "Subcutaneous Adipose",
            "SKIN_SUN_EXPOSED": "Sun-Exposed Skin",
            "THYROID": "Thyroid",
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
    async def get_available_tissues(self) -> Dict[str, Any]:
        """Get list of available tissues with categories"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/reference/tissue"
                data = await self._make_request(
                    client, url, {"datasetId": self.dataset}
                )

                if not data or "data" not in data:
                    return {
                        "tissues": list(self.valid_tissues.keys()),
                        "categories": {},
                    }

                # Process tissue data and organize by category
                categories = {}
                for tissue_id, display_name in self.valid_tissues.items():
                    category = self._get_tissue_category(tissue_id)
                    if category not in categories:
                        categories[category] = []
                    categories[category].append({"id": tissue_id, "name": display_name})

                return {
                    "tissues": list(self.valid_tissues.keys()),
                    "categories": categories,
                }

        except Exception as e:
            logger.error(f"Error getting tissues: {str(e)}")
            return {"tissues": [], "categories": {}}

    def _get_tissue_category(self, tissue_id: str) -> str:
        """Get category for a tissue based on its ID"""
        categories = {
            "BRAIN": "Brain",
            "HEART": "Cardiovascular",
            "MUSCLE": "Muscle",
            "ADIPOSE": "Fat",
            "SKIN": "Skin",
            "BLOOD": "Blood",
            "LIVER": "Digestive",
            "KIDNEY": "Urinary",
            "LUNG": "Respiratory",
            "THYROID": "Endocrine",
        }

        for key, category in categories.items():
            if key in tissue_id:
                return category
        return "Other"

    @cache.memoize(timeout=3600)
    async def get_tissue_expression_summary(self, gene: str) -> Dict:
        """Get expression summary across tissues for a gene"""
        try:
            # Get Gencode ID for the gene
            gencode_id = await self.get_gencode_id(gene)

            if not gencode_id:
                logger.error(f"Could not find Gencode ID for gene {gene}")
                return {
                    "status": "error",
                    "message": f"Gene {gene} not found",
                    "data": {"gene": gene, "tissue_expression": []},
                }

            logger.info(f"Found Gencode ID for {gene}: {gencode_id}")
            available_tissues = list(self.valid_tissues.keys())

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get expression data for all tissues
                url = f"{self.base_url}/expression/medianGeneExpression"  # Changed endpoint
                params = {
                    "gencodeId": [gencode_id],
                    "tissueSiteDetailId": available_tissues,
                    "datasetId": self.dataset,
                    "format": "json",
                }

                logger.info(f"Requesting expression data with params: {params}")
                data = await self._make_request(client, url, params)

                if not data:
                    logger.error("No response data received")
                    return {
                        "status": "error",
                        "message": "No response from expression service",
                        "data": {"gene": gene, "tissue_expression": []},
                    }

                if "data" not in data or not data["data"]:
                    logger.error(f"No expression data found in response: {data}")
                    return {
                        "status": "error",
                        "message": "No expression data found",
                        "data": {"gene": gene, "tissue_expression": []},
                    }

                # Process expression data
                tissue_expression = []
                for tissue_data in data["data"]:
                    tissue_id = tissue_data.get("tissueSiteDetailId")
                    median_expression = tissue_data.get("median")

                    if (
                        tissue_id in self.valid_tissues
                        and median_expression is not None
                    ):
                        tissue_expression.append(
                            {
                                "tissue": tissue_id,
                                "display_name": self.valid_tissues[tissue_id],
                                "median_expression": float(median_expression),
                            }
                        )

                # Sort tissues by median expression
                tissue_expression.sort(
                    key=lambda x: x["median_expression"], reverse=True
                )

                if not tissue_expression:
                    logger.warning(
                        f"No valid tissue expression data found for gene {gene}"
                    )
                    return {
                        "status": "error",
                        "message": "No tissue expression data found",
                        "data": {"gene": gene, "tissue_expression": []},
                    }

                return {
                    "status": "success",
                    "data": {
                        "gene": gene,
                        "gencode_id": gencode_id,
                        "tissue_expression": tissue_expression,
                    },
                }

        except Exception as e:
            logger.error(f"Error getting tissue expression summary: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "data": {"gene": gene, "tissue_expression": []},
            }

    async def get_gencode_id(self, gene_symbol: str) -> Optional[str]:
        """Get Gencode ID for a gene symbol including version"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/reference/gene"
                params = {
                    "geneSymbol": gene_symbol,
                    "format": "json",
                }  # Changed from geneId to geneSymbol

                logger.info(f"Requesting Gencode ID for gene {gene_symbol}")
                data = await self._make_request(client, url, params)

                if not data or "data" not in data or not data["data"]:
                    logger.warning(f"No Gencode ID found for gene {gene_symbol}")
                    return None

                gene_data = data["data"][0]
                gencode_id = gene_data.get("gencodeId")
                logger.info(f"Found Gencode ID for {gene_symbol}: {gencode_id}")
                return gencode_id

        except Exception as e:
            logger.error(f"Error getting Gencode ID for {gene_symbol}: {str(e)}")
            return None

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

    @cache.memoize(timeout=3600)
    async def get_dataset_metadata(self, dataset_id: str) -> Dict:
        """Get metadata columns with their properties"""
        try:
            # If it's a valid tissue, use get_expression_data
            if dataset_id.upper() in self.valid_tissues:
                df_expr, df_meta = await self.get_expression_data(["SIRT1"], dataset_id)

                if df_meta.empty:
                    return {
                        "status": "error",
                        "message": f"No metadata available for tissue {dataset_id}",
                        "columns": [],
                    }

                columns = []
                for column in df_meta.columns:
                    if column != "sample_id":
                        unique_values = df_meta[column].nunique()
                        column_type = str(df_meta[column].dtype)

                        columns.append(
                            {
                                "name": column,
                                "unique_values": unique_values,
                                "type": column_type,
                            }
                        )

                return {"status": "success", "columns": columns}

            # Otherwise assume it's a GEO dataset ID
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                params = {"db": "gds", "id": dataset_id, "retmode": "json"}

                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"Failed to fetch GEO dataset {dataset_id}",
                        "columns": [],
                    }

                data = response.json()
                result = data.get("result", {}).get(str(dataset_id))

                if not result:
                    return {
                        "status": "error",
                        "message": f"Dataset {dataset_id} not found",
                        "columns": [],
                    }

                # Extract columns from dataset variables
                variables = result.get("variables", [])
                columns = []

                for var in variables:
                    columns.append(
                        {
                            "name": var.get("name", ""),
                            "unique_values": len(var.get("categories", [])),
                            "type": (
                                "categorical"
                                if var.get("type") == "factor"
                                else "numerical"
                            ),
                        }
                    )

                return {"status": "success", "columns": columns}

        except Exception as e:
            logger.error(f"Error getting dataset metadata: {str(e)}")
            return {"status": "error", "message": str(e), "columns": []}


expression_endpoints = ExpressionEndpoints()
