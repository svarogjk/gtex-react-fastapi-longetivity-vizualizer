from tenacity import retry, stop_after_attempt, wait_exponential
from sklearn.preprocessing import LabelEncoder
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import json
from app.utils.helpers import logger
from app.server_cache.cache_manager import cache
import httpx
from asyncio import gather


class ExpressionEndpoints:
    def __init__(self):
        self.base_url = "https://gtexportal.org/api/v2"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; Research/1.0)",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.dataset = "gtex_v8"
        self.limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        # Configure client defaults
        self.client_kwargs = {
            "timeout": self.timeout,
            "headers": self.headers,
            "limits": self.limits,
            "follow_redirects": True,
        }

        self.le_hardy = LabelEncoder()

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

        # Add valid tissues map
        self.valid_tissues = {
            "Adipose_Subcutaneous": "Subcutaneous Adipose",
            "Adipose_Visceral_Omentum": "Visceral Adipose",
            "Adrenal_Gland": "Adrenal Gland",
            "Artery_Aorta": "Aorta",
            "Artery_Coronary": "Coronary Artery",
            "Artery_Tibial": "Tibial Artery",
            "Brain_Amygdala": "Amygdala",
            "Brain_Anterior_cingulate_cortex_BA24": "Anterior Cingulate Cortex",
            "Brain_Caudate_basal_ganglia": "Caudate",
            "Brain_Cerebellar_Hemisphere": "Cerebellar Hemisphere",
            "Brain_Cerebellum": "Cerebellum",
            "Brain_Cortex": "Cortex",
            "Brain_Frontal_Cortex_BA9": "Frontal Cortex",
            "Brain_Hippocampus": "Hippocampus",
            "Brain_Hypothalamus": "Hypothalamus",
            "Brain_Nucleus_accumbens_basal_ganglia": "Nucleus Accumbens",
            "Brain_Putamen_basal_ganglia": "Putamen",
            "Brain_Spinal_cord_cervical_c-1": "Spinal Cord",
            "Brain_Substantia_nigra": "Substantia Nigra",
            "Breast_Mammary_Tissue": "Breast",
            "Cells_Cultured_fibroblasts": "Fibroblasts",
            "Cells_EBV-transformed_lymphocytes": "Lymphoblasts",
            "Colon_Sigmoid": "Sigmoid Colon",
            "Colon_Transverse": "Transverse Colon",
            "Esophagus_Gastroesophageal_Junction": "Gastroesophageal Junction",
            "Esophagus_Mucosa": "Esophagus Mucosa",
            "Esophagus_Muscularis": "Esophagus Muscularis",
            "Heart_Atrial_Appendage": "Heart Atrial Appendage",
            "Heart_Left_Ventricle": "Heart Left Ventricle",
            "Kidney_Cortex": "Kidney Cortex",
            "Liver": "Liver",
            "Lung": "Lung",
            "Minor_Salivary_Gland": "Minor Salivary Gland",
            "Muscle_Skeletal": "Skeletal Muscle",
            "Nerve_Tibial": "Tibial Nerve",
            "Ovary": "Ovary",
            "Pancreas": "Pancreas",
            "Pituitary": "Pituitary",
            "Prostate": "Prostate",
            "Skin_Not_Sun_Exposed_Suprapubic": "Skin Not Sun Exposed",
            "Skin_Sun_Exposed_Lower_leg": "Skin Sun Exposed",
            "Small_Intestine_Terminal_Ileum": "Small Intestine",
            "Spleen": "Spleen",
            "Stomach": "Stomach",
            "Testis": "Testis",
            "Thyroid": "Thyroid",
            "Uterus": "Uterus",
            "Vagina": "Vagina",
            "Whole_Blood": "Whole Blood",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Create a configured HTTP client"""
        return httpx.AsyncClient(**self.client_kwargs)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _make_request(
        self, client: httpx.AsyncClient, url: str, params: Dict = None
    ) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes

            logger.info(f"Successful request to {response.url}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise

    @cache.memoize(timeout=3600)
    async def get_expression_data(
        self, genes: List[str], tissue: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch gene expression data for multiple genes"""
        normalized_tissue = self.valid_tissues.get(tissue.upper(), tissue)

        # Get Gencode IDs for all genes
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            gencode_tasks = [self.get_gencode_id(gene) for gene in genes]
            gencode_ids = await gather(*gencode_tasks)

            # Filter out None values and create gene mapping
            valid_genes = [(gene, gid) for gene, gid in zip(genes, gencode_ids) if gid]

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
    async def get_tissue_expression_summary_by_gene(self, gene: str) -> Dict:
        """Get expression summary across tissues for a gene"""
        try:
            gencode_id = await self.get_gencode_id(gene)
            logger.info(f"Gencode ID lookup for {gene}: {gencode_id}")

            if not gencode_id:
                return {"gene": gene, "tissue_expression": []}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Updated endpoint for tissue expression with correct parameter name
                url = f"{self.base_url}/expression/medianGeneExpression"
                params = {
                    "datasetId": "gtex_v8",
                    "gencodeId": gencode_id,  # Changed from geneId to gencodeId
                    "format": "json",
                }

                logger.info(f"Requesting expression data: {url} with params {params}")
                response = await client.get(url, params=params, headers=self.headers)

                if response.status_code != 200:
                    logger.error(
                        f"GTEx API error: {response.status_code} - {response.text}"
                    )
                    return {"gene": gene, "tissue_expression": []}

                data = response.json()

                if not data or "data" not in data:
                    logger.error(f"Unexpected GTEx API response: {data}")
                    return {"gene": gene, "tissue_expression": []}

                tissue_expression = []
                for tissue_data in data["data"]:
                    tissue_id = tissue_data.get("tissueSiteDetailId")
                    if tissue_id in self.valid_tissues:
                        tissue_expression.append(
                            {
                                "tissue": tissue_id,
                                "display_name": self.valid_tissues[tissue_id],
                                "median_expression": float(
                                    tissue_data.get("median", 0)
                                ),
                                "tissue_name": tissue_data.get("tissueSiteDetail", ""),
                                "sample_count": tissue_data.get("sampleCount", 0),
                            }
                        )

                if not tissue_expression:
                    return {"gene": gene, "tissue_expression": []}

                return {
                    "gene": gene,
                    "gencode_id": gencode_id,
                    "tissue_expression": sorted(
                        tissue_expression,
                        key=lambda x: x["median_expression"],
                        reverse=True,
                    ),
                }

        except Exception as e:
            logger.error(f"Error in tissue expression summary: {str(e)}")
            return {"gene": gene, "tissue_expression": []}

    async def get_dataset_expression_summary_by_gene_tissue(
        self, gene: str, tissue: str
    ) -> Dict:
        """
        Get comprehensive expression summary for a gene in a specific tissue.

        Parameters:
        gene (str): Gene symbol to analyze
        tissue (str): Tissue to analyze expression in

        Returns:
        Dict: Dictionary containing expression data, statistics, and metadata
        """
        try:
            # Get gencode ID for the gene
            gencode_id = await self.get_gencode_id(gene)
            if not gencode_id:
                return {"gene": gene, "tissue": tissue, "expression": {}}

            # Get expression data for the gene in the specified tissue
            df_expr, df_meta = await self.get_expression_data([gene], tissue)

            if df_expr.empty or df_meta.empty:
                return {"gene": gene, "tissue": tissue, "expression": {}}

            # Extract tissue display name
            tissue_display = self.valid_tissues.get(tissue, tissue)

            # Calculate expression statistics
            expression_values = (
                df_expr[gene].tolist() if gene in df_expr.columns else []
            )

            statistics = {
                "mean": float(df_expr[gene].mean()) if expression_values else 0,
                "median": float(df_expr[gene].median()) if expression_values else 0,
                "std": float(df_expr[gene].std()) if expression_values else 0,
                "min": float(df_expr[gene].min()) if expression_values else 0,
                "max": float(df_expr[gene].max()) if expression_values else 0,
                "quartiles": (
                    [
                        float(df_expr[gene].quantile(0.25)),
                        float(df_expr[gene].quantile(0.5)),
                        float(df_expr[gene].quantile(0.75)),
                    ]
                    if expression_values
                    else [0, 0, 0]
                ),
                "sample_count": len(expression_values),
            }

            # Additional tissue context data - compare with tissue expression summary
            tissue_context = await self.get_tissue_expression_summary_by_gene(gene)
            tissue_rank = None
            percentile = None
            tissue_data = tissue_context["tissue_expression"]
            all_expressions = [t["median_expression"] for t in tissue_data]

            if all_expressions:
                # Find the current tissue in the list
                current_tissue_data = next(
                    (t for t in tissue_data if t["tissue"] == tissue), None
                )

                if current_tissue_data:
                    current_expression = current_tissue_data["median_expression"]
                    tissue_rank = sum(
                        1 for x in all_expressions if x >= current_expression
                    )
                    percentile = round(
                        (len(all_expressions) - tissue_rank)
                        / len(all_expressions)
                        * 100,
                        2,
                    )

            return {
                "gene": gene,
                "gencode_id": gencode_id,
                "tissue": tissue,
                "tissue_display_name": tissue_display,
                "expression_values": expression_values,
                "statistics": statistics,
                "metadata": {
                    "unit": (
                        df_meta["unit"].iloc[0] if "unit" in df_meta.columns else "TPM"
                    ),
                    "dataset_id": (
                        df_meta["dataset_id"].iloc[0]
                        if "dataset_id" in df_meta.columns
                        else self.dataset
                    ),
                },
                "tissue_context": {
                    "rank": tissue_rank,
                    "percentile": percentile,
                    "total_tissues": (len(tissue_context["tissue_expression"])),
                    "highest_expression_tissue": (
                        tissue_context["tissue_expression"][0]["display_name"]
                        if tissue_context["tissue_expression"]
                        else None
                    ),
                },
            }

        except Exception as e:
            logger.error(
                f"Error getting expression summary for {gene} in {tissue}: {str(e)}"
            )
            return {"gene": gene, "tissue": tissue, "expression": {}}

    async def get_gencode_id(self, gene_symbol: str) -> Optional[str]:
        """Get Gencode ID for a gene symbol"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/reference/gene"
                params = {"geneId": gene_symbol.upper(), "pageSize": 1}

                logger.info(
                    f"Requesting gene info from GTEx: {url} with params {params}"
                )
                response = await client.get(url, params=params, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    if (
                        data
                        and isinstance(data, dict)
                        and "data" in data
                        and data["data"]
                    ):
                        gene_data = data["data"][0]
                        gencode_id = gene_data.get("gencodeId")
                        if gencode_id:
                            logger.info(
                                f"Found Gencode ID for {gene_symbol}: {gencode_id}"
                            )
                            return gencode_id

                logger.warning(f"No Gencode ID found for gene {gene_symbol}")
                return None

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
    async def fetch_sample_data(self, client, subject):
        subject_id = subject.get("subjectId")
        sample_url = f"{self.base_url}/dataset/sample"
        dataset_id = subject.get("datasetId")
        subject_id = subject.get("subjectId")
        sample_params = {
            "datasetId": dataset_id,
            "subjectId": subject_id,
            "sortBy": "sampleId",
            "sortDirection": "asc",
        }
        sample_response = await client.get(
            sample_url, params=sample_params, headers=self.headers
        )
        if sample_response.status_code == 200:
            sample_data = sample_response.json().get("data", {})
        else:
            sample_data = {}

        return {
            "subject_id": subject_id,
            "sex": subject.get("sex"),
            "dataset_id": subject.get("datasetId"),
            "age_bracket": subject.get("ageBracket"),
            "hardy_scale": subject.get("hardyScale"),
            "sample_data": sample_data,
        }

    @cache.memoize(timeout=3600)
    async def get_subject_metadata(self, dataset_id: str) -> list[dict]:
        """
        Get subject metadata from GTEx API using available endpoints.
        This function is designed to be robust against API changes.
        """
        metadata_subjects = []
        # Extract GTEx version from dataset_id
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Try the main dataset endpoint first which should give us basic info
            subject_url = f"{self.base_url}/dataset/subject"
            subject_params = {"datasetId": dataset_id.casefold()}

            logger.info(f"Requesting GTEx subject data from: {subject_url}")
            subject_response = await client.get(
                subject_url, params=subject_params, headers=self.headers
            )

            if subject_response.status_code == 200:
                subject_data = subject_response.json()
                logger.info(f"Successfully retrieved subject data from {subject_url}")
                tasks = [
                    self.fetch_sample_data(client, subject)
                    for subject in subject_data.get("data", [])
                ]
                metadata_subjects = await gather(*tasks)
        return metadata_subjects

    def prepare_df_meta(self, metadata: list[dict]) -> pd.DataFrame:
        df_meta = pd.DataFrame(metadata)
        df_meta = df_meta.explode("sample_data")
        df_meta = pd.concat(
            [
                df_meta.drop(columns=["sample_data"]).reset_index(drop=True),
                pd.json_normalize(df_meta["sample_data"].values).reset_index(drop=True),
            ],
            axis=1,
        )
        df_meta["hardy_numeric"] = self.le_hardy.fit_transform(df_meta["hardy_scale"])
        df_meta[["age_low", "age_high"]] = (
            df_meta["age_bracket"].str.split("-", expand=True).astype(int)
        )
        df_meta["time"] = (df_meta["age_low"] + df_meta["age_high"]) / 2
        return df_meta


expression_endpoints = ExpressionEndpoints()
