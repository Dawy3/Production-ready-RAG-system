import base64
import io
from mistralai import Mistral
from PIL import Image
from helpers.config import get_settings


class MistralProvider:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)

    def recognize_text(self, image: Image.Image):
        """
        Recognize text from a PIL.Image object.
        image: already processed PIL.Image
        Returns: OCR response from Mistral
        """

        # Convert image to JPEG bytes
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG")
        img_bytes = buffer.getvalue()

        # Encode as base64
        b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Send to Mistral OCR
        ocr_response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",  # base64 can be sent as an image_url
                "image_url": f"data:image/jpeg;base64,{b64}",
            },
            include_image_base64=False,
        )

        return ocr_response