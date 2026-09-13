# proxy_manager.py — управление прокси для Telegram бота
import random
import time
from config import PROXY_URL, PROXY_LIST, PROXY_FALLBACK

_current = PROXY_URL
_failures = {}   # proxy_url -> (count, last_fail_time)
_MAX_FAILURES = 3
_COOLDOWN = 300  # 5 мин после 3 фейлов

def _alive(proxy):
    if not proxy:
        return True
    f = _failures.get(proxy)
    if not f:
        return True
    cnt, ts = f
    if cnt < _MAX_FAILURES:
        return True
    return (time.time() - ts) > _COOLDOWN

def get_proxy():
    """Возвращает живой прокси (или None если все мертвы/отключены)"""
    global _current
    candidates = [PROXY_URL] + PROXY_LIST if PROXY_URL else list(PROXY_LIST)
    candidates = [p for p in candidates if p and _alive(p)]
    if not candidates:
        return None
    # Предпочитаем текущий если он жив, иначе случайный
    if _current in candidates:
        return _current
    _current = random.choice(candidates)
    return _current

def mark_failed(proxy):
    """Отмечаем прокси как упавший"""
    if not proxy:
        return
    cnt, _ = _failures.get(proxy, (0, 0))
    _failures[proxy] = (cnt + 1, time.time())
    print(f"⚠️ Прокси упал ({cnt+1}/{_MAX_FAILURES}): {proxy}")

def mark_ok(proxy):
    if not proxy:
        return
    _failures.pop(proxy, None)

def can_fallback():
    return PROXY_FALLBACK

def format_for_ptb(proxy):
    """Формат для python-telegram-bot: возвращает dict с параметрами proxy"""
    if not proxy:
        return {}
    return {"proxy_url": proxy}
