# main.py - ИСПРАВЛЕННАЯ ВЕРСИЯ С GRACEFUL SHUTDOWN
import deps_manager
import kb_compat
import proxy_manager
kb_compat.install()
import cities_data
import faq  # рано: патчит меню кнопкой FAQ  # города рас
deps_manager.ensure_dependencies()

import asyncio
import time
import threading
import os
import sys
import signal
import warnings
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from config import TOKEN, REGEN_INTERVAL, ADMINS
from database import Database, Player
from logger import GameLogger
from console import console_thread
from admin import (
    admin_help_command, ahelp_command, admin_stats, tech_works, broadcast,
    restart_bot, emergency_stop, fix_tg_usernames, cleanup_phantom,
    check_player, chatid, convert_proxy, ai_analytics, reset_ai,
    refresh_proxies, online_command, server_status, ai_status, ai_reset, ai_graph, ai_memory, leave_chat
)
from state_manager import state_manager
from resource_fixer import fix_callback_handler, list_backups_command, restore_backup_command, cleanup_backups_command, check_errors_command, fix_all_errors_command
from character_fixer import character_fixer
from miniapp import prestige_miniapp, handle_webapp_data
from casino import *


# Игнорируем предупреждения
warnings.filterwarnings("ignore")

logger = GameLogger()
db = Database()

WAITING_NICKNAME, WAITING_RACE, WAITING_GENDER, WAITING_CLASS = range(4)

# ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
application = None
_last_regen_time = 0
start_time = time.time()


def shutdown_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    print("\n🛑 Получен сигнал остановки. Сохраняем данные...")
    try:
        db.save()
        state_manager.save()
        print("✅ Данные сохранены")
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении: {e}")
    sys.exit(0)


# ===== РЕГЕНЕРАЦИЯ =====
async def regen(context):
    """Регенерация HP и маны всех игроков"""
    global _last_regen_time
    current_time = time.time()
    
    if current_time - _last_regen_time < REGEN_INTERVAL:
        return
    
    _last_regen_time = current_time
    data = db.get_all()
    
    for uid, p in data.items():
        if not isinstance(p, dict) or not p.get('race'):
            continue
        if p.get('death_time'):
            continue
        if p.get('hp', 0) < p.get('max_hp', 100):
            regen_amount = max(1, int(p.get('max_hp', 100) * 0.05))
            p['hp'] = min(p.get('max_hp', 100), p.get('hp', 0) + regen_amount)
        
        player = Player(uid)
        player.regenerate_mana()
    
    db.save()


# ===== СОЗДАНИЕ ПЕРСОНАЖА =====
async def start_command(update: Update, context):
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    logger.command(uid, update.effective_user.first_name, "start", "")
    
    from main_screen import show_main_screen
    from keyboards import get_no_character_keyboard
    
    if not player.get('race'):
        await update.message.reply_text(
            "🌟 **Добро пожаловать в Авалон!** 🌟\n\n"
            "Для начала, придумай себе **имя** (никнейм):\n"
            "_(от 3 до 20 символов, можно использовать буквы, цифры и символы)_\n\n"
            "❌ Чтобы отменить создание, напиши `/cancel`",
            reply_markup=get_no_character_keyboard(),
            parse_mode='Markdown'
        )
        return WAITING_NICKNAME
    else:
        await show_main_screen(update, context)
        return ConversationHandler.END


async def cancel_creation(update: Update, context):
    await update.message.reply_text(
        "❌ Создание персонажа отменено.\n"
        "Если захочешь начать заново, напиши /start"
    )
    return ConversationHandler.END


