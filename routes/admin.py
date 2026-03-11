from fastapi import APIRouter, Depends
from database import user_collection
from models.user import UserResponse
from middleware.auth import require_role
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(require_role("admin"))):
    """
    Get all registered users from MongoDB. Admin only.
    """
    users = await user_collection.find().to_list(length=None)
    result = []
    for user in users:
        result.append(
            UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                name=user["name"],
                role=user["role"],
            )
        )
    return result


@router.get("/users/count")
async def get_user_count(admin: dict = Depends(require_role("admin"))):
    """
    Get total count of registered users. Admin only.
    """
    count = await user_collection.count_documents({})
    return {"count": count}
