"""Data Ingestion API routes."""

from io import StringIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.application.use_cases.ingest import IngestPerformanceDataUseCase
from src.data_ingestion.schemas import BulkIngestRequest, IngestResponse
from src.domain.entities import PerformanceRecord
from src.infrastructure.repositories import SqlAlchemyPerformanceRepository

router = APIRouter(prefix="/v1", tags=["ingest"])


def get_ingest_use_case() -> IngestPerformanceDataUseCase:
    """Dependency for ingest use case."""
    repo = SqlAlchemyPerformanceRepository()
    return IngestPerformanceDataUseCase(performance_repo=repo)


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Bulk ingest records",
    description="Ingest performance records from JSON body. Max 10000 records per request.",
)
async def bulk_ingest(
    request: BulkIngestRequest,
    use_case: Annotated[IngestPerformanceDataUseCase, Depends(get_ingest_use_case)],
) -> IngestResponse:
    """Bulk ingest performance records via JSON."""
    records = [
        PerformanceRecord(
            athlete_id=r.athlete_id,
            record_date=r.record_date,
            sleep_hours=r.sleep_hours,
            sleep_quality=r.sleep_quality,
            training_load=r.training_load,
            stress_level=r.stress_level,
            recovery_score=r.recovery_score,
            resting_heart_rate=r.resting_heart_rate,
            hrv=r.hrv,
            performance_score=r.performance_score,
        )
        for r in request.records
    ]
    count = use_case.execute_from_records(records)
    return IngestResponse(
        records_ingested=count,
        message=f"Successfully ingested {count} record(s)",
    )


@router.post(
    "/ingest/csv",
    response_model=IngestResponse,
    summary="Ingest from CSV",
    description="Upload a CSV file. Required columns: athlete_id, record_date, sleep_hours, "
    "sleep_quality, training_load, stress_level, recovery_score",
)
async def ingest_csv(
    file: Annotated[UploadFile, File(description="CSV file to ingest")],
    use_case: Annotated[IngestPerformanceDataUseCase, Depends(get_ingest_use_case)],
) -> IngestResponse:
    """Ingest performance data from uploaded CSV file."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    try:
        df = pd.read_csv(StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")

    if len(df) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10000 rows per file. Split into multiple uploads.",
        )

    try:
        count = use_case.execute_from_dataframe(df)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return IngestResponse(
        records_ingested=count,
        message=f"Successfully ingested {count} record(s) from {file.filename}",
    )