async def get_nickname(update: Update, context):
    from main_screen import show_main_screen
    from keyboards import get_races_inline
    
    nickname = update.message.text.strip()
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if len(nickname) < 3:
        await update.message.reply_text("❌ **Слишком короткий никнейм!**\nМинимум 3 символа. Попробуй ещё раз:", parse_mode='Markdown')
        return WAITING_NICKNAME
    
    if len(nickname) > 20:
        await update.message.reply_text("❌ **Слишком длинный никнейм!**\nМаксимум 20 символов. Попробуй ещё раз:", parse_mode='Markdown')
        return WAITING_NICKNAME
    
    forbidden = ['@', '#', '$', '%', '^', '&', '*', '(', ')', '[', ']', '{', '}', '\\', '/', '|']
    if any(c in nickname for c in forbidden):
        await update.message.reply_text(f"❌ **Недопустимые символы!**\nНельзя использовать: {' '.join(forbidden)}\n\nПопробуй ещё раз:", parse_mode='Markdown')
        return WAITING_NICKNAME
    
    data = db.get_all()
    for uid_check, p in data.items():
        if isinstance(p, dict) and p.get('name') == nickname:
            await update.message.reply_text(f"❌ **Никнейм '{nickname}' уже занят!**\nПридумай другой:")
            return WAITING_NICKNAME
    
    player['name'] = nickname
    player['tg_username'] = update.effective_user.username    
    player.save()
    context.user_data['nickname'] = nickname
    
    await update.message.reply_text(f"✨ Отлично! Тебя будут звать **{nickname}** ✨\n\nТеперь выбери свою расу:", parse_mode='Markdown', reply_markup=get_races_inline())
    return WAITING_RACE


async def handle_character_creation(update: Update, context):
    """Обработчик выбора расы, пола и класса"""
    from keyboards import get_beast_folk_inline, get_genders_inline, get_class_keyboard, get_races_inline
    from classes import CLASS_DATA, apply_class_stats
    from main_screen import show_main_screen
    
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = str(query.from_user.id)
    player = Player(uid)
    
    print(f"🔍 [DEBUG] handle_character_creation: data={data}")  # Для отладки
    
    # ============================================================
    # 1. ВЫБОР РАСЫ
    # ============================================================
    if data.startswith("race_"):
        race = data.replace("race_", "")
        print(f"🔍 [DEBUG] Выбрана раса: {race}")
        
        # Если выбраны ЗВЕРОЛЮДЫ — показываем список
        if race == "🐾 ЗВЕРОЛЮДЫ":
            await query.edit_message_text(
                "🐾 **Выбери тип зверолюда:**\n\n"
                "🐺 Волколюд — сила стаи\n"
                "🐱 Кошколюд — грация и ловкость\n"
                "🐻 Медведолюд — мощь и выносливость\n"
                "🦊 Лисолюд — хитрость и удача\n"
                "🐉 Драконолюд — древняя сила\n"
                "🐦 Птицелюд — скорость и лёгкость\n"
                "🐍 Змеелюд — яд и скрытность\n"
                "🐗 Кабанолюд — напор и броня\n"
                "🦌 Оленелюд — благородство и быстрота",
                reply_markup=get_beast_folk_inline()
            )
            return WAITING_RACE  # Остаёмся в том же состоянии
        
        # Если НЕ зверолюд — сохраняем расу
        player['race'] = race
        player.save()
        context.user_data['race'] = race
        
        await query.edit_message_text(
            f"✨ Ты выбрал расу **{race}**!\n\n"
            f"Теперь выбери свой пол:",
            reply_markup=get_genders_inline()
        )
        return WAITING_GENDER
    
    # ============================================================
    # 2. ВЫБОР КОНКРЕТНОГО ЗВЕРОЛЮДА
    # ============================================================
    elif data.startswith("beast_"):
        beast = data.replace("beast_", "")
        print(f"🔍 [DEBUG] Выбран зверолюд: {beast}")
        
        player['race'] = beast
        player.save()
        context.user_data['race'] = beast
        
        await query.edit_message_text(
            f"✨ Ты выбрал расу **{beast}**!\n\n"
            f"Теперь выбери свой пол:",
            reply_markup=get_genders_inline()
        )
        return WAITING_GENDER
    
    # ============================================================
    # 3. ВЫБОР ПОЛА
    # ============================================================
    elif data.startswith("gender_"):
        gender = data.replace("gender_", "")
        print(f"🔍 [DEBUG] Выбран пол: {gender}")
        
        player['gender'] = gender
        player.save()
        context.user_data['gender'] = gender
        
        await query.edit_message_text(
            f"✨ Твой пол: **{gender}**!\n\n"
            f"🎭 **Выбери свой класс:**\n\n"
            f"🗡️ Воин — сильный и выносливый\n"
            f"🔮 Маг — повелитель стихий\n"
            f"🏹 Лучник — точный и быстрый\n"
            f"🛡️ Танк — живая стена\n"
            f"🗡️ Разбойник — скрытный убийца\n"
            f"🙏 Жрец — целитель и поддержка",
            reply_markup=get_class_keyboard()
        )
        return WAITING_CLASS
    
    # ============================================================
    # 4. ВЫБОР КЛАССА
    # ============================================================
    elif data.startswith("class_"):
        class_value = data.replace("class_", "")
        print(f"🔍 [DEBUG] Выбран класс: {class_value}")
        
        # Находим класс
        selected_class = None
        for cls, cls_data in CLASS_DATA.items():
            if cls.value == class_value:
                selected_class = cls
                break
        
        if selected_class:
            apply_class_stats(player, selected_class)
            player.save()
            
            class_name = CLASS_DATA[selected_class]['name']
            class_desc = CLASS_DATA[selected_class]['description']
            stats = CLASS_DATA[selected_class]['base_stats']
            
            await query.edit_message_text(
                f"🎉 **Ты выбрал класс {class_name}!** 🎉\n\n"
                f"_{class_desc}_\n\n"
                f"**Базовые характеристики:**\n"
                f"⚔️ Сила: {stats['power']}\n"
                f"❤️ HP: {stats['hp']}\n"
                f"💙 Мана: {stats['mana']}\n"
                f"🛡️ Броня: {stats.get('armor', 0)}\n"
                f"💥 Крит: {int(stats.get('crit_chance', 0) * 100)}%\n\n"
                f"🌟 Добро пожаловать в Авалон, {player['name']}!",
                parse_mode='Markdown'
            )
            await show_main_screen(update, context)
        else:
            await query.edit_message_text("❌ Ошибка выбора класса! Попробуй ещё раз.")
        
        return ConversationHandler.END
    
    # ============================================================
    # 5. НАЗАД К РАСАМ
    # ============================================================
    elif data == "back_to_races":
        await query.edit_message_text(
            "🎭 **Выбери свою расу:**",
            reply_markup=get_races_inline()
        )
        return WAITING_RACE
    
    return ConversationHandler.END


