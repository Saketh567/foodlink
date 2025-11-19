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
    Parse QR code or barcode data and extract client number
    
    Args:
        qr_data: QR code or barcode scanned data
    
    Returns:
        Client number or None if invalid
    """
    if not qr_data:
        return None
    
    qr_data = qr_data.strip()
    
    # Handle CLIENT: prefix format
    if qr_data.startswith("CLIENT:"):
        return qr_data.replace("CLIENT:", "").strip()
    
    # Handle raw client numbers with format FL-XXX
    if "-" in qr_data and len(qr_data.split("-")) == 2:
        parts = qr_data.split("-")
        if len(parts) == 2 and parts[0].isalpha() and parts[1].isdigit():
            return qr_data
    
    # Handle numeric barcodes - assume they're client IDs and format as FL-XXX
    if qr_data.isdigit():
        # Format as FL-XXX (pad with zeros)
        return f"FL-{qr_data.zfill(3)}"
    
    # Try to extract client number from various formats
    # Handle cases like "FL001" (no dash)
    if len(qr_data) >= 3 and qr_data[:2].isalpha() and qr_data[2:].isdigit():
        return f"{qr_data[:2]}-{qr_data[2:]}"
    
    return None

