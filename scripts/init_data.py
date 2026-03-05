"""Initialize database with sample data - run after DB is up."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.use_cases import IngestPerformanceDataUseCase
from src.infrastructure.repositories import SqlAlchemyPerformanceRepository

if __name__ == "__main__":
    data_path = Path(__file__).parent.parent / "data" / "sample_data.csv"
    if not data_path.exists():
        print(f"Sample data not found: {data_path}")
        sys.exit(1)
    repo = SqlAlchemyPerformanceRepository()
    use_case = IngestPerformanceDataUseCase(performance_repo=repo)
    count = use_case.execute_from_csv(data_path)
    print(f"Ingested {count} records")
