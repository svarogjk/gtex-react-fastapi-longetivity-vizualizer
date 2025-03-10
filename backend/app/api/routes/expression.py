import re
import httpx
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.utils.helpers import validate_genes, validate_tissue, logger
from app.api.endpoints.expression import expression_endpoints
from app.services.search_service import SearchService
from app.services.gtex_service import GTExService

router = APIRouter()
search_service = SearchService()
gtex_service = GTExService()


@router.get("/genes/expression")
async def get_expression(
    genes: List[str] = Query(..., description="List of gene symbols"),
    tissue: str = Query(..., description="Tissue type"),
):
    """Get gene expression data with longevity context"""
    try:
        if not validate_genes(genes):
            raise HTTPException(status_code=400, detail="Invalid gene symbols")

        if not validate_tissue(tissue):
            raise HTTPException(status_code=400, detail="Invalid tissue type")

        # Use the singleton instance to get expression data
        df_expr, df_meta = await expression_endpoints.get_expression_data(genes, tissue)
        result = expression_endpoints.process_expression_data(df_expr, df_meta)

        return result
    except Exception as e:
        logger.error(f"Error in get_expression: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genes/longevity-analysis")
async def analyze_longevity(
    genes: List[str] = Query(..., description="List of gene symbols"),
    tissue: str = Query(..., description="Tissue type"),
):
    """Analyze expression patterns in context of longevity"""
    try:
        if not validate_genes(genes):
            raise HTTPException(status_code=400, detail="Invalid gene symbols")

        result = await expression_endpoints.analyze_longevity_patterns(genes, tissue)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_longevity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tissues")
async def get_tissues():
    """Get list of available tissues with categories"""
    try:
        result = await expression_endpoints.get_available_tissues()
        return result
    except Exception as e:
        logger.error(f"Error getting tissues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/metadata")
async def get_dataset_metadata(dataset_id: str):
    """Get metadata information for a dataset"""
    try:
        result = await expression_endpoints.get_dataset_metadata(dataset_id)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except Exception as e:
        logger.error(f"Error getting dataset metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genes/{gene}/expression/{tissue}")
async def get_gene_tissue_expression(gene: str, tissue: str):
    """Get detailed expression data for a specific gene in a tissue"""
    try:
        if not validate_genes([gene]):
            raise HTTPException(status_code=400, detail="Invalid gene symbol")

        if not validate_tissue(tissue):
            raise HTTPException(status_code=400, detail="Invalid tissue type")

        df_expr, df_meta = await expression_endpoints.get_expression_data(
            [gene], tissue
        )
        result = expression_endpoints.process_expression_data(df_expr, df_meta)

        if result["status"] == "no_data":
            raise HTTPException(status_code=404, detail="No expression data found")

        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting gene tissue expression: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genes/{gene}/tissue-summary")
async def get_tissue_summary(gene: str):
    """Get expression summary across tissues for a gene"""
    try:
        # Validate gene symbol format
        if not re.match(r"^[A-Za-z0-9-]+$", gene):
            raise HTTPException(
                status_code=400, detail=f"Invalid gene symbol format: {gene}"
            )

        result = await expression_endpoints.get_tissue_expression_summary_by_gene(gene)

        # Handle different error cases
        if result["status"] == "error":
            if "not found" in result["message"].lower():
                raise HTTPException(
                    status_code=404, detail=f"Gene {gene} not found in GTEx database"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Error processing gene {gene}: {result['message']}",
            )

        return result

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting tissue summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error processing gene {gene}"
        )


