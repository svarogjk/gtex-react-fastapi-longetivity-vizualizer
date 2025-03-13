# app/utils/helpers.py
import re
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_genes(genes: List[str]) -> bool:
    """
    Validate gene symbols.
    Basic validation: checks if genes are non-empty strings matching typical gene symbol pattern.
    """
    if not genes or not isinstance(genes, list):
        return False

    # Basic gene symbol pattern: uppercase letters and numbers
    gene_pattern = re.compile(r"^[A-Z0-9]+[A-Z0-9\-]*[A-Z0-9]+$")

    return all(
        isinstance(gene, str) and gene.strip() and gene_pattern.match(gene.strip())
        for gene in genes
    )


def validate_tissue(tissue: str) -> bool:
    """
    Validate tissue type.
    Basic validation: checks if tissue is a non-empty string in uppercase with underscores.
    """
    if not tissue or not isinstance(tissue, str):
        return False

    # Basic tissue pattern: uppercase letters, numbers, and underscores
    tissue_pattern = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
    return bool(tissue_pattern.match(tissue.strip()))


def process_response(results: dict) -> dict:
    """
    Process and format the response data
    """
    if not results:
        return {"message": "No results found"}

    return results
