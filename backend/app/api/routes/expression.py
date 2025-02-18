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


@router.get("/genes/{gene}/tissue-summary")
async def get_tissue_summary(gene: str):
    """Get expression summary across tissues for a gene"""
    try:
        if not validate_genes([gene]):
            raise HTTPException(status_code=400, detail="Invalid gene symbol")

        result = await expression_endpoints.get_tissue_expression_summary(gene)
        if result["status"] == "error":
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            raise HTTPException(status_code=500, detail=result["message"])

        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting tissue summary: {str(e)}")
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
