# admin.py - РАСШИРЕННАЯ АДМИН-ПАНЕЛЬ + НЕЙРОНКА
# ПОЛНАЯ ВЕРСИЯ С ПРАВИЛЬНЫМИ ИМПОРТАМИ

import asyncio
import sys
import os
import glob
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMINS, TOKEN
from database import Database, Player
from logger import GameLogger
from utils import update_message
from main_screen import show_main_screen

logger = GameLogger()
db = Database()


# ===== ГЛАВНАЯ СПРАВКА =====

async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать полную справку по админ-командам"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    text = """
👑 **АДМИНИСТРИРОВАНИЕ АВАЛОНА 4.0** 👑

═══════════════════════════════════════

🔧 **ТЕХНИЧЕСКИЕ РАБОТЫ:**
• `/tech on [сообщение]` — включить режим техработ
• `/tech off` — выключить режим техработ  
• `/tech status` — проверить статус техработ

📢 **РАССЫЛКИ:**
• `/broadcast <сообщение>` — массовая рассылка всем игрокам
  (используй `\\n` для переноса строк)

🔄 **УПРАВЛЕНИЕ БОТОМ:**
• `/restart` — перезапуск бота
• `/emergency_stop` — экстренная остановка бота
• `/admin_stats` — общая статистика бота

🌐 **ПРОКСИ И СЕТЬ:**
• `/refresh_proxies` — принудительно обновить список прокси
• `/proxy_status` — статус текущих прокси
• `/proxy_test` — проверить все прокси
• `/convert_proxy <tg://ссылка>` — конвертировать ссылку в MTProto

🔍 **ДИАГНОСТИКА ИГРОКОВ:**
• `/check_player @ник` — просмотр данных игрока
• `/check_player <ID>` — просмотр по ID
• `/check_errors` — проверка ошибок в базе данных
• `/fix_all` — автоматическое исправление ошибок

💾 **БЭКАПЫ:**
• `/list_backups` — список всех сохранённых бэкапов
• `/restore_backup <имя_файла>` — восстановление из бэкапа
• `/cleanup_backups [число]` — удаление старых бэкапов

👤 **УПРАВЛЕНИЕ ИГРОКАМИ:**
• `/fix_tg` — заполнить tg_username для всех игроков
• `/cleanup_phantom` — удалить фантомные записи (без расы)
• `/chatid` — узнать ID текущего чата
• `/give_money <@ник> <сумма>` — выдать монеты игроку
• `/take_money <@ник> <сумма>` — забрать монеты у игрока
• `/reset_player <@ник>` — сбросить прогресс игрока

🧠 **SMART AI (САМООБУЧЕНИЕ):**
• `/ai_analytics` — глобальная аналитика AI
• `/ai_analytics @ник` — аналитика по конкретному игроку
• `/reset_ai <@ник>` — сбросить память AI об игроке

🧠 **НЕЙРОННАЯ СЕТЬ (НОВОЕ):**
• `/ai_status` — глобальная статистика нейросетей
• `/ai_reset @ник` — сбросить обучение нейронки для игрока
• `/ai_graph @ник` — показать график обучения нейронки

📊 **СТАТИСТИКА:**
• `/online` — список онлайн-игроков
• `/server_status` — статус сервера и авто-функций
• `/logs` — последние логи (только в консоли)

═══════════════════════════════════════

💡 **АВТОМАТИЗАЦИЯ (работает сама):**
• ✅ Авто-сохранение данных — каждые 60 секунд
• ✅ Авто-бэкап — каждые 24 часа
• ✅ Авто-прокси — проверка каждые 5 минут
• ✅ Авто-ротация прокси — при сетевых ошибках
• ✅ Авто-загрузка прокси — с внешних источников

🛡️ **Безопасность:** 
   Только пользователи из списка ADMINS в .env имеют доступ
