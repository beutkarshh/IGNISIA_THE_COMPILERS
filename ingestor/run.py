"""Entry point: python -m ingestor.run"""
import asyncio
from ingestor.vitals_ingestor import ingestion_loop

if __name__ == "__main__":
    asyncio.run(ingestion_loop())
