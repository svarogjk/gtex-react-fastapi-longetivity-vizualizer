from typing import List, Dict, Optional, Set
import pandas as pd
import httpx
from app.utils.helpers import logger
from app.server_cache.cache_manager import cache


class LongevityGenes:
    """Known longevity-associated genes"""

    CORE_GENES = {
        "SIRT1",
        "SIRT2",
        "SIRT3",
        "SIRT4",
        "SIRT5",
        "SIRT6",
        "SIRT7",  # Sirtuins
        "FOXO1",
        "FOXO3",
        "FOXO4",  # FOXO family
        "CDKN2A",
        "CDKN2B",  # Cell cycle regulators
        "TERT",  # Telomerase
        "APOE",  # Apolipoprotein E
        "IGF1",
        "IGF1R",  # Insulin-like growth factor
        "MTOR",  # mTOR pathway
        "AMPK",  # Energy sensor
        "PGC1A",  # Mitochondrial function
        "KLOTHO",  # Anti-aging hormone
        "NR3C1",  # Stress response
        "PARP1",  # DNA repair
    }

    PATHWAY_KEYWORDS = [
        "aging",
        "longevity",
        "lifespan",
        "senescence",
        "telomere",
        "mitochondrial",
        "stress response",
        "DNA repair",
        "oxidative stress",
        "inflammation",
        "autophagy",
        "proteostasis",
    ]

    @staticmethod
    def search_longevity_genes(query: str) -> Set[str]:
        """Search for longevity-related genes based on query"""
        query = query.upper()
        matches = set()

        # Direct matches from core genes
        matches.update(gene for gene in LongevityGenes.CORE_GENES if query in gene)

        # Keyword-based matches
        if any(keyword in query.lower() for keyword in LongevityGenes.PATHWAY_KEYWORDS):
            matches.update(LongevityGenes.CORE_GENES)

        return matches


class GTExService:
    def __init__(self):
        self.base_url = "https://gtexportal.org/api/v2"
        self.timeout = 30.0

    @cache.memoize(timeout=3600)
    async def search_genes(self, query: str) -> Dict[str, List[str]]:
        """Search for genes with longevity context"""
        # First check longevity-specific genes
        longevity_matches = LongevityGenes.search_longevity_genes(query)

        # Search GTEx Portal
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/reference/gene", params={"geneId": query}
            )
            gtex_results = response.json().get("data", [])

            gtex_genes = [gene["geneSymbol"] for gene in gtex_results]

        return {
            "longevity_related": list(longevity_matches),
            "gtex_matches": gtex_genes,
        }

    @cache.memoize(timeout=3600)
    async def get_expression_with_longevity_context(
        self, genes: List[str], tissue: str
    ) -> Dict:
        """Get expression data with longevity analysis"""
        # Get basic expression data
        expr_df, meta_df = await self.get_expression_data(genes, tissue)

        # Add longevity context
        longevity_genes = set(genes) & LongevityGenes.CORE_GENES

        result = {
            "expression_data": expr_df.to_dict(),
            "metadata": meta_df.to_dict(),
            "longevity_context": {
                "is_longevity_related": bool(longevity_genes),
                "longevity_genes_present": list(longevity_genes),
                "related_pathways": [
                    pathway
                    for pathway in LongevityGenes.PATHWAY_KEYWORDS
                    if any(gene in pathway.upper() for gene in genes)
                ],
            },
        }

        return result

    @cache.memoize(timeout=3600)
    async def analyze_longevity_patterns(self, genes: List[str], tissue: str) -> Dict:
        """Analyze expression patterns in context of longevity"""
        expr_df, meta_df = await self.get_expression_data(genes, tissue)

        # Calculate correlations between longevity genes
        longevity_genes = [g for g in genes if g in LongevityGenes.CORE_GENES]
        correlations = (
            expr_df[longevity_genes].corr() if longevity_genes else pd.DataFrame()
        )

        # Basic statistics
        stats = {
            gene: {
                "mean": float(expr_df[gene].mean()),
                "std": float(expr_df[gene].std()),
                "is_longevity_related": gene in LongevityGenes.CORE_GENES,
            }
            for gene in genes
        }

        return {
            "longevity_analysis": {
                "num_longevity_genes": len(longevity_genes),
                "longevity_genes": longevity_genes,
                "correlations": correlations.to_dict(),
                "gene_stats": stats,
            },
            "tissue_context": {"tissue": tissue, "sample_count": len(expr_df)},
        }