"""
    await update_message(update, context, text, parse_mode='Markdown')


# ===== УПРАВЛЕНИЕ ПРОКСИ =====

async def convert_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Конвертировать tg:// ссылку в MTProto и добавить в базу"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Формат:** `/convert_proxy <tg://ссылка>`\n\n"
            "Пример:\n"
            "`/convert_proxy tg://proxy?server=149.154.167.91&port=443&secret=ee8aab...`\n\n"
            "💡 Альтернатива: просто отправь ссылку — бот сам распознает",
            parse_mode='Markdown'
        )
        return
    
    tg_link = ' '.join(context.args)
    
    from mtproto_converter import MTProtoConverter
    from bypass import ProxyManager
    
    parsed = MTProtoConverter.parse_tg_link(tg_link)
    
    if not parsed:
        await update.message.reply_text("❌ Не удалось распознать ссылку!")
        return
    
    server, port, secret = parsed
    mtproto = MTProtoConverter.to_mtproto(server, port, secret)
    
    pm = ProxyManager()
    if pm.add_proxy(mtproto):
        await update.message.reply_text(
            f"✅ Прокси добавлен в базу!\n\n"
            f"📡 `{mtproto}`\n\n"
            f"🔄 Проверка прокси запущена автоматически..."
        )
        asyncio.create_task(pm.update_proxies_async(TOKEN))
    else:
        await update.message.reply_text("⚠️ Прокси уже есть в базе или не работает")


async def refresh_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принудительно обновить список прокси"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    msg = await update.message.reply_text("🔄 Обновление прокси...")
    
    proxy_manager = context.bot_data.get('proxy_manager')
    if not proxy_manager:
        await msg.edit_text("❌ Прокси-менеджер не инициализирован!")
        return
    
    from bypass import auto_fetch_proxies
    
    await auto_fetch_proxies(proxy_manager, TOKEN)
    await proxy_manager.update_proxies_async(TOKEN)
    
    status = "✅" if proxy_manager.current else "⚠️"
    await msg.edit_text(
        f"{status} **ПРОКСИ ОБНОВЛЕНЫ!**\n\n"
        f"📡 Всего прокси: {len(proxy_manager.proxies)}\n"
        f"✅ Работающих: {len(proxy_manager.working)}\n"
        f"⭐ Текущий: `{proxy_manager.current[:50] if proxy_manager.current else 'Нет'}...`\n"
        f"🕐 Последнее обновление: {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"💡 Для детального статуса используй `/proxy_status`",
        parse_mode='Markdown'
    )


async def proxy_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус прокси"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    proxy_manager = context.bot_data.get('proxy_manager')
    if not proxy_manager:
        await update.message.reply_text("❌ Прокси-менеджер не инициализирован!")
        return
    
    text = f"🌐 **СТАТУС ПРОКСИ** 🌐\n\n"
    text += f"📡 Всего прокси: {len(proxy_manager.proxies)}\n"
    text += f"✅ Работающих: {len(proxy_manager.working)}\n"
    text += f"⭐ Текущий прокси: "
    
    if proxy_manager.current:
        stats = proxy_manager.proxy_stats.get(proxy_manager.current, {})
        latency = stats.get('latency', 0)
        failures = stats.get('failures', 0)
        text += f"`{proxy_manager.current[:60]}...`\n"
        text += f"   ⏱️ Задержка: {latency:.2f}с\n"
        text += f"   ❌ Ошибок: {failures}\n"
    else:
        text += "Нет работающих прокси!\n"
    
    text += f"\n📋 **ТОП-5 ЛУЧШИХ ПРОКСИ:**\n"
    
    working_with_stats = [(p, proxy_manager.proxy_stats.get(p, {}).get('latency', 999)) 
                          for p in proxy_manager.working[:5]]
    working_with_stats.sort(key=lambda x: x[1])
    
    for i, (proxy, latency) in enumerate(working_with_stats[:5], 1):
        text += f"{i}. `{proxy[:40]}...` — {latency:.2f}с\n"
    
    text += f"\n🕐 Последнее обновление: {datetime.now().strftime('%H:%M:%S')}"
    
    await update.message.reply_text(text, parse_mode='Markdown')


# ===== СТАТИСТИКА =====

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расширенную статистику"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    players = db.get_all()
    
    total_players = 0
    players_with_char = 0
    total_money = 0
    total_kills = 0
    locations = {}
    total_power = 0
    total_level = 0
    total_wins = 0
    total_losses = 0
    
    for uid, p in players.items():
        if isinstance(p, dict):
            total_players += 1
            if p.get('race'):
                players_with_char += 1
                total_money += p.get('money', 0)
                total_kills += p.get('kills', 0)
                total_power += p.get('power', 0)
                total_level += p.get('level', 0)
                total_wins += p.get('wins', 0)
                total_losses += p.get('losses', 0)
                loc = p.get('location', 'unknown')
                locations[loc] = locations.get(loc, 0) + 1
    
    clans_count = 0
    clan_members = 0
    if '_clans' in players:
        clans = players['_clans']
        clans_count = len(clans)
        for clan_id, clan in clans.items():
            clan_members += len(clan.get('members', {}))
    
    avg_power = total_power // players_with_char if players_with_char > 0 else 0
    avg_level = total_level // players_with_char if players_with_char > 0 else 0
    
    proxy_manager = context.bot_data.get('proxy_manager')
    proxy_status_text = "✅ Активен" if proxy_manager and proxy_manager.current else "⚠️ Нет прокси"
    working_count = len(proxy_manager.working) if proxy_manager else 0
    
    text = f"📊 **СТАТИСТИКА БОТА AVALON 4.0** 📊\n\n"
    text += f"👥 **Игроки:**\n"
    text += f"• Всего записей: {total_players}\n"
    text += f"• С персонажами: {players_with_char}\n"
    text += f"• Без персонажа: {total_players - players_with_char}\n\n"
    
    text += f"💰 **Экономика:**\n"
    text += f"• Всего монет: {total_money:,}\n"
    text += f"• Всего убийств: {total_kills:,}\n"
    text += f"• Средняя сила: {avg_power}\n"
    text += f"• Средний уровень: {avg_level}\n\n"
    
    text += f"⚔️ **PvP Статистика:**\n"
    text += f"• Всего побед: {total_wins:,}\n"
    text += f"• Всего поражений: {total_losses:,}\n\n"
    
    text += f"🏰 **Кланы:**\n"
    text += f"• Всего кланов: {clans_count}\n"
    text += f"• Участников в кланах: {clan_members}\n\n"
    
    text += f"🌐 **Сеть:**\n"
    text += f"• Статус прокси: {proxy_status_text}\n"
    text += f"• Работающих прокси: {working_count}\n"
    if proxy_manager and proxy_manager.current:
        text += f"• Текущий прокси: `{proxy_manager.current[:40]}...`\n\n"
    
    text += f"📍 **Локации:**\n"
    loc_names = {
        'city': '🏰 Авалон', 
        'tavern': '🍺 Таверна', 
        'forest': '🌲 Лес', 
        'dungeon': '🏚️ Подземелье',
        'hospital': '🏥 Больница'
    }
    for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]:
        text += f"• {loc_names.get(loc, loc)}: {count} игроков\n"
    
    await update_message(update, context, text, parse_mode='Markdown')


async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список онлайн-игроков"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    from battle import active_battles
    from dungeon import active_dungeon_raids
    from hospital import hospital_patients
    
    text = "👥 **ОНЛАЙН ИГРОКИ** 👥\n\n"
    
    if active_battles:
        text += "⚔️ **В БОЮ:**\n"
        for uid in active_battles.keys():
            player = Player(uid)
            text += f"• {player.get('name', uid)} (ID: {uid})\n"
        text += "\n"
    
    if active_dungeon_raids:
        text += "🏚️ **В ПОДЗЕМЕЛЬЕ:**\n"
        for uid in active_dungeon_raids.keys():
            player = Player(uid)
            text += f"• {player.get('name', uid)} (ID: {uid})\n"
        text += "\n"
    
    if hospital_patients:
        text += "🏥 **В БОЛЬНИЦЕ:**\n"
        for uid in hospital_patients.keys():
            player = Player(uid)
            text += f"• {player.get('name', uid)} (ID: {uid})\n"
        text += "\n"
    
    if not active_battles and not active_dungeon_raids and not hospital_patients:
        text += "📭 Сейчас нет активных игроков\n"
    
    text += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус сервера и авто-функций"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    import time
    import psutil
    
    text = "🖥️ **СТАТУС СЕРВЕРА** 🖥️\n\n"
    
    text += f"💻 **Система:**\n"
    text += f"• CPU: {psutil.cpu_percent()}%\n"
    text += f"• RAM: {psutil.virtual_memory().percent}%\n"
    text += f"• Диск: {psutil.disk_usage('/').percent}%\n\n"
    
    import main
    if hasattr(main, 'start_time'):
        uptime = time.time() - main.start_time
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        text += f"⏱️ **Время работы:** {days}д {hours}ч {minutes}м\n\n"
    
    text += f"⚙️ **АВТО-ФУНКЦИИ:**\n"
    text += f"• ✅ Авто-сохранение — активна (каждые 60 сек)\n"
    text += f"• ✅ Авто-бэкап — активен (каждые 24 часа)\n"
    text += f"• ✅ Авто-прокси — активна (проверка каждые 5 мин)\n"
    text += f"• ✅ Авто-ротация — активна\n\n"
    
    proxy_manager = context.bot_data.get('proxy_manager')
    if proxy_manager:
        text += f"🌐 **Прокси:**\n"
        text += f"• Работающих: {len(proxy_manager.working)}\n"
        text += f"• Всего: {len(proxy_manager.proxies)}\n"
        if proxy_manager.current:
            text += f"• Текущий: `{proxy_manager.current[:40]}...`\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


# ===== УПРАВЛЕНИЕ ИГРОКАМИ =====

async def tech_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление техработами"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    args = context.args
    if not args:
        await update_message(update, context, 
            "🔧 **ТЕХРАБОТЫ**\n\n"
            "`/tech on [сообщение]` — включить режим техработ\n"
            "`/tech off` — выключить режим техработ\n"
            "`/tech status` — проверить статус",
            parse_mode='Markdown')
        return
    
    action = args[0].lower()
    
    if action == "on":
        message = " ".join(args[1:]) if len(args) > 1 else "🔧 Ведутся технические работы. Бот временно недоступен."
        context.bot_data['tech_works'] = {'enabled': True, 'message': message}
        await update_message(update, context, f"✅ Режим техработ ВКЛЮЧЁН\n📢 Сообщение: {message}")
        logger.tech_works(update.effective_user.first_name, True)
    
    elif action == "off":
        context.bot_data['tech_works'] = {'enabled': False, 'message': ""}
        await update_message(update, context, "✅ Режим техработ ВЫКЛЮЧЕН")
        logger.tech_works(update.effective_user.first_name, False)
    
    elif action == "status":
        tech = context.bot_data.get('tech_works', {'enabled': False})
        status = "ВКЛЮЧЕН" if tech.get('enabled') else "ВЫКЛЮЧЕН"
        await update_message(update, context, f"🔧 Режим техработ: {status}\n📢 Сообщение: {tech.get('message', '—')}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылка всем игрокам"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    if not context.args:
        await update_message(update, context, 
            "📢 **РАССЫЛКА**\n\n"
            "Формат: `/broadcast сообщение`\n"
            "Используй `\\n` для переноса строки\n\n"
            "Пример: `/broadcast Привет!\\nНовое обновление!`",
            parse_mode='Markdown')
        return
    
    message = ' '.join(context.args).replace('\\n', '\n')
    players = db.get_all()
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text("📤 Начинаю массовую рассылку...")
    
    for uid, p in players.items():
        if not p.get('race'):
            continue
        try:
            await context.bot.send_message(chat_id=int(uid), text=message)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(
        f"✅ **РАССЫЛКА ЗАВЕРШЕНА!**\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего игроков: {sent + failed}"
    )
    logger.broadcast(update.effective_user.first_name, sent)


async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск бота"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    await update_message(update, context, "🔄 **ПЕРЕЗАПУСК БОТА...**\n\nСохранение данных...")
    logger.admin_action(update.effective_user.first_name, "перезапуск бота")
    
    db.save()
    python = sys.executable
    os.execl(python, python, *sys.argv)


async def emergency_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экстренная остановка"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    await update_message(update, context, "🛑 **ЭКСТРЕННАЯ ОСТАНОВКА БОТА...**")
    logger.admin_action(update.effective_user.first_name, "экстренная остановка")
    
    db.save()
    context.bot_data['tech_works'] = {'enabled': True, 'message': "🔧 Бот временно остановлен администратором."}
    sys.exit(0)


async def fix_tg_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заполнить tg_username для всех игроков"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    msg = await update.message.reply_text("🔄 Начинаю заполнение tg_username...")
    
    data = db.get_all()
    updated = 0
    
    for uid, p in data.items():
        if uid.startswith('_') or not isinstance(p, dict):
            continue
        if p.get('race') and not p.get('tg_username'):
            p['tg_username'] = p.get('name', 'NoName')
            updated += 1
    
    db.save()
    await msg.edit_text(f"✅ Добавлено tg_username: {updated} игрокам")


async def cleanup_phantom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить фантомных игроков (без расы)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    msg = await update.message.reply_text("🔍 Чистка фантомных игроков...")
    
    data = db.get_all()
    deleted = 0
    
    for uid, p in list(data.items()):
        if uid.startswith('_') or not isinstance(p, dict):
            continue
        if not p.get('race'):
            del data[uid]
            deleted += 1
    
    db.save()
    await msg.edit_text(f"✅ Удалено фантомов: {deleted}")


async def check_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверить данные игрока"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    if not context.args:
        await update_message(update, context, "📝 **Формат:** `/check_player @ник` или `/check_player ID`", parse_mode='Markdown')
        return
    
    target = context.args[0].replace('@', '').lower()
    players = db.get_all()
    
    target_id = None
    target_data = None
    
    if target.isdigit() and target in players:
        target_id = target
        target_data = players[target]
    else:
        for uid, p in players.items():
            if isinstance(p, dict) and p.get('name', '').lower() == target:
                target_id = uid
                target_data = p
                break
    
    if not target_data:
        await update_message(update, context, f"👤 Игрок '{target}' не найден!")
        return
    
    text = f"🔍 **ДАННЫЕ ИГРОКА**\n\n"
    text += f"ID: `{target_id}`\n"
    text += f"Имя: {target_data.get('name', 'Неизвестно')}\n"
    text += f"Раса: {target_data.get('race', 'Не выбрана')}\n"
    text += f"Пол: {target_data.get('gender', 'Не выбран')}\n"
    text += f"Класс: {target_data.get('class', 'Не выбран')}\n\n"
    
    text += f"📊 **Характеристики:**\n"
    text += f"• Уровень: {target_data.get('level', 1)}\n"
    text += f"• Сила: {target_data.get('power', 50)}\n"
    text += f"• HP: {target_data.get('hp', 100)}/{target_data.get('max_hp', 100)}\n"
    text += f"• Мана: {target_data.get('mana', 50)}/{target_data.get('max_mana', 50)}\n"
    text += f"• Монет: {target_data.get('money', 0):,}\n\n"
    
    text += f"⚔️ **Статистика:**\n"
    text += f"• Убийств: {target_data.get('kills', 0)}\n"
    text += f"• Побед: {target_data.get('wins', 0)} | Поражений: {target_data.get('losses', 0)}\n"
    text += f"• Достижений: {len(target_data.get('achievements', {}))}\n"
    text += f"• Работ выполнено: {target_data.get('works_done', 0)}\n"
    text += f"• Крафтов: {target_data.get('crafts_done', 0)}\n\n"
    
    text += f"📍 Локация: {target_data.get('location', 'city')}\n"
    
    if target_data.get('death_time'):
        text += f"💀 Статус: МЁРТВ\n"
    else:
        text += f"✅ Статус: ЖИВ\n"
    
    await update_message(update, context, text, parse_mode='Markdown')


async def give_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдать монеты игроку"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("📝 **Формат:** `/give_money <@ник> <сумма>`", parse_mode='Markdown')
        return
    
    target = context.args[0].replace('@', '')
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Сумма должна быть числом!")
        return
    
    players = db.get_all()
    target_id = None
    target_data = None
    
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == target.lower():
            target_id = uid
            target_data = p
            break
    
    if not target_data:
        await update.message.reply_text(f"❌ Игрок {target} не найден!")
        return
    
    old_money = target_data.get('money', 0)
    target_data['money'] = old_money + amount
    db.save()
    
    await update.message.reply_text(
        f"✅ Выдано {amount}💰 игроку {target_data['name']}\n"
        f"💰 Баланс был: {old_money:,} → стал: {target_data['money']:,}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"🎁 Администратор выдал тебе {amount}💰!\n💰 Твой баланс: {target_data['money']:,}"
        )
    except:
        pass


async def take_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забрать монеты у игрока"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("📝 **Формат:** `/take_money <@ник> <сумма>`", parse_mode='Markdown')
        return
    
    target = context.args[0].replace('@', '')
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Сумма должна быть числом!")
        return
    
    players = db.get_all()
    target_id = None
    target_data = None
    
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == target.lower():
            target_id = uid
            target_data = p
            break
    
    if not target_data:
        await update.message.reply_text(f"❌ Игрок {target} не найден!")
        return
    
    old_money = target_data.get('money', 0)
    new_money = max(0, old_money - amount)
    target_data['money'] = new_money
    db.save()
    
    await update.message.reply_text(
        f"✅ Забрано {amount}💰 у игрока {target_data['name']}\n"
        f"💰 Баланс был: {old_money:,} → стал: {new_money:,}"
    )


async def reset_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить прогресс игрока"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 **Формат:** `/reset_player <@ник>`", parse_mode='Markdown')
        return
    
    target = context.args[0].replace('@', '')
    
    players = db.get_all()
    target_id = None
    target_data = None
    
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == target.lower():
            target_id = uid
            target_data = p
            break
    
    if not target_data:
        await update.message.reply_text(f"❌ Игрок {target} не найден!")
        return
    
    from resource_fixer import create_backup
    create_backup()
    
    target_data['level'] = 1
    target_data['exp'] = 0
    target_data['power'] = 50
    target_data['hp'] = 100
    target_data['max_hp'] = 100
    target_data['money'] = 500
    target_data['kills'] = 0
    target_data['wins'] = 0
    target_data['losses'] = 0
    target_data['inventory'] = {'items': [], 'equipped': {}}
    target_data['resources'] = {}
    target_data['achievements'] = {}
    target_data['death_time'] = None    
    db.save()
    
    await update.message.reply_text(
        f"✅ Прогресс игрока {target_data['name']} сброшен!\n"
        f"📦 Создан бэкап перед сбросом"
    )


# ===== SMART AI УПРАВЛЕНИЕ =====

async def ai_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать аналитику умного ИИ (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Эта команда только для администраторов.")
        return
    
    from smart_ai import smart_enemy_manager
    
    if context.args:
        player_name = context.args[0].replace('@', '').lower()
        players = db.get_all()
        
        target_id = None
        for uid, p in players.items():
            if isinstance(p, dict) and p.get('name', '').lower() == player_name:
                target_id = uid
                break
        
        if target_id:
            report = smart_enemy_manager.get_player_ai_report(target_id)
            await update.message.reply_text(report, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Игрок {player_name} не найден в базе данных!")
    else:
        report = smart_enemy_manager.get_all_admins_report()
        await update.message.reply_text(report, parse_mode='Markdown')


async def reset_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить память AI об игроке"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 **Формат:** `/reset_ai <@ник>`", parse_mode='Markdown')
        return
    
    player_name = context.args[0].replace('@', '').lower()
    players = db.get_all()
    
    target_id = None
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == player_name:
            target_id = uid
            break
    
    if not target_id:
        await update.message.reply_text(f"❌ Игрок {player_name} не найден!")
        return
    
    deleted = 0
    for file in glob.glob("enemy_memory.json"):
        try:
            os.remove(file)
            deleted += 1
        except:
            pass
    for file in glob.glob("global_enemy_memory.json"):
        try:
            os.remove(file)
            deleted += 1
        except:
            pass
    for file in glob.glob("tactics_*.json"):
        try:
            os.remove(file)
            deleted += 1
        except:
            pass
    
    from smart_ai import smart_enemy_manager
    smart_enemy_manager.active_ais.clear()
    
    await update.message.reply_text(
        f"✅ Память AI об игроке {player_name} сброшена!\n"
        f"🗑️ Удалено файлов: {deleted}\n"
        f"🧠 AI начнёт обучение заново при следующем бое"
    )


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Узнать ID чата"""
    chat = update.effective_chat
    thread_id = getattr(update.message, 'message_thread_id', None)
    
    text = f"📊 **ИНФОРМАЦИЯ О ЧАТЕ**\n\n"
    text += f"Название: {chat.title or 'Личные сообщения'}\n"
    text += f"Тип: {chat.type}\n"
    text += f"ID чата: `{chat.id}`\n"
    
    if thread_id:
        text += f"ID темы: `{thread_id}`\n"
    else:
        text += f"Темы: не используются\n"
    
    await update_message(update, context, text, parse_mode='Markdown')


