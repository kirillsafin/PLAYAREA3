import logging
import os

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.models.profile import ProfileModel
from api.models.user import UserModel
from api.schemas.profile import BaseProfileDto, GetProfileDto, PutProfileDto
from api.schemas.user import CreateUserDto, GetUserEmailAndUsernameDto
from fastapi import UploadFile


class UserService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info("UserService created")
        self.__password_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )

    def __hash_password(self, password):
        return self.__password_context.hash(password)

# user
    def create_user(self, db_session: Session, create_user: CreateUserDto) -> None:
        # check if create_user.username and create_user.email is none or empty
        if not create_user.username and not create_user.email:
            raise Exception("Username and email cannot be empty")

        try:
            user: UserModel = UserModel(
                username=create_user.username,
                email=create_user.email,
                password=self.__hash_password(
                    create_user.password) if create_user.password else create_user.password,
                is_superuser=create_user.is_superuser,
                profile=ProfileModel(),
            )

            db_session.add(user)
            db_session.commit()
        except Exception as e:
            raise e

    def find_user_by_id(self, db_session: Session, user_id: int) -> GetUserEmailAndUsernameDto:
        try:
            user: UserModel = db_session.query(UserModel).filter(
                UserModel.id == user_id).one()
        except Exception as e:
            raise e

        return GetUserEmailAndUsernameDto(
            username=user.username,
            email=user.email
        )
    def add_profile_picture(self, db_session: Session, user_id: int, profile_picture: UploadFile) -> BaseProfileDto:
        # create dir for file upload if not exist
        os.makedirs(f'static/{user_id}', exist_ok=True)
        # save file to dir
        with open(f'static/{user_id}/{profile_picture.filename}', 'wb') as f:
            f.write(profile_picture.file.read())
        # save file path to db
        try:
            # add string to array field `images` in profile table for user with id user_id, use update() and where() methods on db_session
            profile: ProfileModel = db_session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id)).scalars().one()
            profile.images = profile.images + [f'static/{user_id}/{profile_picture.filename}']

            db_session.commit()
            return BaseProfileDto(
                id=profile.id,
                dark_theme=profile.dark_theme,
                images=profile.images,
                active_image=profile.active_image,
            )
        except Exception as e:
            db_session.rollback()
            os.remove(f'static/{user_id}/{profile_picture.filename}')
            raise e

    def update_profile(self, db_session: Session, user_id: int, put_profile: PutProfileDto) -> BaseProfileDto:
        try:
            profile: ProfileModel = db_session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id)).scalars().one()
            profile.dark_theme = put_profile.dark_theme
            profile.active_image = put_profile.active_image

            db_session.commit()
            return BaseProfileDto(
                id=profile.id,
                dark_theme=profile.dark_theme,
                images=profile.images,
                active_image=profile.active_image,
            )
        except Exception as e:
            db_session.rollback()
            raise e

    def get_profile_by_user_id(self, db_session: Session, user_id: int) -> GetProfileDto:
        try:
            profile: ProfileModel = db_session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id)).scalars().one()
            return GetProfileDto(
                id=profile.id,
                dark_theme=profile.dark_theme,
                images=profile.images,
                active_image=profile.active_image,
                user_id=profile.user_id,
            )
        except Exception as e:
            raise e
