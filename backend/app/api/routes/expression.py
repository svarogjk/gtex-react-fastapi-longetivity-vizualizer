# app/api/routes/expression.py
from fastapi import APIRouter, HTTPException, Depends
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from enum import Enum
import redis
import json
from datetime import timedelta
import dask.dataframe as dd
from functools import lru_cache
import pickle
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from app.services.gtex_service import GTExService
from app.utils.helpers import validate_genes, validate_tissue, process_response, logger

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_EXPIRE_TIME = int(os.getenv("REDIS_EXPIRE_TIME", 3600))  # 1 hour default


class RedisManager:
    _redis_client = None
    _redis_binary = None

    @classmethod
    def get_redis_client(cls):
        if cls._redis_client is None:
            cls._redis_client = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
        return cls._redis_client

    @classmethod
    def get_redis_binary(cls):
        if cls._redis_binary is None:
            cls._redis_binary = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=False
            )
        return cls._redis_binary

    @classmethod
    async def initialize(cls):
        """Initialize Redis connections"""
        try:
            redis_client = cls.get_redis_client()
            redis_client.ping()
            print("Successfully connected to Redis")
        except redis.ConnectionError as e:
            print("Failed to connect to Redis. Ensure Redis server is running.")
            raise

    @classmethod
    async def cleanup(cls):
        """Cleanup Redis connections"""
        if cls._redis_client:
            cls._redis_client.close()
            cls._redis_client = None
        if cls._redis_binary:
            cls._redis_binary.close()
            cls._redis_binary = None


@asynccontextmanager
async def lifespan(app):
    # Startup
    await RedisManager.initialize()
    yield
    # Shutdown
    await RedisManager.cleanup()


router = APIRouter()


class DatasetEnum(str, Enum):
    LONGEVITY_DB = "longevity_db"
    AGING_ATLAS = "aging_atlas"
    CALORIC_RESTRICTION = "caloric_restriction"
    LONGITUDINAL_AGING = "longitudinal_aging"
    CENTENARIAN_STUDY = "centenarian_study"


# Dataset metadata with file paths and configurations
DATASET_CONFIG = {
    "longevity_db": {
        "name": "LongevityDB",
        "description": "Comprehensive database of longevity-associated genes and variants",
        "file_path": "data/longevity_db.parquet",
        "samples": 15000,
        "variables": ["age", "lifespan", "health_status", "genetic_variants"],
        "index_col": "sample_id",
        "cache_key_prefix": "longevity_db",
    },
    "aging_atlas": {
        "name": "Aging Atlas",
        "description": "Multi-tissue molecular signatures of aging",
        "file_path": "data/aging_atlas.parquet",
        "samples": 20000,
        "variables": ["age", "tissue_type", "expression_level", "aging_score"],
        "index_col": "sample_id",
        "cache_key_prefix": "aging_atlas",
    },
    "caloric_restriction": {
        "name": "Caloric Restriction Study",
        "description": "Long-term effects of caloric restriction on longevity",
        "file_path": "data/caloric_restriction.parquet",
        "samples": 8000,
        "variables": ["intervention_group", "lifespan", "metabolic_markers"],
        "index_col": "sample_id",
        "cache_key_prefix": "caloric",
    },
    "longitudinal_aging": {
        "name": "Longitudinal Aging Study",
        "description": "20-year longitudinal study of aging biomarkers",
        "file_path": "data/longitudinal_aging.parquet",
        "samples": 12000,
        "variables": ["timepoint", "age", "biomarkers", "health_outcomes"],
        "index_col": "sample_id",
        "cache_key_prefix": "longitudinal",
    },
    "centenarian_study": {
        "name": "Centenarian Cohort",
        "description": "Genetic and phenotypic data from centenarians",
        "file_path": "data/centenarian.parquet",
        "samples": 5000,
        "variables": ["age", "genetic_profile", "lifestyle_factors"],
        "index_col": "sample_id",
        "cache_key_prefix": "centenarian",
    },
}


class CacheManager:
    @staticmethod
    def get_cache_key(prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"

    @staticmethod
    async def get_cached_data(key: str) -> Optional[Any]:
        try:
            redis_client = RedisManager.get_redis_client()
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache error: {e}")
            return None

    @staticmethod
    async def set_cached_data(key: str, data: Any, expire: int = REDIS_EXPIRE_TIME):
        try:
            redis_client = RedisManager.get_redis_client()
            redis_client.setex(key, expire, json.dumps(data))
        except Exception as e:
            print(f"Cache error: {e}")

    @staticmethod
    async def get_cached_dataframe(key: str) -> Optional[pd.DataFrame]:
        try:
            redis_binary = RedisManager.get_redis_binary()
            data = redis_binary.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Cache error: {e}")
            return None

    @staticmethod
    async def set_cached_dataframe(
        key: str, df: pd.DataFrame, expire: int = REDIS_EXPIRE_TIME
    ):
        try:
            redis_binary = RedisManager.get_redis_binary()
            redis_binary.setex(key, expire, pickle.dumps(df))
        except Exception as e:
            print(f"Cache error: {e}")


async def load_dataset(dataset_id: DatasetEnum) -> dd.DataFrame:
    """Load dataset using Dask for efficient processing"""
    config = DATASET_CONFIG[dataset_id]
    file_path = config["file_path"]

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"Dataset file not found: {dataset_id}"
        )

    try:
        return dd.read_parquet(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(e)}")


