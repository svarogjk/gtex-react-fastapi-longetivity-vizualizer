from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from app.services.search_service import SearchService
from app.utils.helpers import logger

router = APIRouter()


@router.get("/dropdown/options")
async def get_dropdown_options(search_service: SearchService = Depends()) -> dict:
    """
    Get options for both genes and datasets dropdowns
    """
    try:
        return await search_service.get_dropdown_options()
    except Exception as e:
        logger.error(f"Error getting dropdown options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropdown/genes")
async def search_genes(
    query: Optional[str] = None, search_service: SearchService = Depends()
) -> dict:
    """
    Search for genes based on query and longevity keywords
    """
    try:
        return await search_service.search_genes(query)
    except Exception as e:
        logger.error(f"Error searching genes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dropdown/datasets")
async def search_datasets(
    genes: Optional[List[str]] = Query(None), search_service: SearchService = Depends()
) -> dict:
    """
    Search for datasets based on selected genes and longevity keywords
    """
    try:
        return await search_service.search_datasets(genes)
    except Exception as e:
        logger.error(f"Error searching datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
