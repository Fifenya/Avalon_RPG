# resource_fixer.py - ФИКСЕР БАЗЫ ДАННЫХ И БЭКАПЫ (ТОЛЬКО ПО КОМАНДЕ)
import json
import os
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils import update_message
from config import DATA_FILE, ADMINS

db = Database()
BACKUP_DIR = "backups"

os.makedirs(BACKUP_DIR, exist_ok=True)


def create_backup() -> str:
    """Создаёт бэкап data.json"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/data_{timestamp}.json"
    
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, backup_file)
    
    return backup_file


def list_backups() -> list:
    """Возвращает список бэкапов"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.startswith("data_") and f.endswith(".json"):
                filepath = os.path.join(BACKUP_DIR, f)
                size = os.path.getsize(filepath) // 1024
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                backups.append({
                    "name": f,
                    "path": filepath,
                    "size": size,
                    "date": mtime.strftime("%Y-%m-%d %H:%M:%S")
                })
    return backups


def restore_backup(backup_name: str) -> bool:
    """Восстанавливает бэкап"""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        return False
    
    create_backup()
    shutil.copy2(backup_path, DATA_FILE)
    db._load()
    
    return True


def cleanup_backups(keep_count: int = 10) -> int:
    """Удаляет старые бэкапы"""
    backups = list_backups()
    if len(backups) <= keep_count:
        return 0
    
    to_delete = backups[keep_count:]
    deleted = 0
    for backup in to_delete:
        try:
            os.remove(backup["path"])
            deleted += 1
        except:
            pass
    
    return deleted


