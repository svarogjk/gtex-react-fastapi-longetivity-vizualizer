from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.utils.helpers import validate_genes, validate_tissue, logger
from app.api.endpoints.expression import expression_endpoints
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()


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


@router.get("/genes/{gene}/tissue-summary")
async def get_tissue_summary(gene: str):
    """Get expression summary across tissues for a gene"""
    try:
        if not validate_genes([gene]):
            raise HTTPException(status_code=400, detail="Invalid gene symbol")

        result = await expression_endpoints.get_tissue_expression_summary(gene)
        return result
    except Exception as e:
        logger.error(f"Error getting tissue summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dropdown endpoints
@router.get("/dropdown/genes")
async def get_gene_options(query: Optional[str] = None):
    """Get gene options for dropdown"""
    try:
        results = await search_service.search_genes(query)
        return results
    except Exception as e:
        logger.error(f"Error getting gene options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropdown/datasets")
async def get_dataset_options(genes: Optional[List[str]] = Query(None)):
    """Get dataset options for dropdown"""
    try:
        results = await search_service.search_datasets(genes)
        return results
    except Exception as e:
        logger.error(f"Error getting dataset options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropdown/options")
async def get_dropdown_options():
    """Get all options for both dropdowns"""
    try:
        return await search_service.get_dropdown_options()
    except Exception as e:
        logger.error(f"Error getting dropdown options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
