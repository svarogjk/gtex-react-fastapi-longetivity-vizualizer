from fastapi import APIRouter, Depends
from app.services.gtex_service import GTExService
from typing import List

router = APIRouter()


@router.get("/genes/{tissue}")
async def get_expression(
    tissue: str, genes: List[str], gtex_service: GTExService = Depends()
):
    """Get gene expression data for specified genes and tissue"""
    df = await gtex_service.get_expression_data(genes, tissue)
    return gtex_service.process_expression_data(df)


@router.post("/analyze")
async def analyze_expression(
    genes: List[str], tissue: str, gtex_service: GTExService = Depends()
):
    """Analyze gene expression patterns"""
    df = await gtex_service.get_expression_data(genes, tissue)

    # Additional analysis
    analysis = {
        "basic_stats": gtex_service.process_expression_data(df),
        "correlations": df.pivot(columns="gene", values="expression").corr().to_dict(),
    }

    return analysis
