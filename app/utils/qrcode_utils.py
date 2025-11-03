"""
QR Code Utility Functions
Generate and manage QR codes for client numbers
"""
import qrcode
import io
from flask import send_file
from app.database import query_db

def generate_qr_code(data, size=10, border=4):
    """
    Generate QR code image
    
    Args:
        data: Data to encode in QR code
        size: Box size (default: 10)
        border: Border thickness (default: 4)
    
    Returns:
        PIL Image object
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def generate_qr_code_bytes(data, size=10, border=4):
    """
    Generate QR code as bytes
    
    Args:
        data: Data to encode
        size: Box size
        border: Border thickness
    
    Returns:
        BytesIO object containing PNG image
    """
    img = generate_qr_code(data, size, border)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

def get_client_qr_data(client_number):
    """
    Get QR code data for a client
    Format: CLIENT:FL-001 (can be extended with more info)
    
    Args:
        client_number: Client number (e.g., FL-001)
    
    Returns:
        String data to encode in QR code
    """
    return f"CLIENT:{client_number}"

def parse_qr_data(qr_data):
    """
    Parse QR code data and extract client number
    
    Args:
        qr_data: QR code scanned data
    
    Returns:
        Client number or None if invalid
    """
    if qr_data.startswith("CLIENT:"):
        return qr_data.replace("CLIENT:", "")
    # Also accept raw client numbers
    if "-" in qr_data and len(qr_data.split("-")) == 2:
        return qr_data
    return None