async def ahelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать полную справку по админ-командам"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    await admin_help_command(update, context)


async def ai_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать память ИИ об игроке"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа!")
        return
    
    from smart_ai import smart_enemy_manager
    import glob
    
    args = context.args
    
    if args:
        player_name = args[0].replace('@', '').lower()
        players = db.get_all()
        
        target_id = None
        target_name = None
        for uid, p in players.items():
            if isinstance(p, dict) and p.get('name', '').lower() == player_name:
                target_id = uid
                target_name = p.get('name', player_name)
                break
        
        if not target_id:
            await update.message.reply_text(f"❌ Игрок {player_name} не найден!")
            return
        
        memory_text = f"🧠 ПАМЯТЬ ИИ ОБ ИГРОКЕ 🧠\n\n"
        memory_text += f"👤 Игрок: {target_name}\n"
        memory_text += f"🆔 ID: {target_id}\n\n"
        
        found = False
        
        for (enemy_id, player_id), ai in smart_enemy_manager.active_ais.items():
            if player_id == target_id:
                found = True
                memory_text += f"🔥 Активный бой: {ai.enemy_name}\n"
                memory_text += f"   ❤️ HP: {ai.current_hp}/{ai.base_hp}\n"
                memory_text += f"   🎮 Раундов: {ai.turn_count}\n"
        
        memory_files = glob.glob(f"enemy_memory_*_{target_id}.json") + \
                       glob.glob(f"enemy_memory_*_{target_id}.faiss.meta") + \
                       glob.glob(f"vec_*_{target_id}.faiss.meta")
        
        if memory_files:
            found = True
            memory_text += f"\n💾 Сохранённых файлов: {len(memory_files)}\n"
        
        if not found:
            memory_text += "📭 Нет данных об этом игроке.\n\n"
            memory_text += "💡 Сразитесь с монстром, чтобы создать память!"
        
        await update.message.reply_text(memory_text, parse_mode=None)
    else:
        memory_text = f"🧠 СТАТИСТИКА ПАМЯТИ ИИ 🧠\n\n"
        active_count = len(smart_enemy_manager.active_ais)
        memory_text += f"🔥 Активных боёв: {active_count}\n\n"
        
        memory_files = glob.glob("enemy_memory*.json") + \
                       glob.glob("*_memory*.json") + \
                       glob.glob("*.faiss.meta")
        
        if memory_files:
            memory_text += f"💾 Сохранённых файлов: {len(memory_files)}\n"
            for file in sorted(memory_files)[:5]:
                if os.path.exists(file):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%H:%M %d.%m')
                    memory_text += f"   • {os.path.basename(file)} ({file_time})\n"
        
        await update.message.reply_text(memory_text, parse_mode=None)


