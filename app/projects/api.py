from fastapi import APIRouter, Depends

from app.common.auth import CurrentUser, get_current_user

router = APIRouter()


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "org_id": str(user.org_id),
        "roles": [r.value for r in user.roles],
    }
