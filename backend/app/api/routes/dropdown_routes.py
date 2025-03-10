from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from app.services.search_service import SearchService
from app.utils.helpers import logger

router = APIRouter()


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
