import socket

def test_connection(ip: str, port: int, timeout: int = 3) -> bool:
    """
    Belirli bir IP adresi ve porta TCP üzerinden bağlanmayı dener.
    Bağlantı başarılıysa True, başarısız veya timeout olduysa False döner.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Network error: {e}")
        return False
