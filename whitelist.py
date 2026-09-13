# whitelist.py — белый список пользователей для аудио (save/forward)
# Логика: аудио уходит с protect_content=True, ТОЛЬКО если получателя нет в списке.
# Хранилище читается при КАЖДОЙ отправке — обновление без перезапуска бота.
# Бэкенды: json (по умолчанию) | sqlite | postgres (переключение через .env)
import json
import os
import sqlite3
from config import ADMINS

CREATOR_ID = int(os.getenv("CREATOR_ID") or (ADMINS[0] if ADMINS else 0))
MANAGE_IDS = set(ADMINS) | {CREATOR_ID}   # кто может управлять списком

BACKEND = os.getenv("WHITELIST_BACKEND", "json")   # json | sqlite | postgres
JSON_FILE = "allowed_users.json"
SQLITE_FILE = "allowed_users.db"
PG_DSN = os.getenv("PG_DSN", "")

# ---------- JSON-хранилище (нет БД — по спеке) ----------
class JsonStorage:
    def _load(self):
        if not os.path.exists(JSON_FILE):
            return []
        try:
            with open(JSON_FILE, encoding="utf-8") as f:
                return [int(x) for x in json.load(f)]
        except Exception:
            return []
    def _save(self, ids):
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(ids, f)
    def is_allowed(self, uid):
        return int(uid) in self._load()          # чтение файла при каждом вызове
    def add(self, uid):
        ids = self._load()
        if int(uid) not in ids:
            ids.append(int(uid))
            self._save(ids)
        return True
    def remove(self, uid):
        ids = self._load()
        if int(uid) in ids:
            ids.remove(int(uid))
            self._save(ids)
            return True
        return False
    def list_all(self):
        return self._load()

# ---------- SQLite-хранилище ----------
class SqliteStorage:
    def _conn(self):
        con = sqlite3.connect(SQLITE_FILE)
        con.execute("CREATE TABLE IF NOT EXISTS allowed_users "
                    "(user_id INTEGER PRIMARY KEY)")
        return con
    def is_allowed(self, uid):
        con = self._conn()
        try:
            return con.execute("SELECT 1 FROM allowed_users WHERE user_id=?",
                               (int(uid),)).fetchone() is not None
        finally:
            con.close()
    def add(self, uid):
        con = self._conn()
        try:
            con.execute("INSERT OR IGNORE INTO allowed_users VALUES (?)", (int(uid),))
            con.commit()
            return True
        finally:
            con.close()
    def remove(self, uid):
        con = self._conn()
        try:
            cur = con.execute("DELETE FROM allowed_users WHERE user_id=?", (int(uid),))
            con.commit()
            return cur.rowcount > 0
        finally:
            con.close()
    def list_all(self):
        con = self._conn()
        try:
            return [r[0] for r in con.execute("SELECT user_id FROM allowed_users")]
        finally:
            con.close()

# ---------- PostgreSQL (готово к переходу: pip install psycopg2-binary) ----------
class PostgresStorage:
    def _conn(self):
        import psycopg2  # ленивый импорт: бот работает без драйвера
        con = psycopg2.connect(PG_DSN)
        con.autocommit = True
        with con.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS allowed_users "
                        "(user_id BIGINT PRIMARY KEY)")
        return con
    def is_allowed(self, uid):
        con = self._conn()
        try:
            with con.cursor() as cur:
                cur.execute("SELECT 1 FROM allowed_users WHERE user_id=%s", (int(uid),))
                return cur.fetchone() is not None
        finally:
            con.close()
    def add(self, uid):
        con = self._conn()
        try:
            with con.cursor() as cur:
                cur.execute("INSERT INTO allowed_users VALUES (%s) ON CONFLICT DO NOTHING",
                            (int(uid),))
            return True
        finally:
            con.close()
    def remove(self, uid):
        con = self._conn()
        try:
            with con.cursor() as cur:
                cur.execute("DELETE FROM allowed_users WHERE user_id=%s", (int(uid),))
                return cur.rowcount > 0
        finally:
            con.close()
    def list_all(self):
        con = self._conn()
        try:
            with con.cursor() as cur:
                cur.execute("SELECT user_id FROM allowed_users")
                return [r[0] for r in cur.fetchall()]
        finally:
            con.close()

