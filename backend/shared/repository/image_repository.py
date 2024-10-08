import hashlib
import io
import json
import zipfile
from typing import List
from firebase_admin import storage
from google.cloud.storage import Blob
from fastapi import UploadFile, HTTPException
from shared.data_classes import (
    RGB,
    GetImageResponse,
    ColorDTO,
    Image,
    GetJSONResponse,
    GetMaskResponse,
)


class ImageRepository:
    def __init__(self) -> None:
        self.bucket = storage.bucket()
        self.base_collection_name = "images"
        self.processed_image_path = "processed"
        self.masks_path = "masks"
        self.metadata_exception = HTTPException(
            status_code=500, detail="Error encountered: invalid metadata"
        )

    async def upload_unprocessed_image(self, uid: str, file: UploadFile):
        await file.seek(0)
        content = await file.read()
        image_hash = hashlib.sha256(content).hexdigest()
        base_path = f"{self.base_collection_name}/{uid}/{image_hash}"
        image_path = f"{base_path}/{image_hash}"
        blob = self.bucket.blob(image_path)

        # TODO Update History here (Add New entry or update existing one)
        if blob.exists():
            return image_hash
        content_file = io.BytesIO(content)
        blob.upload_from_file(content_file, content_type=file.content_type)
        blob.make_private()
        return image_hash

    @staticmethod
    def _create_metadata(upload_request: ColorDTO):
        return {
            "r": upload_request.rgb.r,
            "g": upload_request.rgb.g,
            "b": upload_request.rgb.b,
            "paint_id": upload_request.paint_id,
        }

    @staticmethod
    def _parse_metadata_from_blob(blob: Blob):
        blob.reload()
        metadata = blob.metadata
        if metadata is None:
            return None, None, None, None
        r = metadata.get("r", None)
        g = metadata.get("g", None)
        b = metadata.get("b", None)
        paintId = metadata.get("paint_id", None)
        return r, g, b, paintId

    async def upload_processed_image(
        self, uid: str, raw_image_hash: str, image_bytes, dto: ColorDTO
    ):
        base_path = f"{self.base_collection_name}/{uid}/{raw_image_hash}/{self.processed_image_path}"
        processed_image_hash = f"{raw_image_hash}-{dto.paint_id}"
        image_path = f"{base_path}/{processed_image_hash}"
        blob = self.bucket.blob(image_path)
        if blob.exists():
            return processed_image_hash
        blob.metadata = self._create_metadata(dto)
        blob.upload_from_string(image_bytes, content_type="image/jpg")
        blob.make_private()

        return processed_image_hash

    async def upload_masks(
        self, uid: str, raw_image_hash: str, buffers: list[io.BytesIO]
    ):
        uploaded_mask_hashes = []
        for i in range(len(buffers)):
            base_path = (
                f"{self.base_collection_name}/{uid}/{raw_image_hash}/{self.masks_path}"
            )
            file_name = f"{raw_image_hash}-{i}"
            image_path = f"{base_path}/{file_name}"

            buffers[i].seek(0)
            blob = self.bucket.blob(image_path)

            blob.upload_from_file(buffers[i], content_type="image/bmp")
            blob.make_private()
            uploaded_mask_hashes.append(file_name)

        return uploaded_mask_hashes

    @staticmethod
    def _get_mask_from_blob(blob: Blob):
        bmp_buffer = io.BytesIO()
        blob.download_to_file(bmp_buffer)
        bmp_buffer.seek(0)

        return bmp_buffer

    def get_masks_by_hash(
        self, uid: str, image_hash: str, mask_hashes: list[str]
    ) -> None | List[GetMaskResponse]:
        mask_responses = []

        base_path = f"{self.base_collection_name}/{uid}/{image_hash}/{self.masks_path}"

        for i in range(len(mask_hashes)):
            file_name = f"{mask_hashes[i]}"
            mask_path = f"{base_path}/{file_name}"
            blob = self.bucket.blob(mask_path)
            if not blob.exists():
                pass
            buffer = self._get_mask_from_blob(blob)
            blob.make_private()

            response = GetMaskResponse(image_hash=image_hash, mask_data=buffer)
            mask_responses.append(response)

        return mask_responses

    async def upload_json(self, uid: str, raw_image_hash: str, json_dict: dict):
        base_path = f"{self.base_collection_name}/{uid}/{raw_image_hash}"
        file_name = f"{raw_image_hash}.json"
        image_path = f"{base_path}/{file_name}"

        json_str = json.dumps(json_dict)
        blob = self.bucket.blob(image_path)

        blob.upload_from_string(
            json_str.encode("utf-8"), content_type="application/json"
        )
        blob.make_private()
        return GetJSONResponse(image_hash=raw_image_hash)

    @staticmethod
    def _get_json_from_blob(blob: Blob) -> dict:
        json_string = blob.download_as_string().decode("utf-8")
        dict_obj = json.loads(json_string)

        return dict_obj

    def get_json_by_hash(self, uid: str, image_hash: str) -> None | GetJSONResponse:
        base_path = f"{self.base_collection_name}/{uid}/{image_hash}/"
        file_name = f"{image_hash}.json"
        base_path += file_name
        blob = self.bucket.blob(base_path)
        if not blob.exists():
            return None
        obj = self._get_json_from_blob(blob)
        blob.make_private()

        return GetJSONResponse(image_hash=image_hash, json_data=obj)

    @staticmethod
    def _get_image_from_blob(blob: Blob) -> Image:
        image_bytes = blob.download_as_bytes()

        return Image(image_bytes=image_bytes, contentType=blob.content_type)

    def get_raw_image_by_hash(
        self, uid: str, image_hash: str, download_image: bool = False
    ) -> None | GetImageResponse:
        base_path = f"{self.base_collection_name}/{uid}/{image_hash}/"
        file_name = f"{image_hash}"
        base_path += file_name
        blob = self.bucket.blob(base_path)
        if not blob.exists():
            return None
        if download_image:
            raw_image = self._get_image_from_blob(blob)
        else:
            raw_image = None
        blob.make_private()
        return GetImageResponse(
            image_hash=image_hash, rgb=None, paintId=None, image_data=raw_image
        )

    def get_processed_image_by_hash(
        self, uid: str, image_hash: str, download_image: bool = False
    ) -> None | GetImageResponse:
        raw_hash = image_hash.split("-")[0]
        path = f"{self.base_collection_name}/{uid}/{raw_hash}/{self.processed_image_path}/{image_hash}"
        blob = self.bucket.blob(path)
        if not blob.exists():
            return None
        # If Image exists with no metadata, what do we do? (probably wouldn't even)
        # Get data we can?
        # Cancel the request?
        # Dont return images without metadata?
        r, g, b, paintId = self._parse_metadata_from_blob(blob)
        if not r or not g or not b or not paintId:
            raise self.metadata_exception
        if download_image:
            raw_image = self._get_image_from_blob(blob)
        else:
            raw_image = None
        blob.make_private()
        return GetImageResponse(
            image_hash=image_hash,
            rgb=RGB(r=r, g=g, b=b),
            paintId=paintId,
            image_data=raw_image,
        )

    def check_image_exists_for_id(self, uid: str, image_hash: str, dto: ColorDTO):
        file_name = f"{image_hash}-{dto.paint_id}"
        return self.get_processed_image_by_hash(uid, file_name)

    def get_all_processed_images(self, uid: str, raw_hash: str):
        path = (
            f"{self.base_collection_name}/{uid}/{raw_hash}/{self.processed_image_path}"
        )
        blobs = self.bucket.list_blobs(prefix=path)
        if not blobs:
            return []
        ret: List[GetImageResponse] = []
        for blob in blobs:
            filename = blob.name.split("/")[-1]
            r, g, b, paintId = self._parse_metadata_from_blob(blob)
            blob.make_private()
            ret.append(
                GetImageResponse(
                    image_hash=filename, rgb=RGB(r=r, g=g, b=b), paintId=paintId
                )
            )
        return ret
    @staticmethod
    def _get_content_type_extension(content_type: str):
        # expect type of type/file_extension
        return content_type.split("/")[-1]
    def bulk_retrieve_images_from_raw_image_hash(self, uid: str, raw_image_hash: str) -> io.BytesIO | None:
        base_path = f"{self.base_collection_name}/{uid}/{raw_image_hash}"
        file_name = f"{raw_image_hash}"
        raw_image_path = f"{base_path}/{file_name}"
        raw_image_blob = self.bucket.blob(raw_image_path)
        if not raw_image_blob.exists():
            return None
        processed_image_collection_path = f"{base_path}/{self.processed_image_path}"
        processed_image_blobs = self.bucket.list_blobs(prefix=processed_image_collection_path)

        zip_data = io.BytesIO()
        with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
            raw_image_blob.reload()
            file_type = self._get_content_type_extension(raw_image_blob.content_type)
            raw_image_content = raw_image_blob.download_as_bytes()

            zipf.writestr(zipfile.ZipInfo(f"{raw_image_hash}.{file_type}"), raw_image_content)

            for processed_blob in processed_image_blobs:
                processed_blob.reload()
                file_type = self._get_content_type_extension(processed_blob.content_type)
                filename = processed_blob.name.split("/")[-1]
                blob_content = processed_blob.download_as_bytes()
                zip_info = zipfile.ZipInfo(f"{filename}.{file_type}")
                zipf.writestr(zip_info, blob_content)
        
        zip_data.seek(0)
        return zip_data