@router.get("/datasets-summary/genes/{gene}/tissues/{tissue}")
async def get_dataset_expression_summaries(
    gene: str,
    tissue: str,
    limit: Optional[int] = Query(
        50, description="Limit the number of datasets returned"
    ),
):
    """
    Get expression summaries across multiple datasets for a specific gene and tissue.

    Returns median expression values and dataset metadata for the gene in the specified tissue.
    """
    try:
        # Validate gene symbol
        if not validate_genes([gene]):
            raise HTTPException(status_code=400, detail=f"Invalid gene symbol: {gene}")

        # Handle case sensitivity for tissue
        tissue_upper = tissue.upper()
        normalized_tissue = None

        # Check if it's a valid tissue key or display name
        for tissue_key, display_name in expression_endpoints.valid_tissues.items():
            if (
                tissue_upper == tissue_key.upper()
                or tissue.lower() == display_name.lower()
            ):
                normalized_tissue = tissue_key
                break

        if not normalized_tissue:
            # Get all available tissues for better error message
            tissues_info = await expression_endpoints.get_available_tissues()
            available_tissues = tissues_info.get("tissues", [])

            raise HTTPException(
                status_code=400,
                detail=f"Invalid tissue type: {tissue}. Available tissues include: {', '.join(available_tissues[:5])}...",
            )

        # Get the detailed expression summary for this gene-tissue combination
        result = (
            await expression_endpoints.get_dataset_expression_summary_by_gene_tissue(
                gene, normalized_tissue
            )
        )

        if result["status"] == "error":
            if "not found" in result["message"].lower():
                raise HTTPException(
                    status_code=404, detail=f"Gene {gene} not found in GTEx database"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Error processing gene {gene} in tissue {normalized_tissue}: {result['message']}",
            )

        # Get related datasets with expression data for this gene-tissue combination
        related_datasets = []

        # First, try to get GTEx dataset information
        gtex_dataset = {
            "dataset_id": result["data"]["metadata"]["dataset_id"],
            "dataset_name": "GTEx v8",
            "dataset_type": "GTEx",
            "median_expression": result["data"]["statistics"]["median"],
            "mean_expression": result["data"]["statistics"]["mean"],
            "unit": result["data"]["metadata"]["unit"],
            "sample_count": result["data"]["statistics"]["sample_count"],
            "source": "GTEx",
        }
        related_datasets.append(gtex_dataset)

        # Try to get additional datasets from GEO with this gene-tissue combination
        try:
            # Query the search service for related datasets
            additional_datasets = await search_service.find_datasets_for_gene_tissue(
                gene, normalized_tissue, limit - 1
            )

            if additional_datasets and "datasets" in additional_datasets:
                for dataset in additional_datasets["datasets"]:
                    # If we have expression data for this dataset, add it
                    if "median_expression" in dataset:
                        related_datasets.append(
                            {
                                "dataset_id": dataset["dataset_id"],
                                "dataset_name": dataset.get(
                                    "title", dataset.get("name", "Unknown")
                                ),
                                "dataset_type": dataset.get("type", "Unknown"),
                                "median_expression": dataset["median_expression"],
                                "mean_expression": dataset.get("mean_expression", None),
                                "unit": dataset.get("unit", "Unknown"),
                                "sample_count": dataset.get("sample_count", 0),
                                "source": dataset.get("source", "GEO"),
                            }
                        )
        except Exception as e:
            logger.warning(
                f"Error retrieving additional datasets for {gene} in {normalized_tissue}: {str(e)}"
            )
            # Continue with just the GTEx data if there's an error with additional datasets

        # Return the consolidated result
        return {
            "status": "success",
            "data": {
                "gene": gene,
                "tissue": normalized_tissue,
                "original_tissue_query": tissue,
                "tissue_display_name": result["data"]["tissue_display_name"],
                "gtex_summary": {
                    "statistics": result["data"]["statistics"],
                    "tissue_context": result["data"]["tissue_context"],
                },
                "datasets": related_datasets[:limit],
            },
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting dataset expression summaries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error processing gene {gene} in tissue {tissue}",
        )


@router.get("/debug/gtex/{gene}")
async def debug_gtex_api(gene: str):
    """Debug endpoint to test GTEx API connections"""
    async with httpx.AsyncClient() as client:
        results = {}

        # Test gene lookup with new format
        gene_url = f"{expression_endpoints.base_url}/reference/gene"
        gene_params = {"geneId": gene.upper(), "pageSize": 1}

        try:
            gene_response = await client.get(
                gene_url, params=gene_params, headers=expression_endpoints.headers
            )
            results["gene_lookup"] = {
                "url": str(gene_response.url),
                "status": gene_response.status_code,
                "headers": dict(gene_response.headers),
                "response": gene_response.text[:500],
            }
        except Exception as e:
            results["gene_lookup"] = {"error": str(e)}

        # Test alternative lookup format
        alt_params = {"geneId": f"ENSG00000146648.{gene.upper()}", "pageSize": 1}

        try:
            alt_response = await client.get(
                gene_url, params=alt_params, headers=expression_endpoints.headers
            )
            results["alternative_lookup"] = {
                "url": str(alt_response.url),
                "status": alt_response.status_code,
                "headers": dict(alt_response.headers),
                "response": alt_response.text[:500],
            }
        except Exception as e:
            results["alternative_lookup"] = {"error": str(e)}

        # Test expression endpoint
        expr_url = (
            f"{expression_endpoints.base_url}/expression/medianTranscriptExpression"
        )
        expr_params = {"datasetId": "gtex_v8", "geneId": gene.upper(), "format": "json"}

        try:
            expr_response = await client.get(
                expr_url, params=expr_params, headers=expression_endpoints.headers
            )
            results["expression_lookup"] = {
                "url": str(expr_response.url),
                "status": expr_response.status_code,
                "headers": dict(expr_response.headers),
                "response": expr_response.text[:500],
            }
        except Exception as e:
            results["expression_lookup"] = {"error": str(e)}

        return {
            "status": "success",
            "results": results,
            "base_url": expression_endpoints.base_url,
            "headers": expression_endpoints.headers,
        }
