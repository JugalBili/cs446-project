from fastapi import APIRouter, Depends, UploadFile, Form, File, HTTPException, Response
from shared.data_classes import ColorDTO, ImageData
from pydantic import ValidationError
from shared.service.image_service import ImageService
from typing import Annotated
from Api.dependencies import get_image_service, get_user, get_image_server_client
from Api.repository.user_authentication_repository import User
from Api.client.image_server_client import ImageServerClient
import json

router = APIRouter(
    # specify sub-route. All routes in this file will be in the form of /login/{whatever}
    prefix="/image",
    # tags are strictly for metadata (helps with openAPI specifications)
    tags=["image"],
    # also metadata
    responses={401: {"description": "Incorrect Login information"}},
)


@router.get("/{image_hash}")
def get_image_by_hash(image_service: Annotated['ImageService', Depends(get_image_service)],
                    #   user: Annotated['User', Depends(get_user)],
                      image_hash: str
                      ):
    user = User(email="a@a.com", firstname="test", lastname="test", uid="test")
    image = image_service.get_image_by_hash(user.uid, image_hash)
    return Response(content=image.image_bytes, media_type=image.contentType)


@router.get("/list/{image_hash}")
def list_image_for_hash(image_service: Annotated['ImageService', Depends(get_image_service)],
                        # user: Annotated['User', Depends(get_user)],
                        image_hash: str
                        ):
    user = User(email="a@a.com", firstname="test", lastname="test", uid="test")
    return image_service.get_image_summary_by_hash(user.uid, image_hash)


@router.post("/")
async def upload_file(image_service: Annotated['ImageService', Depends(get_image_service)],
                    #   user: Annotated['User', Depends(get_user)],
                      file: UploadFile = File(...),
                      colors: str = Form(...)):
    try:
        raw_colors = json.loads(colors)
        color_list = [ColorDTO(**color) for color in raw_colors]
    except (SyntaxError, ValidationError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid 'colors' input: {e}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"invalid color input: {e}")
    user = User(email="a@a.com", firstname="test", lastname="test", uid="test")
    return await image_service.upload_and_process_image(user.uid, file, color_list)