async def select_class(update: Update, context):
    from classes import CLASS_DATA, apply_class_stats
    from main_screen import show_main_screen
    
    query = update.callback_query
    await query.answer()
    
    class_value = query.data.replace("class_", "")
    uid = str(query.from_user.id)
    player = Player(uid)
    
    print(f"🔍 [DEBUG] select_class: class_value={class_value}")
    print(f"🔍 [DEBUG] До выбора класса: race={player.get('race')}, class={player.get('class')}")
    
    # Находим класс
    selected_class = None
    for cls, cls_data in CLASS_DATA.items():
        if cls.value == class_value:
            selected_class = cls
            break
    
    if selected_class:
        # Применяем статы класса
        apply_class_stats(player, selected_class)
        
        # Убеждаемся, что раса сохранена
        if not player.get('race'):
            print("❌ [DEBUG] ОШИБКА: раса не сохранена!")
            await query.edit_message_text(
                "❌ Ошибка: раса не выбрана! Начни регистрацию заново через /start"
            )
            return ConversationHandler.END
        
        # Сохраняем
        player.save()
        
        print(f"🔍 [DEBUG] После выбора класса: race={player.get('race')}, class={player.get('class')}")
        
        class_name = CLASS_DATA[selected_class]['name']
        class_desc = CLASS_DATA[selected_class]['description']
        stats = CLASS_DATA[selected_class]['base_stats']
        
        await query.edit_message_text(
            f"🎉 **Ты выбрал класс {class_name}!** 🎉\n\n"
            f"_{class_desc}_\n\n"
            f"**Базовые характеристики:**\n"
            f"⚔️ Сила: {stats['power']}\n"
            f"❤️ HP: {stats['hp']}\n"
            f"💙 Мана: {stats['mana']}\n"
            f"🛡️ Броня: {stats.get('armor', 0)}\n"
            f"💥 Крит: {int(stats.get('crit_chance', 0) * 100)}%\n\n"
            f"🌟 Добро пожаловать в Авалон, {player['name']}!",
            parse_mode='Markdown'
        )
        
        # Показываем главный экран
        await show_main_screen(update, context)
    else:
        await query.edit_message_text("❌ Ошибка выбора класса! Попробуй ещё раз.")
    
    return ConversationHandler.END


