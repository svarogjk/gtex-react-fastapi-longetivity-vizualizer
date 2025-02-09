# app/api/routes/expression.py
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.services.gtex_service import GTExService
from app.utils.helpers import validate_genes, validate_tissue, process_response, logger

router = APIRouter()


@router.get("/genes")
async def get_expression(
    genes: List[str] = Query(
        ...,
        description="List of gene IDs",
        example=["SIRT1", "FOXO3", "CDKN2A"],
    ),
    tissue: str = Query(
        ..., description="Tissue site detail ID", example="WHOLE_BLOOD"
    ),
    gtex_service: GTExService = Depends(),
):
    """
    Get gene expression data for specified genes in a tissue.
    Returns expression values and metadata in separate tables.
    """
    if not genes:
        raise HTTPException(
            status_code=400, detail="Please provide at least one gene ID"
        )

    try:
        df_expr, df_meta = await gtex_service.get_expression_data(genes, tissue)
        result = gtex_service.process_expression_data(df_expr, df_meta)

        # Add request metadata
        result["request"] = {
            "genes_requested": genes,
            "tissue_requested": tissue,
            "normalized_tissue": gtex_service.normalize_tissue(tissue),
        }

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
