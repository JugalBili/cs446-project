from Api.config import Settings
from shared.data_classes import ImageData, GetProcessedResponse
from fastapi import HTTPException
from pydantic import ValidationError
import requests

class ImageServerClient:
    def __init__(self, env: Settings):
        self.base_url = env.image_server_url

    def send_image_process_request(self, image_data: ImageData):
        json_data = image_data.model_dump_json()
        url = self.base_url + "/image/generate"
        try:
            print("sending request to: ", url)
            print("sending data: ", json_data)
            resp  = requests.post(url, data=json_data, headers={"Content-Type": "application/json"}, timeout=15)
            resp.raise_for_status()
            processed_data = resp.json()
            print("received data from server: ", processed_data)
            processed_resp = [GetProcessedResponse(**image_response) for image_response in processed_data]
            return processed_resp
        except ValidationError as e:
            HTTPException(status_code=500, detail=f"Internal server error when calling Image Processor: {e}")
        except requests.HTTPError as e:
            HTTPException(status_code=500, detail=f"Internal server error when calling Image Processor: {e}")
        except Exception as e:
            HTTPException(status_code=500, detail=f"Internal server error when calling Image Processor: {e}")



