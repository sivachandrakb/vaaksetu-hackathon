"""VaakSetu — Real-Time Datasets API"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()
MOCK_DIR = Path(__file__).parent.parent / "mock_data"

@router.get("/{source}")
async def get_dataset(source: str):
    """Return mock data for a specific government data source."""
    valid = {"seva_sindhu", "bbmp", "bwssb", "bhoomi", "crm_logs"}
    if source not in valid:
        raise HTTPException(404, f"Unknown source. Valid: {', '.join(valid)}")
    path = MOCK_DIR / f"{source}.json"
    if not path.exists():
        raise HTTPException(404, "Data file not found")
    with open(path) as f:
        return json.load(f)

@router.get("/")
async def list_datasets():
    return {
        "available": ["seva_sindhu", "bbmp", "bwssb", "bhoomi", "crm_logs"],
        "note": "These are mock datasets simulating real-time government API feeds"
    }
