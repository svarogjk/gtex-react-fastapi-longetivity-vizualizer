import httpx
import pandas as pd
from fastapi import HTTPException
from typing import List, Dict, Optional, Tuple
from asyncio import gather
from app.utils.helpers import logger


class GTExService:
    def __init__(self):
        self.base_url = "https://gtexportal.org/api/v2"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        self.valid_tissues = {
            "Adipose_Subcutaneous",
            "Adipose_Visceral_Omentum",
            "Adrenal_Gland",
            "Artery_Aorta",
            "Artery_Coronary",
            "Artery_Tibial",
            "Bladder",
            "Brain_Amygdala",
            "Brain_Anterior_cingulate_cortex_BA24",
            "Brain_Caudate_basal_ganglia",
            "Brain_Cerebellar_Hemisphere",
            "Brain_Cerebellum",
            "Brain_Cortex",
            "Brain_Frontal_Cortex_BA9",
            "Brain_Hippocampus",
            "Brain_Hypothalamus",
            "Brain_Nucleus_accumbens_basal_ganglia",
            "Brain_Putamen_basal_ganglia",
            "Brain_Spinal_cord_cervical_c-1",
            "Brain_Substantia_nigra",
            "Breast_Mammary_Tissue",
            "Cells_Cultured_fibroblasts",
            "Cells_EBV-transformed_lymphocytes",
            "Cells_Transformed_fibroblasts",
            "Cervix_Ectocervix",
            "Cervix_Endocervix",
            "Colon_Sigmoid",
            "Colon_Transverse",
            "Esophagus_Gastroesophageal_Junction",
            "Esophagus_Mucosa",
            "Esophagus_Muscularis",
            "Fallopian_Tube",
            "Heart_Atrial_Appendage",
            "Heart_Left_Ventricle",
            "Kidney_Cortex",
            "Kidney_Medulla",
            "Liver",
            "Lung",
            "Minor_Salivary_Gland",
            "Muscle_Skeletal",
            "Nerve_Tibial",
            "Ovary",
            "Pancreas",
            "Pituitary",
            "Prostate",
            "Skin_Not_Sun_Exposed_Suprapubic",
            "Skin_Sun_Exposed_Lower_leg",
            "Small_Intestine_Terminal_Ileum",
            "Spleen",
            "Stomach",
            "Testis",
            "Thyroid",
            "Uterus",
            "Vagina",
            "Whole_Blood",
        }
        self.tissue_map = {
            "WHOLE_BLOOD": "Whole_Blood",
            "BLOOD": "Whole_Blood",
            "LIVER": "Liver",
            "LUNG": "Lung",
            "HEART": "Heart_Left_Ventricle",
            "BRAIN": "Brain_Cortex",
            "MUSCLE": "Muscle_Skeletal",
            "SKIN": "Skin_Sun_Exposed_Lower_leg",
        }
        self.max_retries = 3
        self.timeout = 30.0
        self.dataset = "gtex_v8"

    def normalize_tissue(self, tissue: str) -> str:
        """Normalize tissue name to valid GTEx v8 tissue ID"""
        tissue_upper = tissue.upper()
        if tissue_upper in self.tissue_map:
            normalized = self.tissue_map[tissue_upper]
        else:
            normalized = tissue

        if normalized not in self.valid_tissues:
            raise ValueError(
                f"Invalid tissue: {tissue}. Must be one of: {', '.join(sorted(self.valid_tissues))}"
            )

        return normalized

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

    async def get_expression_data(
        self, genes: List[str], tissue: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch gene expression data for multiple genes"""
        try:
            normalized_tissue = self.normalize_tissue(tissue)
            logger.info(f"Using normalized tissue: {normalized_tissue}")
        except ValueError as e:
            logger.error(str(e))
            return pd.DataFrame(), pd.DataFrame()

        # Get Gencode IDs for all genes
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            gencode_tasks = [self.get_gencode_id(gene) for gene in genes]
            gencode_ids = await gather(*gencode_tasks)

            # Filter out None values and create gene mapping
            valid_genes = [(gene, gid) for gene, gid in zip(genes, gencode_ids) if gid]

            if not valid_genes:
                logger.warning("No valid Gencode IDs found")
                return pd.DataFrame(), pd.DataFrame()

            # Make request with proper formatting
            url = f"{self.base_url}/expression/geneExpression"
            params = {
                "gencodeId": [gid for _, gid in valid_genes],
                "tissueSiteDetailId": [normalized_tissue],
                "datasetId": self.dataset,
                "format": "json",
            }

            logger.info(f"Making expression request with params: {params}")
            data = await self._make_request(client, url, params)

            if data and "data" in data:
                expression_data = data["data"]
                logger.info(f"Got expression data")
                logger.info(
                    f"Number of entries in expression_data: {len(expression_data)}"
                )

                # Initialize dictionary to store expression values by gene
                expression_dict = {}
                metadata_dict = None

                # Process each gene's data
                for entry in expression_data:
                    gene_symbol = entry.get("geneSymbol")
                    expression_values = entry.get("data", [])

                    logger.info(
                        f"Processing {gene_symbol} with {len(expression_values)} values"
                    )

                    # Store expression values
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

                    # Add sample IDs
                    df_expr.index = [
                        f"GTEX_BLOOD_{i+1:04d}" for i in range(len(df_expr))
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

                    logger.info(f"Expression DataFrame shape: {df_expr.shape}")
                    logger.info(f"Expression columns: {df_expr.columns.tolist()}")
                    logger.info(f"Metadata DataFrame shape: {df_meta.shape}")

                    return df_expr, df_meta

            logger.warning("No expression data received")
            return pd.DataFrame(), pd.DataFrame()

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
            }

        # Calculate gene correlations
        genes = [col for col in df_expr.columns if col != "sample_id"]
        if len(genes) > 1:
            correlations = df_expr[genes].corr().round(3).to_dict()
        else:
            correlations = {}

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
