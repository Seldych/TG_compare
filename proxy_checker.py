import socket
import ssl
import concurrent.futures
from urllib.parse import urlparse, parse_qs


def _decode_secret(secret_hex):
    """Декодировать hex-секрет, вернуть (bytes, is_tls)."""
    raw = bytes.fromhex(secret_hex)
    is_tls = raw[0] != 0xee if len(raw) > 0 else False
    return raw, is_tls


def check_one(server, port, secret, timeout=5):
    """Проверить один MTProto-прокси через TCP/TLS сокет."""
    try:
        secret_bytes, is_tls = _decode_secret(secret)
    except (ValueError, IndexError):
        return False

    sock = None
    try:
        sock = socket.create_connection((server, int(port)), timeout=timeout)
        sock.settimeout(2)

        if is_tls:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=server)

        sock.sendall(secret_bytes)

        try:
            data = sock.recv(16)
            return len(data) > 0
        except socket.timeout:
            return True
        except ConnectionResetError:
            return False

    except Exception:
        return False
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def check_all_socket(lines, max_concurrent=10, timeout=5):
    """Проверить список proxy-URL через сокеты (без внешних зависимостей).

    Возвращает список кортежей (строка, жива_ли).
    """
    def _check(line):
        parsed = urlparse(line.strip())
        params = parse_qs(parsed.query)
        server = params.get("server", [""])[0]
        port = params.get("port", [""])[0]
        secret = params.get("secret", [""])[0]
        if not server or not port or not secret:
            return (line, False)
        ok = check_one(server, port, secret, timeout)
        return (line, ok)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_concurrent
    ) as pool:
        results = list(pool.map(_check, lines))

    return results


def check_all_telethon(lines, api_id, api_hash, max_concurrent=10, timeout=5):
    """Проверка через Telethon — заглушка.

    Требует api_id и api_hash с https://my.telegram.org/apps.
    Реализуется при получении ключей.
    """
    raise NotImplementedError(
        "Telethon-проверка требует настройки API Telegram.\n"
        "Получите api_id и api_hash на https://my.telegram.org/apps\n"
        "и введите их в настройках приложения."
    )