# ===== ТЕКСТОВЫЙ ХЕНДЛЕР =====
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from main_screen import show_main_screen
    from clan import clan_command, clan_text_handler, clan_create_name, clan_search_process, clan_bank_process
    from top import top_menu
    from inventory import show_inventory
    from resources import show_resources
    from equipment import show_equipment
    from profile import show_profile
    from shop import shop_command
    from crafting import crafting_menu
    from work import work_handler
    from gathering import gathering_menu
    from battle import start_battle
    from casino import casino_menu
    from dungeon import enter_dungeon
    from tavern import sit_at_counter, leave_tavern
    from race_shop import race_shop_menu
    from keyboards import get_races_inline
    
    text = update.message.text
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    # ===== ПРОВЕРКА НА НАЛИЧИЕ РАСЫ =====
    if player.get('name') and not player.get('race'):
        await update.message.reply_text(
            "🧙 **Выбор расы**\n\n"
            "Кажется, ты ещё не выбрал свою расу!\n"
            "Сделай это сейчас:",
            reply_markup=get_races_inline()
        )
        return
    
    if not player.get('race') and text != "📜 О боте":
        await update.message.reply_text("❌ Сначала создай персонажа через /start")
        return
    
    logger.button(player.get('name', update.effective_user.first_name), text, "главное меню")