async def leave_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заставить бота выйти из указанного чата/группы"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    args = context.args
    
    if not args and update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title
        
        await update.message.reply_text(f"🚪 Выхожу из группы **{chat_title}**...")
        await context.bot.leave_chat(chat_id)
        return
    
    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ ID чата должен быть числом!")
            return
        
        await update.message.reply_text(f"🚪 Выхожу из чата `{chat_id}`...", parse_mode='Markdown')
        await context.bot.leave_chat(chat_id)
        return
    
    await update.message.reply_text(
        "📝 **Формат:**\n"
        "• `/leave` — выйти из текущей группы\n"
        "• `/leave 123456789` — выйти по ID чата\n\n"
        "💡 Узнать ID чата: `/chatid`",
        parse_mode='Markdown'
    )


# ============================================
# НЕЙРОНКА — КОМАНДЫ
# ============================================

async def ai_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус нейронной сети"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    try:
        from ai_phone import phone_ai
        report = phone_ai.get_report()
        await update.message.reply_text(report, parse_mode=None)
    except ImportError:
        await update.message.reply_text("❌ Нейронка не установлена! Файл ai_phone.py отсутствует.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def ai_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить обучение нейронки для игрока"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Формат:** `/ai_reset @ник`\n\n"
            "Сбросить обучение нейронки для конкретного игрока.\n"
            "Нейронка начнёт учиться заново.",
            parse_mode='Markdown'
        )
        return
    
    player_name = context.args[0].replace('@', '').lower()
    players = db.get_all()
    
    target_id = None
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == player_name:
            target_id = uid
            break
    
    if not target_id:
        await update.message.reply_text(f"❌ Игрок {player_name} не найден!")
        return
    
    deleted = 0
    for file in glob.glob(f"ai_models/*_{target_id}.pt"):
        try:
            os.remove(file)
            deleted += 1
        except:
            pass
    
    for file in glob.glob(f"ai_stats_*_{target_id}.json"):
        try:
            os.remove(file)
            deleted += 1
        except:
            pass
    
    try:
        from ai_phone import phone_ai
        to_remove = []
        for (eid, pid), enemy in phone_ai.enemies.items():
            if pid == target_id:
                to_remove.append((eid, pid))
        for eid, pid in to_remove:
            phone_ai.remove(eid, pid)
    except:
        pass
    
    await update.message.reply_text(
        f"✅ Нейронка для игрока {player_name} сброшена!\n"
        f"🗑️ Удалено файлов: {deleted}\n"
        f"🧠 Нейронка начнёт обучение с нуля в следующем бою."
    )


