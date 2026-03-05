"""Load sample data via Data Ingestion API (when running as microservice)."""

import sys
from pathlib import Path

import os

import httpx
import pandas as pd

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

INGESTION_URL = os.getenv("DATA_INGESTION_URL", "http://localhost:8081")


def main():
    data_path = Path(__file__).parent.parent / "data" / "sample_data.csv"
    if not data_path.exists():
        print(f"Sample data not found: {data_path}")
        sys.exit(1)

    df = pd.read_csv(data_path)
    records = []
    for _, row in df.iterrows():
        r = {
            "athlete_id": str(row["athlete_id"]),
            "record_date": str(row["record_date"]),
            "sleep_hours": float(row["sleep_hours"]),
            "sleep_quality": float(row["sleep_quality"]),
            "training_load": float(row["training_load"]),
            "stress_level": float(row["stress_level"]),
            "recovery_score": float(row["recovery_score"]),
        }
        if pd.notna(row.get("resting_heart_rate")):
            r["resting_heart_rate"] = float(row["resting_heart_rate"])
        if pd.notna(row.get("hrv")):
            r["hrv"] = float(row["hrv"])
        if pd.notna(row.get("performance_score")):
            r["performance_score"] = float(row["performance_score"])
        records.append(r)

    try:
        resp = httpx.post(
            f"{INGESTION_URL}/v1/ingest",
            json={"records": records},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"Ingested {data['records_ingested']} records via Data Ingestion API")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
