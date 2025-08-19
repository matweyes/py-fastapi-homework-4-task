from database import UserModel, UserProfileModel
from schemas.profiles import ProfileCreateData
from fastapi import Form


def get_user_by_id(user_id) -> UserModel | None:
    ...


def get_user_profile(user_id) -> UserProfileModel | None:
    ...


def as_form(cls):
    def _as_form(
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: str = Form(...),
        date_of_birth: str = Form(...),
        info: str = Form(...),
    ) -> cls:
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info,
        )
    return _as_form

ProfileCreateData.as_form = classmethod(as_form)