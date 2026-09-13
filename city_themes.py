# city_themes.py — с детальным дебагом
import os
import json
import random
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

THEMES_DIR = 'music/themes'
CACHE_FILE = 'theme_cache.json'

def _cache_load():
    try:
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _cache_get(key):
    return _cache_load().get(key)

def _cache_set(key, val):
    d = _cache_load()
    d[key] = val
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f)


LOG_FILE = 'audio_debug.log'

def dbg(msg):
    """Пишет в файл и stdout"""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"❌ Ошибка лога: {e}")

# Маппинг: id города -> файл темы
CITY_THEMES = {
    # Форматы записей:
    #   'город': 'file.mp3'                       — одна тема
    #   'город': ['a.mp3', 'b.mp3']               — равные шансы
    #   'город': [('a.mp3', 80), ('b.mp3', 20)]   — веса (относительные, не обязательно в сумме 100)
    'elf_city': [
        ('silvaris_theme1.mp3', 80),   # основная тема Сильвариса
        ('silvaris_theme2.mp3', 20),   # редкая
    ],
    'demon_city': [
        ('demon_theme1.mp3', 80),      # основная тема Инфернуса
        ('demon_theme2.mp3', 20),      # редкая
    ],
    'city_kosh': ['cat_theme.mp3'],
    'city_volk': ['volkograd_theme.mp3'],
    # Примеры на будущее (просто раскомментируй/допиши):
    # 'dorton': [('dorton_theme.mp3', 70), ('dorton_night.mp3', 30)],
    # 'city_volk': [('volkograd_theme.mp3', 60), ('volkograd_war.mp3', 40)],
}

def _pick_theme(themes):
    """Выбор темы с учётом весов.
    Форматы: 'file.mp3' | ['a.mp3','b.mp3'] | [('a.mp3',80),('b.mp3',20)]"""
    if isinstance(themes, str):
        return themes
    files, weights = [], []
    for item in themes:
        if isinstance(item, (tuple, list)):
            files.append(item[0])
            weights.append(float(item[1]))
        else:
            files.append(item)
            weights.append(1.0)
    return random.choices(files, weights=weights, k=1)[0]


def _track_title(fname):
    """Название трека: без .mp3 и без суффикса/номера темы"""
    base = fname.rsplit(".", 1)[0]
    base = re.sub(r"_?theme\d*$", "", base)
    return base or fname.rsplit(".", 1)[0]


async def play_theme_for_city(update: Update, context: ContextTypes.DEFAULT_TYPE, city_id: str, city_name=None):
    dbg(f"🎵 play_theme_for_city вызван, city_id={city_id}")
    
    themes = CITY_THEMES.get(city_id)
    if not themes:
        dbg(f"ℹ️ Для {city_id} тема не задана в CITY_THEMES")
        dbg(f"   Доступные: {list(CITY_THEMES.keys())}")
        return
    theme_file = _pick_theme(themes)
    if isinstance(themes, (list, tuple)) and len(themes) > 1:
        dbg(f"🎲 Выбрана тема с учётом весов: {theme_file}")
    
    theme_path = os.path.join(THEMES_DIR, theme_file)
    dbg(f"📂 Ищу файл: {theme_path}")
    
    if not os.path.exists(theme_path):
        dbg(f"❌ Файл НЕ СУЩЕСТВУЕТ: {theme_path}")
        return
    
    file_size = os.path.getsize(theme_path)
    dbg(f"📦 Файл найден, размер: {file_size} байт")
    
    if file_size < 100:
        dbg(f"⚠️ Файл слишком маленький (пустой?) — пропуск")
        return
    
    try:
        from whitelist import send_audio_safe, send_voice_safe
        dbg("✅ whitelist импортирован")
    except ImportError as e:
        dbg(f"❌ Ошибка импорта whitelist: {e}")
        return
    
    # Формат: voice (ogg, красиво) или audio (mp3, плеер). Переключатель в .env:
    # THEME_FORMAT=voice  (по умолчанию)  |  THEME_FORMAT=audio
    voice_mode = os.getenv("THEME_FORMAT", "voice") == "voice"
    ogg_path = theme_path[:-4] + ".ogg" if theme_path.endswith(".mp3") else None
    use_voice = voice_mode and ogg_path and os.path.exists(ogg_path)

    if use_voice:
        send_path, cache_key, is_voice = ogg_path, theme_file + ":voice", True
        dbg("🎤 Режим: голосовое сообщение (ogg opus)")
    else:
        send_path, cache_key, is_voice = theme_path, theme_file + ":audio", False
        dbg("🎵 Режим: аудиофайл (mp3-плеер)")

    cached = _cache_get(cache_key)
    if cached:
        dbg("⚡ Отправляю по кэшу file_id (мгновенно)")
        audio_src = cached
    else:
        dbg(f"📤 Отправляю файлом: {os.path.basename(send_path)}")
        audio_src = open(send_path, 'rb')
    try:
        if is_voice:
            result = await send_voice_safe(
                context, update.effective_user.id, audio_src)
        else:
            result = await send_audio_safe(
                context, update.effective_user.id, audio_src,
                title=_track_title(theme_file),
                performer=context.bot.first_name or "Авалон")
        media = getattr(result, 'voice', None) or getattr(result, 'audio', None)
        fid = getattr(media, 'file_id', None)
        if fid and not cached:
            _cache_set(cache_key, fid)
            dbg("💾 file_id сохранён в theme_cache.json")
        dbg("📤 Отправка успешна")
    except Exception as e:
        import traceback
        dbg(f"❌ Ошибка при отправке: {e}")
        dbg(traceback.format_exc())
    finally:
        if not isinstance(audio_src, str):
            try:
                audio_src.close()
            except Exception:
                pass

async def city_theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Темы играют автоматически при входе в город")

async def play_city_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        city_id = update.callback_query.data.replace('theme_', '')
        await play_theme_for_city(update, context, city_id)