# ---------- Фабрика бэкендов ----------
_storage = None
def get_storage():
    global _storage
    if _storage is None:
        if BACKEND == "sqlite":
            _storage = SqliteStorage()
        elif BACKEND == "postgres":
            try:
                st = PostgresStorage()
                st.list_all()          # проверка соединения
                _storage = st
            except Exception as e:
                print(f"⚠️ PostgreSQL недоступен ({e}) — fallback на JSON")
                _storage = JsonStorage()
        else:
            _storage = JsonStorage()
    return _storage

def is_allowed(uid):
    return get_storage().is_allowed(uid)

# ---------- Безопасная отправка АУДИО ----------
async def send_audio_safe(context, chat_id, audio, **kwargs):
    """protect_content=True всем, КРОМЕ белого списка. Только для аудио!"""
    kwargs.pop("protect_content", None)
    # Большие медиа на мобильной сети требуют долгих таймаутов
    kwargs.setdefault("write_timeout", 120)
    kwargs.setdefault("read_timeout", 60)
    kwargs.setdefault("connect_timeout", 30)
    protect = not is_allowed(chat_id)
    last_err = None
    for attempt in (1, 2):
        try:
            return await context.bot.send_audio(
                chat_id=chat_id, audio=audio,
                protect_content=protect, **kwargs)
        except Exception as e:
            last_err = e
            print(f"⚠️ [whitelist] попытка {attempt} не удалась: {e}")
            if attempt == 1:
                try:
                    audio.seek(0)   # rewind файла перед ретраем
                except Exception:
                    pass
    raise last_err

# ---------- Админ-команды ----------
def _parse_id(text):
    try:
        return int(str(text).strip())
    except (ValueError, TypeError):
        return None

async def allow_command(update, context):
    if update.effective_user.id not in MANAGE_IDS:
        await update.message.reply_text("⛔ Недоступно!")
        return
    if not context.args:
        await update.message.reply_text("📝 Формат: /allow <user_id>")
        return
    uid = _parse_id(context.args[0])
    if uid is None:
        await update.message.reply_text("❌ Введи числовой ID!")
        return
    get_storage().add(uid)
    await update.message.reply_text(
        f"✅ ID {uid} в белом списке: аудио ему придёт БЕЗ защиты (можно сохранять/пересылать)")

async def deny_command(update, context):
    if update.effective_user.id not in MANAGE_IDS:
        await update.message.reply_text("⛔ Недоступно!")
        return
    if not context.args:
        await update.message.reply_text("📝 Формат: /deny <user_id>")
        return
    uid = _parse_id(context.args[0])
    if uid is None:
        await update.message.reply_text("❌ Введи числовой ID!")
        return
    if get_storage().remove(uid):
        await update.message.reply_text(f"🗑️ ID {uid} удалён из белого списка")
    else:
        await update.message.reply_text(f"ℹ️ ID {uid} и так не в списке")

async def list_allowed_command(update, context):
    if update.effective_user.id not in MANAGE_IDS:
        await update.message.reply_text("⛔ Недоступно!")
        return
    ids = get_storage().list_all()
    backend = type(get_storage()).__name__
    if not ids:
        await update.message.reply_text(f"📋 Белый список пуст (хранилище: {backend})")
    else:
        await update.message.reply_text(
            f"📋 Белый список ({backend}):\n" + "\n".join(f"• {i}" for i in ids))


async def send_voice_safe(context, chat_id, voice, **kwargs):
    """Голосовое сообщение с protect_content по белому списку"""
    kwargs.pop("protect_content", None)
    kwargs.setdefault("write_timeout", 120)
    kwargs.setdefault("read_timeout", 60)
    kwargs.setdefault("connect_timeout", 30)
    protect = not is_allowed(chat_id)
    last_err = None
    for attempt in (1, 2):
        try:
            return await context.bot.send_voice(
                chat_id=chat_id, voice=voice,
                protect_content=protect, **kwargs)
        except Exception as e:
            last_err = e
            print(f"⚠️ [whitelist voice] попытка {attempt}: {e}")
            if attempt == 1:
                try:
                    voice.seek(0)
                except Exception:
                    pass
    raise last_err