# ===== РЕЖИМЫ ВВОДА КЛАНА =====
    if await clan_create_name(update, context):
        return
    if await clan_search_process(update, context):
        return
    if await clan_bank_process(update, context):
        return

    # ===== ТЕКСТОВЫЕ КНОПКИ КЛАНА =====
    if text in ("🏰 Создать клан", "📋 Список кланов", "🏆 Топ кланов", "🔍 Поиск клана",
                "🏰 Мой клан", "🏦 Банк клана", "📤 Покинуть клан", "📥 Положить",
                "📤 Взять", "📊 Статистика банка", "⚙️ Управление кланом", "🔙 Назад к клану"):
        await clan_text_handler(update, context)
        return

    # ===== РЕЖИМ ПЕРЕМЕЩЕНИЯ =====
    if context.user_data.get('travel_mode'):
        from travel import travel_by_button
        if await travel_by_button(update, context, text):
            return
  
    # Основные команды
    if text == "👾 Охота":
        await start_battle(update, context)
    elif text == "🌿 Сбор ресурсов":
        await gathering_menu(update, context)
    elif text == "💼 Работа":
        await work_handler(update, context)
    elif text == "🏪 Магазин":
        await shop_command(update, context)
    elif text == "🔨 Крафт":
        await crafting_menu(update, context)
    elif text == "📦 Инвентарь":
        await show_inventory(update, context)
    elif text == "📦 Ресурсы":
        await show_resources(update, context)
    elif text == "⚔️ Экипировка":
        await show_equipment(update, context)
    elif text == "📜 Профиль":
        await show_profile(update, context)
    elif text == "🏰 Кланы":
        await clan_command(update, context)
    elif text == "🏆 Топ":
        await top_menu(update, context)
    elif text == "🗺️ Сменить локацию":
        from travel import show_locations
        await show_locations(update, context)
    elif text == "🍺 Таверна":
        if player.get('location') != 'city':
            await update.message.reply_text("❌ Ты можешь зайти в таверну только из Авалона!")
            return
        player['location'] = 'tavern'
        player.save()
        await show_main_screen(update, context)
    elif text == "🍺 Сесть за стойку":
        await sit_at_counter(update, context)
    elif text == "🚪 Выйти из таверны":
        await leave_tavern(update, context)
    elif text == "🏚️ Рейд":
        await enter_dungeon(update, context)
    elif text == "🎰 Казино":
        await casino_menu(update, context)
    elif text == "🏪 Городской магазин":
        class FakeQuery:
            def __init__(self, from_user, message):
                self.from_user = from_user
                self.message = message
            async def answer(self):
                pass
        fake_query = FakeQuery(update.effective_user, update.message)
        update.callback_query = fake_query
        await race_shop_menu(update, context)
        update.callback_query = None
    elif text == "🔙 На главную":
        await show_main_screen(update, context)
    elif text == "📜 О боте":
        from faq import faq_command
        await faq_command(update, context)
    elif text == "📚 Справочник":
        from faq import faq_command
        await faq_command(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда! Используй кнопки меню.")


# ===== ОБРАБОТЧИК ОШИБОК =====

async def enemy_personas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает типы врагов и их поведение"""
    from enemy_personas import ENEMY_PERSONAS
    
    text = "🎭 **ТИПЫ ВРАГОВ** 🎭\n\n"
    for key, persona in ENEMY_PERSONAS.items():
        if key == "default":
            continue
        text += f"**{persona['name']}**\n"
        text += f"_{persona['system'][:100]}..._\n\n"
    
    text += "\n💡 Персона назначается случайно при создании врага"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    err_text = str(error).lower()
    import traceback
    traceback.print_exc()  # полный стек в терминал для отладки
    error_str = str(error)
    logger.error("Ошибка", type(error).__name__, error_str)
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ Произошла техническая ошибка. Пожалуйста, попробуй позже.")
        except:
            pass


async def phantom_cleanup_loop():
    """Фоновая очистка фантомов каждые 5 минут"""
    while True:
        await asyncio.sleep(300)
        try:
            data = db.get_all()
            deleted = 0
            for uid, p in list(data.items()):
                if uid.startswith('_'):
                    continue
                if isinstance(p, dict) and not p.get('race'):
                    del data[uid]
                    deleted += 1
            if deleted > 0:
                db.save()
                logger.system("Очистка", f"Удалено фантомов: {deleted}")
        except Exception as e:
            print(f"Ошибка очистки: {e}")


# ===== ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА =====
async def main_async():
    """Асинхронная функция запуска бота"""
    global application
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    # ===== ОЧИСТКА ФАНТОМОВ ПРИ ЗАПУСКЕ =====
    deleted = db.cleanup_phantoms()
    if deleted:
        print(f"🗑️ При запуске удалено фантомов: {deleted}")
    
    from keyboards import get_races_inline, get_beast_folk_inline, get_genders_inline, get_class_keyboard
    from keyboards import get_locations_keyboard, get_main_keyboard
    from main_screen import change_location, show_main_screen
    from clan import clan_back_handler, clan_create_confirm, clan_upgrade_handler, clan_info_handler, clan_join_handler, clan_search_back
    from top import top_money, top_power, top_level, top_hunter
    from shop import shop_callback_handler
    from casino import casino_callback_handler
    from dungeon import dungeon_callback_handler
    from tavern import tavern_menu_back, order_ale, tavern_exit
    from gathering import gathering_callback_handler
    from battle import battle_callback_handler, battle_save_handler
    from equipment import equip_wear_menu, equip_remove_menu, upgrade_item_rank_command
    from resource_fixer import fix_callback_handler, list_backups_command, restore_backup_command, cleanup_backups_command, check_errors_command, fix_all_errors_command
    
    print("\n" + "=" * 60)
    print("🚀 AVALON 4.0 — ЗАПУСК НА ANDROID")
    print("=" * 60)
    print(f"📡 Токен: {TOKEN[:10]}...")
    print(f"👥 Админы: {ADMINS}")
    print("🔄 Режим: polling (долгосрочное соединение)")
    print("=" * 60 + "\n")
    
    # Создаём приложение
    application = (
        Application.builder()
        .token(TOKEN)
        .read_timeout(30)
        .write_timeout(120)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    application.bot_data['start_time'] = start_time
    
    # Запускаем фоновую очистку
    asyncio.create_task(phantom_cleanup_loop())
    
    # ConversationHandler для создания персонажа
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
            WAITING_RACE: [CallbackQueryHandler(handle_character_creation, pattern="^(race_|beast_)")],
            WAITING_GENDER: [CallbackQueryHandler(handle_character_creation, pattern="^gender_")],
            WAITING_CLASS: [CallbackQueryHandler(select_class, pattern="^class_")],
        },
        fallbacks=[CommandHandler("cancel", cancel_creation)],
    )
    application.add_handler(conv_handler)
    
    # ===== БАЗОВЫЕ КОМАНДЫ =====
    # NOTE: /start is already registered via ConversationHandler above — do NOT add it again here
    application.add_handler(CommandHandler("profile", show_main_screen))
    application.add_handler(CommandHandler("quests", show_main_screen))
    application.add_handler(CommandHandler("arena", show_main_screen))
    application.add_handler(CommandHandler("rest", show_main_screen))
    application.add_handler(CommandHandler("skills", prestige_miniapp))
    
    # ===== АДМИН-КОМАНДЫ =====
    application.add_handler(CommandHandler("leave", leave_chat))
    application.add_handler(CommandHandler("leave_chat", leave_chat))
    application.add_handler(CommandHandler("admin", admin_help_command))
    application.add_handler(CommandHandler("admin_help", admin_help_command))
    application.add_handler(CommandHandler("ahelp", ahelp_command))
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    application.add_handler(CommandHandler("tech", tech_works))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("resart", restart_bot))
    application.add_handler(CommandHandler("emergency_stop", emergency_stop))
    application.add_handler(CommandHandler("fix_tg", fix_tg_usernames))
    application.add_handler(CommandHandler("cleanup_phantom", cleanup_phantom))
    application.add_handler(CommandHandler("check_player", check_player))
    application.add_handler(CommandHandler("check_errors", check_errors_command))
    application.add_handler(CommandHandler("fix_all", fix_all_errors_command))
    application.add_handler(CommandHandler("list_backups", list_backups_command))
    application.add_handler(CommandHandler("restore_backup", restore_backup_command))
    application.add_handler(CommandHandler("cleanup_backups", cleanup_backups_command))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("convert_proxy", convert_proxy))
    application.add_handler(CommandHandler("ai_analytics", ai_analytics))
    application.add_handler(CommandHandler("ai_memory", ai_memory))
    application.add_handler(CommandHandler("reset_ai", reset_ai))
    application.add_handler(CommandHandler("refresh_proxies", refresh_proxies))
    application.add_handler(CommandHandler("online", online_command))
    application.add_handler(CommandHandler("server_status", server_status))
    application.add_handler(CommandHandler("casino", casino_menu))
    # ===== НЕЙРОНКА =====
    application.add_handler(CommandHandler("ai_status", ai_status))
    application.add_handler(CommandHandler("ai_reset", ai_reset))
    application.add_handler(CommandHandler("ai_graph", ai_graph))
    
    # ===== CALLBACK-ХЕНДЛЕРЫ =====
    application.add_handler(CallbackQueryHandler(change_location, pattern="^loc_"))
    application.add_handler(CallbackQueryHandler(shop_callback_handler, pattern="^shop_"))
    application.add_handler(CallbackQueryHandler(casino_callback_handler, pattern="^casino_"))
    application.add_handler(CallbackQueryHandler(dungeon_callback_handler, pattern="^dungeon_"))
    application.add_handler(CallbackQueryHandler(tavern_menu_back, pattern="^tavern_"))
    application.add_handler(CallbackQueryHandler(order_ale, pattern="^order_ale_"))
    application.add_handler(CallbackQueryHandler(tavern_exit, pattern="^tavern_exit$"))
    application.add_handler(CallbackQueryHandler(clan_create_confirm, pattern="^clan_confirm_"))
    application.add_handler(CallbackQueryHandler(clan_upgrade_handler, pattern="^clan_upgrade_"))
    application.add_handler(CallbackQueryHandler(clan_back_handler, pattern="^clan_back$"))
    application.add_handler(CallbackQueryHandler(fix_callback_handler, pattern="^(restore_backup_|fix_cancel)"))
    application.add_handler(CallbackQueryHandler(top_money, pattern="^top_money$"))
    application.add_handler(CallbackQueryHandler(top_power, pattern="^top_power$"))
    application.add_handler(CallbackQueryHandler(top_level, pattern="^top_level$"))
    application.add_handler(CallbackQueryHandler(top_hunter, pattern="^top_hunter$"))
    application.add_handler(CallbackQueryHandler(equip_wear_menu, pattern="^equip_wear$"))
    application.add_handler(CallbackQueryHandler(equip_remove_menu, pattern="^equip_remove$"))
    application.add_handler(CallbackQueryHandler(upgrade_item_rank_command, pattern="^equip_upgrade$"))
    application.add_handler(CallbackQueryHandler(clan_info_handler, pattern="^clan_info_"))
    application.add_handler(CallbackQueryHandler(clan_join_handler, pattern="^clan_join_"))
    application.add_handler(CallbackQueryHandler(clan_search_back, pattern="^clan_search_back$"))
    application.add_handler(CallbackQueryHandler(gathering_callback_handler, pattern="^(gathering_|alchemy_)"))
    application.add_handler(CallbackQueryHandler(battle_callback_handler, pattern="^(battle_|hide_)"))
    application.add_handler(CallbackQueryHandler(battle_save_handler, pattern="^(battle_save_)"))
    
    # Текстовые хендлеры
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(
    filters.StatusUpdate.WEB_APP_DATA, 
    handle_webapp_data
    ))
    # Обработчик ошибок
    # ===== ТЕМЫ ГОРОДОВ =====
    from city_themes import city_theme_command, play_city_theme
    from faq import faq_command, faq_callback
    application.add_handler(CommandHandler("enemy_personas", enemy_personas_command))
    application.add_handler(CommandHandler("faq", faq_command))
    from whitelist import allow_command, deny_command, list_allowed_command
    application.add_handler(CommandHandler("allow", allow_command))
    application.add_handler(CommandHandler("deny", deny_command))
    application.add_handler(CommandHandler("list_allowed", list_allowed_command))
    application.add_handler(CallbackQueryHandler(faq_callback, pattern="^faq_"))
    application.add_handler(CommandHandler("theme", city_theme_command))
    application.add_handler(CallbackQueryHandler(play_city_theme, pattern="^city_theme_"))

    application.add_error_handler(error_handler)
    
    # Job queue для регенерации
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(regen, interval=REGEN_INTERVAL, first=10)
    
    print("✅ Бот готов к работе!")
    print("📡 Запуск polling (долгосрочное соединение)...")
    print("💡 Нажми Ctrl+C для остановки\n")
    
    # Запускаем polling
    await application.initialize()
    await application.start()
    
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        poll_interval=1.0,
        timeout=15
    )
    
    # Держим бота живым
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        print("\n💾 Сохраняем данные перед выходом...")
        db.save()
        state_manager.save()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


# ===== ТОЧКА ВХОДА =====
def main():
    """Запуск бота (синхронная обёртка)"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("🔄 Перезапуск...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main_async())
        else:
            raise
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Запускаем консоль в отдельном потоке
    threading.Thread(target=console_thread, daemon=True).start()
    
    # Запускаем бота
    main()
