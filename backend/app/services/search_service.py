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
        Search for genes based on query or longevity keywords
        Returns both direct matches and longevity-related genes
        """
        try:
            search_terms = []
            if query:
                search_terms.append(query)
            search_terms.extend(self.longevity_keywords)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Search GTEx for each term
                tasks = []
                for term in search_terms:
                    tasks.append(
                        client.get(
                            f"{self.gtex_base_url}/reference/gene",
                            params={"geneId": term, "format": "json", "limit": 50},
                        )
                    )

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                genes = set()
                gene_details = {}

                for response in responses:
                    if isinstance(response, Exception):
                        continue

                    if response.status_code == 200:
                        data = response.json().get("data", [])
                        for gene in data:
                            symbol = gene.get("geneSymbol")
                            if symbol:
                                genes.add(symbol)
                                gene_details[symbol] = {
                                    "description": gene.get("geneDescription", ""),
                                    "type": gene.get("geneType", ""),
                                    "gencode_id": gene.get("gencodeId", ""),
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
    async def search_datasets(self, genes: Optional[List[str]] = None) -> Dict:
        """
        Search for relevant datasets in GEO based on genes and longevity keywords
        """
        try:
            # Construct search query
            search_terms = []
            if genes:
                search_terms.extend(genes)
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
