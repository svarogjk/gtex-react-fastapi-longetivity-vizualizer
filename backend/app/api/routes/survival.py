# app/api/routes/survival.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from app.services.survival_analysis_service import SurvivalAnalysisService

router = APIRouter()


@router.get("/genes/{gene}/{tissue}")
async def get_gene_survival_analysis(
    gene: str,
    tissue: str,
    analysis_service: SurvivalAnalysisService = Depends(),
) -> Dict:
    """
    Perform survival analysis for a specific gene in a specific tissue

    Returns Kaplan-Meier survival curves for high vs low expression groups
    and statistical analysis of survival differences
    """
    if not gene:
        raise HTTPException(status_code=400, detail="Gene must be specified")
    if not tissue:
        raise HTTPException(status_code=400, detail="Tissue must be specified")

    # Perform survival analysis
    results = await analysis_service.perform_kaplan_meier_analysis(gene, tissue)
    return results
