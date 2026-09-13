# faq.py v2 — ролевые справочники:
# игрок -> сразу игроцкий (без выбора)
# админ -> выбор: админский или игроцкий
# создатель -> выбор всех трёх
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMINS

CREATOR_ID = int(os.getenv("CREATOR_ID") or (ADMINS[0] if ADMINS else 0))

ABOUT = ("📜 О БОТЕ AVALON 📜\n"
         "Разработчик: @Fifenya\n"
         "Версия: 4.0 (Android)\n\n")

DOCS = {
    "player": ("🎮 Справочник игрока", "HANDBOOK_PLAYER.md"),
    "admin": ("🛡️ Справочник админа", "HANDBOOK_ADMIN.md"),
    "creator": ("👑 Справочник создателя", "HANDBOOK_CREATOR.md"),
}
PAGE_LIMIT = 3900

def _pretty(text):
    out = []
    for line in text.splitlines():
        line = line.replace("**", "").replace("`", "")
        line = re.sub(r"^#{1,6}\s*", "", line)
        out.append(line)
    return "\n".join(out)

def _load_pages(kind):
    entry = DOCS.get(kind)
    if not entry or not os.path.exists(entry[1]):
        return []
    with open(entry[1], encoding="utf-8") as f:
        text = _pretty(f.read())
    pages, cur = [], ""
    for line in text.splitlines(keepends=True):
        if len(cur) + len(line) > PAGE_LIMIT and cur:
            pages.append(cur)
            cur = ""
        cur += line
    if cur.strip():
        pages.append(cur)
    return pages

def _role(uid):
    if uid == CREATOR_ID:
        return "creator"
    if uid in ADMINS:
        return "admin"
    return "player"

def _allowed(kind, uid):
    role = _role(uid)
    if kind == "player":
        return True
    if kind == "admin":
        return role in ("admin", "creator")
    if kind == "creator":
        return role == "creator"
    return False

def _menu_kb(role):
    rows = [[InlineKeyboardButton("🎮 Игроку", callback_data="faq_player")]]
    if role in ("admin", "creator"):
        rows.append([InlineKeyboardButton("🛡️ Админу", callback_data="faq_admin")])
    if role == "creator":
        rows.append([InlineKeyboardButton("👑 Создателю", callback_data="faq_creator")])
    return InlineKeyboardMarkup(rows)

def _page_kb(kind, idx, total):
    row = []
    if idx > 0:
        row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"faq_nav_{kind}_{idx - 1}"))
    if idx < total - 1:
        row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"faq_nav_{kind}_{idx + 1}"))
    rows = ([row] if row else [])
    rows.append([InlineKeyboardButton("🔙 К списку справочников", callback_data="faq_back")])
    return InlineKeyboardMarkup(rows)

def _page_text(kind, pages, idx, prefix=""):
    footer = f"\n— {DOCS[kind][0]} | стр. {idx + 1}/{len(pages)} —"
    return prefix + pages[idx] + footer

async def _open_player(update, context, is_query, prefix=ABOUT):
    pages = context.user_data.get("faq_pages_player") or _load_pages("player")
    if not pages:
        msg = "❌ Справочник не найден: попроси создателя запустить make_docs.py"
        if is_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    context.user_data["faq_pages_player"] = pages
    text = _page_text("player", pages, 0, prefix)
    kb = _page_kb("player", 0, len(pages))
    if is_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Точка входа: /faq, кнопка '📚 Справочник', кнопка '📜 О боте'"""
    uid = update.effective_user.id
    role = _role(uid)
    is_query = update.callback_query is not None
    if role == "player":
        # обычному игроку — сразу игроцкий справочник, без выбора
        await _open_player(update, context, is_query)
        return
    header = ABOUT + "📚 СПРАВОЧНИКИ — выбери версию:"
    kb = _menu_kb(role)
    if is_query:
        await update.callback_query.edit_message_text(header, reply_markup=kb)
    else:
        await update.message.reply_text(header, reply_markup=kb)

async def faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id
    if data == "faq_back":
        role = _role(uid)
        if role == "player":
            await _open_player(update, context, True)
        else:
            await query.edit_message_text(
                ABOUT + "📚 СПРАВОЧНИКИ — выбери версию:", reply_markup=_menu_kb(role))
        return
    if data.startswith("faq_nav_"):
        _, _, kind, idx_s = data.split("_")
        if not _allowed(kind, uid):
            await query.answer("⛔ Нет доступа!", show_alert=True)
            return
        pages = context.user_data.get(f"faq_pages_{kind}") or _load_pages(kind)
        if not pages:
            await query.edit_message_text("❌ Справочник не найден: запусти make_docs.py")
            return
        idx = max(0, min(int(idx_s), len(pages) - 1))
        await query.edit_message_text(
            _page_text(kind, pages, idx), reply_markup=_page_kb(kind, idx, len(pages)))
        return
    kind = data.replace("faq_", "", 1)
    if not _allowed(kind, uid):
        await query.answer("⛔ Нет доступа!", show_alert=True)
        return
    pages = _load_pages(kind)
    if not pages:
        await query.edit_message_text(
            "❌ Справочник не найден: попроси создателя запустить make_docs.py")
        return
    context.user_data[f"faq_pages_{kind}"] = pages
    await query.edit_message_text(
        _page_text(kind, pages, 0), reply_markup=_page_kb(kind, 0, len(pages)))


# ===== Кнопка "📚 Справочник" в главном меню (безопасный wrapper) =====
import keyboards as _kb
from telegram import ReplyKeyboardMarkup as _RKM

_orig_main_kb = _kb.get_main_keyboard

def _main_kb_with_faq(location='city'):
    kb = _orig_main_kb(location)
    rows = [list(r) for r in kb.keyboard]
    rows.append(["📚 Справочник"])
    return _RKM(rows, resize_keyboard=True)

_kb.get_main_keyboard = _main_kb_with_faq
try:
    import main_screen as _ms
    _ms.get_main_keyboard = _main_kb_with_faq
except Exception:
    pass
