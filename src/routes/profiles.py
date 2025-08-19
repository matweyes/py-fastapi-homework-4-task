from fastapi import APIRouter, UploadFile, File, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select
from config import get_s3_storage_client, get_jwt_auth_manager
from schemas.profiles import ProfileCreateData, ProfileResponseSchema
from database import get_db, UserModel, UserGroupEnum, UserProfileModel
from security.interfaces import JWTAuthManagerInterface
from security.http import get_token
from storages import S3StorageInterface
import os
from validation import validate_image

router = APIRouter()


# Write your code here
@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
        user_id: int,
        request: Request,
        user: ProfileCreateData = Depends(ProfileCreateData.as_form),
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        s3_client: S3StorageInterface = Depends(get_s3_storage_client),

):
    # 1) Token validation
    token = get_token(request)
    try:
        payload = jwt_manager.decode_access_token(token)
    except Exception as e:
        # align test message for expiration
        msg = str(e)
        if "expired" in msg.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    # We support either "user_id" or "sub" claim (match what your tokens contain)
    auth_user_id = payload.get("user_id") or payload.get("sub")
    try:
        auth_user_id = int(auth_user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    # 2) Authorization: only self unless admin
    # Load authenticated user (the caller)
    auth_user_q = await db.execute(select(UserModel).where(UserModel.id == auth_user_id))
    auth_user = auth_user_q.scalar_one_or_none()
    if not auth_user or not auth_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active.")

    is_admin = getattr(auth_user, "group", None) in (getattr(UserGroupEnum, "ADMIN", None), getattr(UserGroupEnum, "SUPERUSER", None))
    if (auth_user.id != user_id) and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to edit this profile.")

    # 3) Target user existence & status
    user_q = await db.execute(select(UserModel).where(UserModel.id == user_id))
    target_user = user_q.scalar_one_or_none()
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active.")

    # 4) Existing profile check
    existing_q = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == user_id))
    existing_profile = existing_q.scalar_one_or_none()
    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a profile.")

    # 5) Validate fields (non-file) via schema
    data = ProfileCreateData(
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        date_of_birth=user.date_of_birth,
        info=user.info,
    )
