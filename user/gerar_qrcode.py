import qrcode
import base64
from io import BytesIO


def gerar_qr_code_base64(texto):
    # Cria um objeto QRCode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(texto)
    qr.make(fit=True)

    # Cria uma imagem PIL do QR Code
    img = qr.make_image(fill_color="black", back_color="white")

    # Salva a imagem em bytes
    buffered = BytesIO()
    img.save(buffered, format="PNG")

    # Converte os bytes da imagem para base64
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_str


# if __name__ == "__main__":
#     texto = "c27d38ec-76ff-425b-ad52-31575ad06986"
#     qr_base64 = gerar_qr_code_base64(texto)
#     print(f"QR Code em base64:\n{qr_base64}")