async def ai_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать график обучения нейронки"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Формат:** `/ai_graph @ник`\n\n"
            "Показать график обучения нейронки для игрока.",
            parse_mode='Markdown'
        )
        return
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        await update.message.reply_text("❌ Для графиков нужен matplotlib: `pip install matplotlib`")
        return
    
    player_name = context.args[0].replace('@', '').lower()
    players = db.get_all()
    
    target_id = None
    for uid, p in players.items():
        if isinstance(p, dict) and p.get('name', '').lower() == player_name:
            target_id = uid
            break
    
    if not target_id:
        await update.message.reply_text(f"❌ Игрок {player_name} не найден!")
        return
    
    stats_files = glob.glob(f"ai_stats_*_{target_id}.json")
    if not stats_files:
        await update.message.reply_text(f"📭 Нет данных для игрока {player_name}")
        return
    
    stats_file = sorted(stats_files)[-1]
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    rewards = stats.get('rewards', [])
    if not rewards:
        await update.message.reply_text(f"📭 Нет данных обучения для {player_name}")
        return
    
    plt.figure(figsize=(10, 6))
    plt.plot(rewards, label='Награда', color='blue', alpha=0.7)
    plt.xlabel('Шаг обучения')
    plt.ylabel('Награда')
    plt.title(f'Обучение нейронки: {player_name}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs('graphs', exist_ok=True)
    path = f'graphs/ai_learning_{target_id}.png'
    plt.savefig(path)
    plt.close()
    
    with open(path, 'rb') as f:
        await update.message.reply_photo(
            photo=f,
            caption=f"📈 **График обучения нейронки для {player_name}**\n\n"
                   f"📊 Всего шагов: {len(rewards)}\n"
                   f"📈 Средняя награда: {sum(rewards[-10:]) / min(10, len(rewards)):.2f}"
        )
