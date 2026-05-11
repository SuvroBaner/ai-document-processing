from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def output_health() -> dict:
    return {"ok": True, "adapters": ["pdf_transmittal"]}
