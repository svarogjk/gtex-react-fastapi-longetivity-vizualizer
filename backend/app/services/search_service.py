from typing import List, Dict, Set, Optional
import httpx
import asyncio
from app.server_cache.cache_manager import cache
from app.utils.helpers import logger


class SearchService:
    def __init__(self):
        self.gtex_base_url = "https://gtexportal.org/api/v2"
        self.geo_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.timeout = 30.0

        # Longevity-related search terms
        self.longevity_keywords = [
            "aging",
            "longevity",
            "lifespan",
            "senescence",
            "age-related",
            "healthspan",
            "age-associated",
            "centenarian",
            "life extension",
            "biological age",
            "DNA damage",
            "telomere",
            "mitochondrial function",
            "oxidative stress",
            "inflammation aging",
            "epigenetic aging",
            "cellular senescence",
        ]

        # Core pathways
        self.longevity_pathways = [
            "SIRT",
            "FOXO",
            "mTOR",
            "insulin signaling",
            "DNA repair",
            "telomerase",
            "autophagy",
            "mitochondrial",
            "stress response",
            "proteostasis",
        ]

    @cache.memoize(timeout=3600)
    async def search_genes(self, query: Optional[str] = None) -> Dict:
        """
        Search for genes based on query and longevity keywords using NCBI E-utilities
        Returns both direct matches and longevity-related genes
        """
        try:
            # Construct search query
            search_terms = []
            if query:
                search_terms.append(f'"{query}"[All Fields]')

            # Add longevity-related terms with proper field tags
            longevity_query = " OR ".join(
                [f'"{term}"[All Fields]' for term in self.longevity_keywords]
            )
            search_terms.append(f"({longevity_query})")

            # Add organism specification for human genes
            search_terms.append('"Homo sapiens"[Organism]')

            # Combine all terms
            final_query = " AND ".join(search_terms)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, search for gene IDs
                esearch_response = await client.get(
                    f"{self.geo_base_url}/esearch.fcgi",
                    params={
                        "db": "gene",
                        "term": final_query,
                        "retmax": 100,
                        "retmode": "json",
                    },
                )

                if esearch_response.status_code != 200:
                    logger.error(f"NCBI esearch failed: {esearch_response.status_code}")
                    return {"genes": [], "gene_details": {}, "total_count": 0}

                search_data = esearch_response.json()
                gene_ids = search_data.get("esearchresult", {}).get("idlist", [])

                if not gene_ids:
                    return {"genes": [], "gene_details": {}, "total_count": 0}

                # Get detailed information for found genes
                esummary_response = await client.get(
                    f"{self.geo_base_url}/esummary.fcgi",
                    params={"db": "gene", "id": ",".join(gene_ids), "retmode": "json"},
                )

                if esummary_response.status_code != 200:
                    logger.error(
                        f"NCBI esummary failed: {esummary_response.status_code}"
                    )
                    return {"genes": [], "gene_details": {}, "total_count": 0}

                summary_data = esummary_response.json()
                result = summary_data.get("result", {})

                genes = set()
                gene_details = {}

                # Process each gene
                for gene_id in gene_ids:
                    gene_data = result.get(str(gene_id), {})
                    if gene_data:
                        symbol = gene_data.get("name")  # Gene symbol
                        if symbol:
                            genes.add(symbol)
                            gene_details[symbol] = {
                                "description": gene_data.get("description", ""),
                                "type": gene_data.get("type", ""),
                                "summary": gene_data.get("summary", ""),
                                "aliases": gene_data.get("otheraliases", "").split(
                                    ", "
                                ),
                                "chromosome": gene_data.get("chromosome", ""),
                                "location": gene_data.get("maplocation", ""),
                            }

                return {
                    "genes": sorted(list(genes)),
                    "gene_details": gene_details,
                    "total_count": len(genes),
                }

        except Exception as e:
            logger.error(f"Error searching genes: {str(e)}")
            return {"genes": [], "gene_details": {}, "total_count": 0}

    @cache.memoize(timeout=3600)
    async def search_datasets(
        self, genes: list[str] | None = None, tissues: list[str] | None = None
    ) -> Dict:
        """
        Search for relevant datasets in GEO based on genes and longevity keywords
        """
        try:
            # Construct search query
            search_terms = []
            if genes:
                search_terms.extend(genes)
            if tissues:
                search_terms.extend(tissues)
            search_terms.extend(self.longevity_keywords)
            search_terms.extend(self.longevity_pathways)

            query = " OR ".join([f'"{term}"[All Fields]' for term in search_terms])
            query += ' AND "expression profiling by array"[DataSet Type]'

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Search GEO
                response = await client.get(
                    f"{self.geo_base_url}/esearch.fcgi",
                    params={
                        "db": "gds",
                        "term": query,
                        "retmax": 100,
                        "retmode": "json",
                    },
                )

                if response.status_code != 200:
                    return {"datasets": [], "total_count": 0}

                data = response.json()
                dataset_ids = data.get("esearchresult", {}).get("idlist", [])

                # Get details for each dataset
                if dataset_ids:
                    details_response = await client.get(
                        f"{self.geo_base_url}/esummary.fcgi",
                        params={
                            "db": "gds",
                            "id": ",".join(dataset_ids),
                            "retmode": "json",
                        },
                    )

                    if details_response.status_code == 200:
                        details_data = details_response.json()
                        datasets = []

                        for dataset_id in dataset_ids:
                            dataset = details_data.get("result", {}).get(dataset_id, {})
                            if dataset:
                                datasets.append(
                                    {
                                        "id": dataset_id,
                                        "title": dataset.get("title", ""),
                                        "description": dataset.get("description", ""),
                                        "organism": dataset.get("organism", ""),
                                        "sample_count": dataset.get("samples", 0),
                                        "platform": dataset.get("platform", ""),
                                        "gse": dataset.get("gse", ""),
                                    }
                                )

                        return {"datasets": datasets, "total_count": len(datasets)}

                return {"datasets": [], "total_count": 0}

        except Exception as e:
            logger.error(f"Error searching datasets: {str(e)}")
            return {"datasets": [], "total_count": 0}

    @cache.memoize(timeout=3600)
    async def get_dropdown_options(self) -> Dict:
        """
        Get options for both dropdowns (genes and datasets)
        """
        try:
            # Get longevity-related genes
            genes_result = await self.search_genes()

            # Get relevant datasets
            datasets_result = await self.search_datasets(
                genes_result.get("genes", [])[:5]
            )

            return {
                "genes": {
                    "options": [
                        {
                            "value": gene,
                            "label": f"{gene}: {details.get('description', '')}",
                            "details": details,
                        }
                        for gene, details in genes_result.get(
                            "gene_details", {}
                        ).items()
                    ],
                    "total_count": genes_result.get("total_count", 0),
                },
                "datasets": {
                    "options": [
                        {
                            "value": dataset.get("gse", ""),
                            "label": dataset.get("title", ""),
                            "details": dataset,
                        }
                        for dataset in datasets_result.get("datasets", [])
                    ],
                    "total_count": datasets_result.get("total_count", 0),
                },
            }

        except Exception as e:
            logger.error(f"Error getting dropdown options: {str(e)}")
            return {
                "genes": {"options": [], "total_count": 0},
                "datasets": {"options": [], "total_count": 0},
            }

    @cache.memoize(timeout=3600)
    async def get_dataset_details(self, dataset_id: str) -> Dict:
        """Get detailed information about a specific dataset"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get details using E-utils
                response = await client.get(
                    f"{self.geo_base_url}/esummary.fcgi",
                    params={"db": "gds", "id": dataset_id, "retmode": "json"},
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": "Failed to fetch dataset details",
                    }

                data = response.json()
                result = data.get("result", {}).get(str(dataset_id), {})

                if not result:
                    return {"success": False, "message": "Dataset not found"}

                # Extract metadata fields from the dataset
                samples = result.get("samples", [])
                metadata = {}

                # Process sample characteristics to extract metadata fields
                for sample in samples:
                    for char in sample.get("characteristics", []):
                        key, value = char.split(": ", 1) if ": " in char else (char, "")
                        if key not in metadata:
                            metadata[key] = []
                        metadata[key].append(value)

                return {
                    "success": True,
                    "metadata": metadata,
                    "title": result.get("title", ""),
                    "summary": result.get("summary", ""),
                    "samples": len(samples),
                }

        except Exception as e:
            logger.error(f"Error getting dataset details: {str(e)}")
            return {"success": False, "message": str(e)}