async def fix_all_errors_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Исправляет все ошибки в базе данных (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Только для администраторов.")
        return
    
    msg = await update.message.reply_text("🔧 Начинаю исправление ошибок...")
    
    data = db.get_all()
    fixed_count = 0
    fixes_log = []
    
    create_backup()
    
    for uid, p in list(data.items()):
        if uid.startswith('_'):
            continue
        if not isinstance(p, dict):
            continue
        
        player_name = p.get('name', uid)
        fixed = False
        
        # Фикс 1: отсутствие инвентаря
        if 'inventory' not in p:
            p['inventory'] = {'items': [], 'equipped': {}}
            fixes_log.append(f"📦 {player_name}: добавлен инвентарь")
            fixed = True
        
        # Фикс 2: недостающие поля в инвентаре
        if 'inventory' in p:
            if 'items' not in p['inventory']:
                p['inventory']['items'] = []
                fixes_log.append(f"📦 {player_name}: добавлен items в инвентарь")
                fixed = True
            if 'equipped' not in p['inventory']:
                p['inventory']['equipped'] = {}
                fixes_log.append(f"📦 {player_name}: добавлен equipped в инвентарь")
                fixed = True
        
        # Фикс 3: отсутствие ресурсов
        if 'resources' not in p:
            p['resources'] = {}
            fixes_log.append(f"📦 {player_name}: добавлены ресурсы")
            fixed = True
        
        # Фикс 4: отсутствие достижений
        if 'achievements' not in p:
            p['achievements'] = {}
            fixes_log.append(f"🏆 {player_name}: добавлены достижения")
            fixed = True
        
        # Фикс 5: отрицательные HP
        if p.get('hp', 0) < 0:
            p['hp'] = p.get('max_hp', 100)
            fixes_log.append(f"❤️ {player_name}: исправлены отрицательные HP")
            fixed = True
        
        # Фикс 6: HP больше max_hp
        if p.get('hp', 0) > p.get('max_hp', 100):
            p['hp'] = p.get('max_hp', 100)
            fixes_log.append(f"❤️ {player_name}: HP превышал максимум")
            fixed = True
        
        # Фикс 7: отрицательные деньги
        if p.get('money', 0) < 0:
            p['money'] = 0
            fixes_log.append(f"💰 {player_name}: исправлены отрицательные деньги")
            fixed = True
        
        # Фикс 8: отсутствие mana_regen
        if 'mana_regen' not in p:
            p['mana_regen'] = 1
            fixes_log.append(f"💙 {player_name}: добавлена регенерация маны")
            fixed = True
        
        # Фикс 9: отсутствие dungeon_floor
        if 'dungeon_floor' not in p:
            p['dungeon_floor'] = 1
            fixes_log.append(f"🏚️ {player_name}: добавлен этаж подземелья")
            fixed = True
        
        # Фикс 10: отсутствие dungeon_progress
        if 'dungeon_progress' not in p:
            p['dungeon_progress'] = 0
            fixes_log.append(f"🏚️ {player_name}: добавлен прогресс подземелья")
            fixed = True
        
        # Фикс 11: кривые статы
        if p.get('crit_chance', 0) > 0.75:
            old = p['crit_chance']
            p['crit_chance'] = 0.75
            fixes_log.append(f"💥 {player_name}: крит {old:.0%} → 75%")
            fixed = True
        if p.get('dodge_chance', 0) > 0.5:
            old = p['dodge_chance']
            p['dodge_chance'] = 0.5
            fixes_log.append(f"💨 {player_name}: уворот {old:.0%} → 50%")
            fixed = True
        if p.get('block_chance', 0) > 0.5:
            old = p['block_chance']
            p['block_chance'] = 0.5
            fixes_log.append(f"🛡️ {player_name}: блок {old:.0%} → 50%")
            fixed = True
        
        # Фикс 12: отсутствие works_done
        if 'works_done' not in p:
            p['works_done'] = 0
            fixes_log.append(f"💼 {player_name}: добавлены работы")
            fixed = True
        
        # Фикс 13: отсутствие crafts_done
        if 'crafts_done' not in p:
            p['crafts_done'] = 0
            fixes_log.append(f"🔨 {player_name}: добавлены крафты")
            fixed = True
        
        # Фикс 14: отсутствие имени
        if not p.get('name') and not uid.startswith('_'):
            p['name'] = f"Герой_{uid[-6:]}"
            fixes_log.append(f"📛 {uid}: добавлено имя")
            fixed = True
        
        # Фикс 15: отсутствие max_mana
        if 'max_mana' not in p:
            p['max_mana'] = 50
            fixes_log.append(f"💙 {player_name}: добавлена max_mana")
            fixed = True
        
        # Фикс 16: отсутствие last_mana_update
        if 'last_mana_update' not in p:
            p['last_mana_update'] = datetime.now().timestamp()
            fixes_log.append(f"💙 {player_name}: добавлена last_mana_update")
            fixed = True
        
        # Фикс 17: отсутствие tg_username
        if 'tg_username' not in p and p.get('name'):
            p['tg_username'] = p.get('name')
            fixes_log.append(f"📱 {player_name}: добавлен tg_username")
            fixed = True
        
        if fixed:
            fixed_count += 1
    
    db.save()
    
    report = f"✅ **Исправление завершено!**\n\n"
    report += f"🔧 Исправлено игроков: {fixed_count}\n"
    report += f"📁 Бэкап создан перед исправлением\n\n"
    
    if fixes_log:
        report += f"**Подробности:**\n"
        for log in fixes_log[:15]:
            report += f"└ {log}\n"
        if len(fixes_log) > 15:
            report += f"└ ...и ещё {len(fixes_log) - 15} исправлений\n"
    
    report += f"\n💡 Для просмотра бэкапов: /list_backups"
    
    await msg.edit_text(report, parse_mode='Markdown')


async def check_errors_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет базу данных на ошибки (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Только для администраторов.")
        return
    
    msg = await update.message.reply_text("🔍 Проверка базы данных...")
    
    data = db.get_all()
    errors = []
    warnings = []
    players_count = 0
    
    for uid, p in data.items():
        if uid.startswith('_'):
            continue
        if not isinstance(p, dict):
            errors.append(f"❌ {uid}: данные не словарь")
            continue
        
        if p.get('race'):
            players_count += 1
        
        if 'hp' in p and p['hp'] < 0:
            errors.append(f"⚠️ {p.get('name', uid)}: отрицательное HP ({p['hp']})")
        
        if 'money' in p and p['money'] < 0:
            errors.append(f"⚠️ {p.get('name', uid)}: отрицательные деньги ({p['money']})")
        
        if 'hp' in p and 'max_hp' in p and p['hp'] > p['max_hp']:
            warnings.append(f"⚠️ {p.get('name', uid)}: HP ({p['hp']}) > max_hp ({p['max_hp']})")
        
        if 'crit_chance' in p and p['crit_chance'] > 0.75:
            warnings.append(f"⚠️ {p.get('name', uid)}: крит {p['crit_chance']:.0%} > 75%")
        
        if 'dodge_chance' in p and p['dodge_chance'] > 0.5:
            warnings.append(f"⚠️ {p.get('name', uid)}: уворот {p['dodge_chance']:.0%} > 50%")
        
        if 'inventory' in p:
            inv = p['inventory']
            if 'items' not in inv:
                errors.append(f"⚠️ {p.get('name', uid)}: инвентарь без items")
            if 'equipped' not in inv:
                errors.append(f"⚠️ {p.get('name', uid)}: инвентарь без equipped")
    
    if errors or warnings:
        result = f"📊 **РЕЗУЛЬТАТ ПРОВЕРКИ**\n\n"
        result += f"👥 Игроков с персонажами: {players_count}\n"
        result += f"❌ Ошибок: {len(errors)}\n"
        result += f"⚠️ Предупреждений: {len(warnings)}\n\n"
        
        if errors:
            result += f"**Ошибки:**\n"
            for e in errors[:10]:
                result += f"└ {e}\n"
            if len(errors) > 10:
                result += f"└ ...и ещё {len(errors) - 10}\n"
            result += f"\n"
        
        if warnings:
            result += f"**Предупреждения:**\n"
            for w in warnings[:10]:
                result += f"└ {w}\n"
            if len(warnings) > 10:
                result += f"└ ...и ещё {len(warnings) - 10}\n"
        
        result += f"\n💡 Используй /fix_all для автоматического исправления"
        
        await msg.edit_text(result, parse_mode='Markdown')
    else:
        await msg.edit_text(
            f"✅ **ОШИБОК НЕ НАЙДЕНО!**\n\n"
            f"👥 Игроков с персонажами: {players_count}\n"
            f"📁 База данных в порядке"
        )


async def list_backups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список бэкапов (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Только для администраторов.")
        return
    
    backups = list_backups()
    
    if not backups:
        await update.message.reply_text("📭 Нет сохранённых бэкапов")
        return
    
    keyboard = []
    for i, backup in enumerate(backups[:15]):
        keyboard.append([InlineKeyboardButton(
            f"{backup['date']} ({backup['size']}KB)",
            callback_data=f"restore_backup_{backup['name']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="fix_cancel")])
    
    await update.message.reply_text(
        f"📁 **СПИСОК БЭКАПОВ**\n\n"
        f"Всего: {len(backups)}\n\n"
        f"Выбери бэкап для восстановления:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def restore_backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Восстанавливает бэкап по команде (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Только для администраторов.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Формат:** /restore_backup <имя_файла>\n\n"
            "Пример: `/restore_backup data_20241201_120000.json`\n\n"
            "💡 Список бэкапов: /list_backups"
        )
        return
    
    backup_name = context.args[0]
    
    create_backup()
    
    if restore_backup(backup_name):
        await update.message.reply_text(
            f"✅ **Бэкап восстановлен!**\n\n"
            f"📁 Файл: {backup_name}\n"
            f"🔄 Данные перезагружены"
        )
    else:
        await update.message.reply_text(f"❌ Бэкап {backup_name} не найден!")


async def cleanup_backups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очищает старые бэкапы (только для админов)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update_message(update, context, "⛔ Нет доступа! Только для администраторов.")
        return
    
    keep = 10
    if context.args and context.args[0].isdigit():
        keep = int(context.args[0])
    
    deleted = cleanup_backups(keep)
    
    await update.message.reply_text(
        f"🗑️ **ОЧИСТКА БЭКАПОВ**\n\n"
        f"📁 Оставлено: {keep} последних\n"
        f"❌ Удалено: {deleted}\n"
        f"💡 Для просмотра оставшихся: /list_backups"
    )


async def fix_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок восстановления бэкапа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in ADMINS:
        await query.edit_message_text("⛔ Нет доступа! Только для администраторов.")
        return
    
    data = query.data
    
    if data == "fix_cancel":
        await query.edit_message_text("❌ Восстановление отменено")
        return
    
    if data.startswith("restore_backup_"):
        backup_name = data.replace("restore_backup_", "")
        
        create_backup()
        
        if restore_backup(backup_name):
            await query.edit_message_text(
                f"✅ **Бэкап восстановлен!**\n\n"
                f"📁 Файл: {backup_name}\n"
                f"🔄 Данные перезагружены"
            )
        else:
            await query.edit_message_text(f"❌ Ошибка восстановления {backup_name}")