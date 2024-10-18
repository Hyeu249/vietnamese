from odoo.http import request
import qrcode
import base64
from io import BytesIO

SHIP_MANAGEMENT = "SHIP_MANAGEMENT"
DOCKING = "DOCKING"


def validate_access_token(type, get_params=False):
    params = request.get_http_params()
    access_token = params.get("access_token")
    supplier_ref = params.get("supplier_ref")
    model = None

    if type == SHIP_MANAGEMENT:
        model = "ship.supplier"
    elif type == DOCKING:
        model = "docking.supplier"

    supplier = request.env[model].sudo().search([("ref", "=", supplier_ref)])
    is_validate = access_token == supplier.access_token

    if is_validate:
        if get_params:
            return (True, supplier, access_token, supplier_ref)
        else:
            return (True, supplier)
    else:
        if get_params:
            return (False, supplier, access_token, supplier_ref)
        else:
            return (False, supplier)


def generate_qr_code_base64(data):
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Add the data to the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert the image to a byte stream
    img_buffer = BytesIO()
    qr_img.save(img_buffer, format="PNG")

    # Encode the image as base64
    base64_image = base64.b64encode(img_buffer.getvalue()).decode()

    return base64_image
