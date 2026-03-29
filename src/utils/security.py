import base64

def encode_password(password: str) -> str:
    """Şifreyi Base64 formatına çevirir."""
    if not password:
        return ""
    bytes_pwd = password.encode('utf-8')
    encoded_pwd = base64.b64encode(bytes_pwd)
    return encoded_pwd.decode('utf-8')

def decode_password(encoded_password: str) -> str:
    """Base64 formatındaki şifreyi çözer."""
    if not encoded_password:
        return ""
    try:
        bytes_pwd = encoded_password.encode('utf-8')
        decoded_pwd = base64.b64decode(bytes_pwd)
        return decoded_pwd.decode('utf-8')
    except Exception:
        return ""
