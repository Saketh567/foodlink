import json
import os

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


def decode_qr(image_path):
    """
    Decode a QR code image and return the decoded JSON payload as a dict.
    Returns None when the image cannot be parsed or does not contain JSON.
    """
    try:
        img = Image.open(image_path)
        result = decode(img)

        if not result:
            return None

        raw_data = result[0].data.decode("utf-8")
        data = json.loads(raw_data)

        if isinstance(data, dict):
            return data
    except Exception:
        return None

    return None


def generate_client_qr(client_id, client_number, save_dir):
    """
    Generates (if necessary) a QR code image for a client.
    """
    payload = {
        "client_id": client_id,
        "client_number": client_number,
    }

    qr_text = json.dumps(payload)

    os.makedirs(save_dir, exist_ok=True)

    filename = f"client_{client_id}.png"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        return filename

    img = qrcode.make(qr_text)
    img.save(filepath)

    return filename
