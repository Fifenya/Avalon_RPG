# hospital.py
import asyncio
from datetime import datetime
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database import Player
from logger import GameLogger
from session_manager import session_manager

# NOTE: session_manager.save() was previously called here at module import time — removed (wrong place)
logger = GameLogger()

hospital_patients = {}
hospital_update_tasks = {}  # Хранение задач автообновления
hospital_messages = {}      # Хранение ID сообщений для редактирования


class HospitalSystem:
    BASE_HEAL_RATE = 1
    DISCHARGE_HP_PERCENT = 50
    UPDATE_INTERVAL = 5  # Обновление каждые 5 секунд
    
    HEAL_OPTIONS = {
        "light": {"price": 500, "heal": 50, "name": "🩹 Лёгкое лечение"},
        "medium": {"price": 1000, "heal": 100, "name": "💊 Среднее лечение"},
        "heavy": {"price": 2000, "heal": 200, "name": "🏥 Полное лечение"},
        "critical": {"price": 5000, "heal": 500, "name": "⭐ Экстренное лечение"}
    }
    
    @staticmethod
    def admit(uid: str, player: Player):
        admit_time = datetime.now()
        required_hp = int(player["max_hp"] * HospitalSystem.DISCHARGE_HP_PERCENT / 100)
        
        hospital_patients[uid] = {
            "admit_time": admit_time,
            "required_hp": required_hp,
            "heal_rate": HospitalSystem.BASE_HEAL_RATE,
            "last_update": admit_time
        }
        
        player["location"] = "hospital"
        player["hp"] = 1
        player["death_time"] = None
        player.save()
        
        logger.system(f"🏥 {player.get('name', 'Игрок')} поступил в больницу", f"нужно {required_hp} HP")
    
    @staticmethod
    def process_healing(uid: str, player: Player):
        if uid not in hospital_patients:
            return player.get("hp", 1), 0, False
        
        patient = hospital_patients[uid]
        now = datetime.now()
        
        time_diff = (now - patient["last_update"]).total_seconds()
        heal_amount = int(time_diff * patient["heal_rate"])
        
        if heal_amount > 0:
            current_hp = player.get("hp", 1)
            new_hp = min(patient["required_hp"], current_hp + heal_amount)
            player["hp"] = new_hp
            patient["last_update"] = now
            player.save()
            
            if new_hp >= patient["required_hp"]:
                return new_hp, patient["required_hp"], True
        
        return player.get("hp", 1), patient["required_hp"], False
    
    @staticmethod
    def discharge(uid: str, player: Player) -> bool:
        """Выписывает игрока из больницы. Возвращает True если выписка произошла."""
        if uid not in hospital_patients:
            return False
        
        # Удаляем из списка пациентов
        del hospital_patients[uid]
        
        # Останавливаем задачу автообновления
        if uid in hospital_update_tasks:
            hospital_update_tasks[uid].cancel()
            del hospital_update_tasks[uid]
        
        # Удаляем сообщение из кэша
        if uid in hospital_messages:
            del hospital_messages[uid]
        
        # Возвращаем игрока в город
        player["location"] = "city"
        player.save()
        
        logger.system(f"🏥 {player.get('name', 'Игрок')} выписан из больницы", "")
        return True
    
    @staticmethod
    def get_status_text(uid: str, player: Player) -> str:
        if uid not in hospital_patients:
            return ""
        
        patient = hospital_patients[uid]
        current_hp = player.get("hp", 1)
        required_hp = patient["required_hp"]
        
        remaining_hp = required_hp - current_hp
        if remaining_hp > 0:
            seconds_left = remaining_hp / patient["heal_rate"]
            minutes_left = int(seconds_left // 60)
            seconds_left = int(seconds_left % 60)
            time_left = f"{minutes_left}м {seconds_left}с" if minutes_left > 0 else f"{seconds_left}с"
        else:
            time_left = "0с"
        
        hp_needed_percent = (current_hp - 1) / (required_hp - 1) * 100 if required_hp > 1 else 100
        filled = int(hp_needed_percent / 10)
        progress_bar = "🟩" * filled + "⬜" * (10 - filled)
        
        hp_filled = int(current_hp / max(1, required_hp) * 20)
        hp_bar = "❤️" * hp_filled + "🖤" * (20 - hp_filled)
        
        return (
            f"🏥 **ГОСПИТАЛЬ СВЯТОГО КЛИНКА** 🏥\n\n"
            f"{hp_bar}\n"
            f"❤️ **{current_hp}/{required_hp} HP**\n\n"
            f"📊 **Прогресс лечения:**\n"
            f"{progress_bar} {hp_needed_percent:.1f}%\n\n"
            f"⏱️ **До выписки:** {time_left}\n\n"
            f"💡 Лечение ускоряется за монеты (кнопки ниже)\n\n"
            f"_Монахини молятся за твоё здоровье..._"
        )
    
    @staticmethod
    def get_keyboard(uid: str, player: Player):
        """Возвращает ReplyKeyboardMarkup (обычные кнопки под полем ввода)"""
        if uid not in hospital_patients:
            return None
        
        keyboard = []
        
        # Кнопки лечения
        heal_buttons = []
        for heal_id, heal_data in HospitalSystem.HEAL_OPTIONS.items():
            if player["money"] >= heal_data["price"]:
                heal_buttons.append(KeyboardButton(f"💊 {heal_data['name']} ({heal_data['price']}💰)"))
        
        if heal_buttons:
            row = []
            for btn in heal_buttons:
                row.append(btn)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
        
        patient = hospital_patients[uid]
        if player.get("hp", 1) >= patient["required_hp"]:
            keyboard.append([KeyboardButton("🚪 Выписаться")])
        
        # Навигационные кнопки
        keyboard.append([KeyboardButton("📦 Инвентарь"), KeyboardButton("⚔️ Экипировка")])
        keyboard.append([KeyboardButton("🏆 Топ"), KeyboardButton("📜 Профиль")])
        keyboard.append([KeyboardButton("🏰 Кланы")])
        keyboard.append([KeyboardButton("🔄 Обновить статус"), KeyboardButton("🔙 На главную")])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def quick_heal(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, heal_type: str):
        """Быстрое лечение (вызывается из текстовой кнопки)"""
        if uid not in hospital_patients:
            await update.message.reply_text("❌ Ты не в больнице!")
            return False
        
        if heal_type not in HospitalSystem.HEAL_OPTIONS:
            await update.message.reply_text("❌ Неизвестный тип лечения!")
            return False
        
        player = Player(uid)
        heal_data = HospitalSystem.HEAL_OPTIONS[heal_type]
        
        if player["money"] < heal_data["price"]:
            await update.message.reply_text(f"❌ Нужно {heal_data['price']} монет!")
            return False
        
        player["money"] -= heal_data["price"]
        
        current_hp = player.get("hp", 1)
        required_hp = hospital_patients[uid]["required_hp"]
        new_hp = min(required_hp, current_hp + heal_data["heal"])
        player["hp"] = new_hp
        player.save()
        
        hospital_patients[uid]["last_update"] = datetime.now()
        
        # Обновляем сообщение
        await HospitalSystem.update_hospital_status(update, context, uid, send_new=False)
        
        # Проверяем, вылечился ли игрок
        if new_hp >= required_hp:
            await HospitalSystem.handle_discharge(update, context, uid, player)
            return True
        
        return True
    
    @staticmethod
    async def handle_discharge(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, player: Player):
        """Обрабатывает выписку игрока из больницы"""
        # Выписываем
        if HospitalSystem.discharge(uid, player):
            # Удаляем сообщение больницы
            if uid in hospital_messages:
                try:
                    await context.bot.delete_message(
                        chat_id=int(uid),
                        message_id=hospital_messages[uid]
                    )
                except:
                    pass
                del hospital_messages[uid]
            
            # Отправляем красивое сообщение о выписке
            await context.bot.send_message(
                chat_id=int(uid),
                text="🏥✨ **ВЫ ЗДОРОВЫ!** ✨🏥\n\n"
                     "Сестрица выписывает тебя из госпиталя.\n"
                     "Ты полностью восстановил силы!\n\n"
                     "🌍 **Теперь ты можешь свободно перемещаться по Авалону!**\n\n"
                     "_Будь осторожнее в следующих приключениях..._ 🍀",
                parse_mode='Markdown'
            )
            
            # Возвращаем на главный экран
            from main_screen import show_main_screen
            await show_main_screen(update, context)
    
    @staticmethod
    async def update_hospital_status(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, send_new: bool = False):
        """Обновляет статус в больнице (редактирует сообщение)"""
        if uid not in hospital_patients:
            return
        
        player = Player(uid)
        text = HospitalSystem.get_status_text(uid, player)
        keyboard = HospitalSystem.get_keyboard(uid, player)
        
        try:
            # Если есть сохранённый ID сообщения — редактируем его
            if uid in hospital_messages and hospital_messages[uid]:
                try:
                    await context.bot.edit_message_text(
                        chat_id=int(uid),
                        message_id=hospital_messages[uid],
                        text=text,
                        parse_mode='Markdown'
                    )
                    return
                except Exception as e:
                    print(f"Ошибка редактирования сообщения: {e}")
                    send_new = True
            
            # Отправляем новое сообщение
            if update and update.callback_query:
                msg = await update.callback_query.message.reply_text(text, parse_mode='Markdown')
            elif update and update.message:
                msg = await update.message.reply_text(text, parse_mode='Markdown')
            else:
                msg = await context.bot.send_message(
                    chat_id=int(uid),
                    text=text,
                    parse_mode='Markdown'
                )
            
            # Сохраняем ID сообщения
            hospital_messages[uid] = msg.message_id
            
            # Отправляем клавиатуру отдельно (если нужно)
            if keyboard:
                await context.bot.send_message(
                    chat_id=int(uid),
                    text="📋 Доступные действия:",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            print(f"Ошибка обновления статуса больницы: {e}")
    
    @staticmethod
    def is_in_hospital(uid: str) -> bool:
        return uid in hospital_patients
    
    @staticmethod
    async def auto_update_loop(uid: str, context: ContextTypes.DEFAULT_TYPE):
        """Фоновый цикл автоматического обновления статуса"""
        while uid in hospital_patients:
            await asyncio.sleep(HospitalSystem.UPDATE_INTERVAL)
            
            if uid not in hospital_patients:
                break
            
            player = Player(uid)
            current_hp, required_hp, discharged = HospitalSystem.process_healing(uid, player)
            
            if discharged:
                # Выписываем и отправляем уведомление
                await HospitalSystem.handle_discharge(None, context, uid, player)
                break
            
            # Обновляем статус
            await HospitalSystem.update_hospital_status(None, context, uid, send_new=False)
    
    @staticmethod
    async def manual_discharge(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, player: Player):
        """Ручная выписка (по кнопке)"""
        if uid not in hospital_patients:
            await update.message.reply_text("❌ Ты не в больнице!")
            return
        
        patient = hospital_patients[uid]
        current_hp = player.get("hp", 1)
        
        if current_hp < patient["required_hp"]:
            await update.message.reply_text(
                f"❌ Ты ещё не восстановился! Нужно {patient['required_hp']} HP, у тебя {current_hp}\n"
                f"💡 Используй лечение за монеты чтобы ускориться!"
            )
            return
        
        # Выписываем
        await HospitalSystem.handle_discharge(update, context, uid, player)
    
    @staticmethod
    async def handle_location_check(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, player: Player) -> bool:
        """Проверяет, в больнице ли игрок, и показывает статус"""
        if HospitalSystem.is_in_hospital(uid):
            current_hp, required_hp, discharged = HospitalSystem.process_healing(uid, player)
            
            if discharged:
                await HospitalSystem.handle_discharge(update, context, uid, player)
                return True
            
            # Запускаем фоновое автообновление, если ещё не запущено
            if uid not in hospital_update_tasks:
                task = asyncio.create_task(HospitalSystem.auto_update_loop(uid, context))
                hospital_update_tasks[uid] = task
            
            # Показываем статус
            await HospitalSystem.update_hospital_status(update, context, uid, send_new=True)
            return True
        
        return False


hospital = HospitalSystem()