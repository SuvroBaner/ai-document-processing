from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def plans_health() -> dict:
    return {"ok": True, "note": "stub for slice"}
