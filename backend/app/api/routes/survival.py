# app/api/routes/survival.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from backend.app.services.survival_analysis_service import SurvivalAnalysisService
from app.services.gtex_service import GTExService

router = APIRouter()


@router.get("/{gene}")
async def get_survival_analysis(
    gene: str,
    gtex_service: GTExService = Depends(),
    analysis_service: SurvivalAnalysisService = Depends(),
) -> Dict:
    """Get survival analysis for a gene"""
    if not gene:
        raise HTTPException(status_code=400, detail="Gene must be specified")

    # Get expression data
    df = await gtex_service.get_expression_data([gene], "WHOLE_BLOOD")

    # Perform survival analysis
    results = analysis_service.analyze_survival(df, gene)
    return results
