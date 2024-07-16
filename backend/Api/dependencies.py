from functools import lru_cache
from Api.config import Settings
from fastapi import Request, HTTPException, Depends
from typing import Annotated

from Api.repository.history_repository import HistoryRepository
from Api.repository.user_authentication_repository import UserAuthenticationRepository
from Api.service.history_service import HistoryService
from Api.service.user_authentication_service import UserAuthenticationService
from shared.repository.image_repository import ImageRepository
from shared.service.image_service import ImageService
from Api.client.image_server_client import ImageServerClient


@lru_cache()
def getEnv():
    return Settings()


def get_authentication_repository(env: Annotated[Settings, Depends(getEnv)]):
    return UserAuthenticationRepository(env)


def get_authentication_service(
    repository: Annotated[
        "UserAuthenticationRepository", Depends(get_authentication_repository)
    ]
):
    return UserAuthenticationService(repository)


def get_image_repository():
    return ImageRepository()


def get_image_server_client(env: Annotated[Settings, Depends(getEnv)]):
    return ImageServerClient(env=env)


def get_image_service(
    repository: Annotated["ImageRepository", Depends(get_image_repository)],
    client: Annotated["ImageServerClient", Depends(get_image_server_client)],
):
    return ImageService(repository, client)


def get_history_repository():
    return HistoryRepository()


def get_history_service(
    repository: Annotated["HistoryRepository", Depends(get_history_repository)]
):
    return HistoryService(repository)


def get_auth_token(request: Request):
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(status_code=401)
    return token


async def get_user(
    token: Annotated[str, Depends(get_auth_token)],
    authentication_service: Annotated[
        "UserAuthenticationService", Depends(get_authentication_service)
    ],
):
    return await authentication_service.authenticate_user(token)
