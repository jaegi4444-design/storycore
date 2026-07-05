"""QR 이미지 생성."""

from __future__ import annotations

import io

import qrcode
import qrcode.image.svg


def generate_qr_svg(url: str) -> bytes:
    qr = qrcode.QRCode(
        image_factory=qrcode.image.svg.SvgPathImage,
        border=1,
        box_size=8,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()
