import asyncio
from urllib.parse import urlparse, parse_qs

from telethon import TelegramClient
from telethon.network import ConnectionTcpFull


async def check_one(server, port, secret, api_id, api_hash, timeout=5):
    """Проверить один MTProto-прокси через Telethon.

    Returns True, если удалось установить соединение.
    """
    client = TelegramClient(
        ":memory:", api_id, api_hash,
        proxy=(server, int(port), secret),
        connection=ConnectionTcpFull,
    )
    try:
        await client.connect(timeout=timeout)
        return True
    except Exception:
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def check_all(lines, api_id, api_hash, max_concurrent=10, timeout=5):
    """Проверить список proxy-URL.

    Возвращает список кортежей (строка, жива_ли).
    """
    sem = asyncio.Semaphore(max_concurrent)

    async def _check(line):
        parsed = urlparse(line.strip())
        params = parse_qs(parsed.query)
        server = params.get("server", [""])[0]
        port = params.get("port", [""])[0]
        secret = params.get("secret", [""])[0]
        if not server or not port or not secret:
            return (line, False)
        async with sem:
            ok = await check_one(server, port, secret, api_id, api_hash, timeout)
            return (line, ok)

    results = await asyncio.gather(*[_check(l) for l in lines], return_exceptions=True)

    out = []
    for r in results:
        if isinstance(r, Exception):
            continue
        out.append(r)
    return out