@router.get("/datasets")
async def get_available_datasets():
    """Get list of available datasets with metadata"""
    cache_key = "datasets:list"

    # Try to get from cache
    cached_data = await CacheManager.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    # Prepare fresh data
    datasets = [
        {
            "id": dataset_id,
            "name": metadata["name"],
            "description": metadata["description"],
            "sample_count": metadata["samples"],
            "available_variables": metadata["variables"],
        }
        for dataset_id, metadata in DATASET_CONFIG.items()
    ]

    # Cache the result
    await CacheManager.set_cached_data(cache_key, datasets)
    return datasets


@router.get("/datasets/{dataset_id}/metadata")
async def get_dataset_metadata(dataset_id: DatasetEnum):
    """Get dataset metadata with caching"""
    cache_key = CacheManager.get_cache_key("metadata", dataset_id)

    # Try to get from cache
    cached_data = await CacheManager.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    # Load fresh data
    try:
        ddf = await load_dataset(dataset_id)
        metadata_sample = ddf.head()

        result = {
            "columns": [
                {
                    "name": col,
                    "type": str(metadata_sample[col].dtype),
                    "description": DATASET_CONFIG[dataset_id]["variables"].get(col, ""),
                }
                for col in metadata_sample.columns
            ],
            "rows": metadata_sample.to_dict(orient="records"),
        }

        # Cache the result
        await CacheManager.set_cached_data(cache_key, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expression/analysis")
async def analyze_expression(
    dataset_id: DatasetEnum,
    genes: List[str],
    target_variable: str,
    tissue_type: Optional[str] = None,
):
    """Analyze gene expression with target variable correlation"""

    # Generate cache key based on parameters
    cache_key = CacheManager.get_cache_key(
        "expression",
        dataset_id,
        ":".join(sorted(genes)),
        target_variable,
        tissue_type or "all",
    )

    # Try to get from cache
    cached_result = await CacheManager.get_cached_data(cache_key)
    if cached_result:
        return cached_result

    try:
        # Load dataset
        ddf = await load_dataset(dataset_id)

        # Filter by tissue type if specified
        if tissue_type:
            ddf = ddf[ddf.tissue_type == tissue_type]

        # Validate genes and target variable
        available_columns = ddf.columns
        if target_variable not in available_columns:
            raise HTTPException(
                status_code=400, detail=f"Target variable not found: {target_variable}"
            )

        missing_genes = [gene for gene in genes if gene not in available_columns]
        if missing_genes:
            raise HTTPException(
                status_code=400, detail=f"Genes not found: {missing_genes}"
            )

        # Calculate statistics
        result = {
            "expression_data": [],
            "target_variable_stats": {
                "name": target_variable,
                "mean": float(ddf[target_variable].mean().compute()),
                "std": float(ddf[target_variable].std().compute()),
            },
        }

        # Calculate gene statistics and correlations
        for gene in genes:
            gene_stats = {
                "gene": gene,
                "mean_expression": float(ddf[gene].mean().compute()),
                "std_expression": float(ddf[gene].std().compute()),
                "correlation_with_target": float(
                    ddf[[gene, target_variable]].corr().compute().iloc[0, 1]
                ),
            }
            result["expression_data"].append(gene_stats)

        # Cache the result
        await CacheManager.set_cached_data(cache_key, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expression/tissue-types/{dataset_id}")
async def get_tissue_types(dataset_id: DatasetEnum):
    """Get available tissue types for a dataset"""
    cache_key = CacheManager.get_cache_key("tissue_types", dataset_id)

    # Try to get from cache
    cached_data = await CacheManager.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    try:
        ddf = await load_dataset(dataset_id)
        if "tissue_type" not in ddf.columns:
            return {"tissue_types": []}

        tissue_types = ddf.tissue_type.unique().compute().tolist()
        result = {"tissue_types": tissue_types}

        # Cache the result
        await CacheManager.set_cached_data(cache_key, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expression/genes/{dataset_id}")
async def get_available_genes(dataset_id: DatasetEnum):
    """Get list of available genes in a dataset"""
    cache_key = CacheManager.get_cache_key("genes", dataset_id)

    # Try to get from cache
    cached_data = await CacheManager.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    try:
        ddf = await load_dataset(dataset_id)
        # Filter columns that represent genes (you might want to customize this logic)
        gene_columns = [col for col in ddf.columns if not col.startswith("_")]
        result = {"genes": gene_columns}

        # Cache the result
        await CacheManager.set_cached_data(cache_key, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Startup event to ensure Redis connection
@router.on_event("startup")
async def startup_event():
    try:
        redis_client.ping()
        print("Successfully connected to Redis")
    except redis.ConnectionError:
        print("Failed to connect to Redis. Ensure Redis server is running.")
        raise


# Shutdown event to clean up connections
@router.on_event("shutdown")
async def shutdown_event():
    redis_client.close()
    redis_binary.close()


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
