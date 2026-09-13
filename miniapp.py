# miniapp.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import json
import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message, require_character
from logger import GameLogger

logger = GameLogger()

# Путь к HTML файлу Mini App
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://fifenya.github.io/avalon_skills/")


async def prestige_miniapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть Mini App с ветками прокачки"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    # Проверяем наличие диплома
    from shared.diploma_manager import diploma_manager
    diploma = diploma_manager.get_diploma(uid)
    
    if not diploma:
        await update_message(update, context,
            "🎓 **ВЕТКИ ПРОКАЧКИ** 🎓\n\n"
            "У тебя пока нет диплома Академии Магии.\n\n"
            "📜 **Как получить диплом:**\n"
            "1. Поступи в Академию через `/start` в боте Академии\n"
            "2. Выбери факультет и специализацию\n"
            "3. Выполняй практики, выигрывай дуэли\n"
            "4. Сдай теоретический экзамен\n"
            "5. Получи диплом командой `/diploma`\n\n"
            "💡 Диплом даёт очки прокачки и доступ к веткам усиления!")
        return
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🎓 Открыть ветки прокачки",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ], [
        InlineKeyboardButton("🔙 На главную", callback_data="main_screen")
    ]])
    
    points = diploma_manager.get_prestige_data(uid).prestige_points
    diploma_emoji = "🔴" if diploma.diploma_type == 'red' else "🔵"
    diploma_name = "КРАСНЫЙ ДИПЛОМ" if diploma.diploma_type == 'red' else "СИНИЙ ДИПЛОМ"
    
    await update_message(update, context,
        f"🎓 **ИНТЕРАКТИВНЫЕ ВЕТКИ ПРОКАЧКИ** 🎓\n\n"
        f"{diploma_emoji} Диплом: **{diploma_name}**\n"
        f"📊 Очков прокачки: **{points}**\n\n"
        f"✨ Нажми на кнопку ниже, чтобы открыть визуальное дерево навыков!\n\n"
        f"_Выбирай навыки, трать очки и становись сильнее!_",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из Mini App"""
    uid = str(update.effective_user.id)
    
    try:
        data = json.loads(update.message.web_app_data.data)
        action = data.get('action')
        
        print(f"📥 [Mini App] Получен запрос от {uid}: {action}")
        
        from shared.diploma_manager import diploma_manager
        from prestige_system import prestige_system
        
        # ===== ТЕСТОВЫЙ ОТВЕТ — ВСЕГДА ОТВЕЧАЕМ =====
        if action == 'test':
            response = {
                'type': 'test_response',
                'message': '✅ Бот работает и отвечает!',
                'your_action': action,
                'timestamp': __import__('time').time()
            }
            print(f"📤 Отправляем тестовый ответ")
            await update.message.reply_text(json.dumps(response))
            return
        
        # ===== ЗАПРОС ДАННЫХ =====
        if action == 'get_prestige_data':
            diploma = diploma_manager.get_diploma(uid)
            diploma_type = diploma.diploma_type if diploma else None
            prestige_data = diploma_manager.get_prestige_data(uid)
            
            if not diploma_type:
                response = {
                    'type': 'prestige_data',
                    'diploma_type': None,
                    'prestige_points': 0,
                    'branches': []
                }
            else:
                branches, _ = prestige_system.get_available_branches(uid)
                branches_detail = []
                for branch in branches:
                    branch_info = prestige_system.get_branch_info(uid, branch['id'])
                    if branch_info:
                        branches_detail.append(branch_info)
                
                response = {
                    'type': 'prestige_data',
                    'diploma_type': diploma_type,
                    'prestige_points': prestige_data.prestige_points,
                    'branches': branches_detail
                }
            
            print(f"📤 [Mini App] Отправка данных для {uid}")
            await update.message.reply_text(json.dumps(response))
        
        # ===== УЛУЧШЕНИЕ НАВЫКА =====
        elif action == 'upgrade_skill':
            branch_id = data.get('branch_id')
            level = data.get('level')
            cost = data.get('cost', 1)
            
            print(f"⭐ [Mini App] Попытка улучшить {branch_id} уровень {level}")
            
            result = prestige_system.upgrade_branch(uid, branch_id)
            
            if result.get('success'):
                response = {
                    'type': 'upgrade_success',
                    'message': result.get('message', 'Навык улучшен!')
                }
            else:
                response = {
                    'type': 'upgrade_error',
                    'message': result.get('message', 'Ошибка улучшения!')
                }
            
            await update.message.reply_text(json.dumps(response))
        
        # ===== ТЕСТОВЫЙ ЗАПРОС =====
        elif action == 'test':
            response = {
                'type': 'test_response',
                'message': 'Бот работает!',
                'timestamp': __import__('time').time()
            }
            await update.message.reply_text(json.dumps(response))
        
        # ===== НЕИЗВЕСТНОЕ ДЕЙСТВИЕ =====
        else:
            print(f"⚠️ [Mini App] Неизвестное действие: {action}")
            response = {
                'type': 'error',
                'message': f'Неизвестное действие: {action}'
            }
            await update.message.reply_text(json.dumps(response))
            
    except Exception as e:
        print(f"❌ [Mini App] Ошибка: {e}")
        response = {
            'type': 'error',
            'message': f'Ошибка: {str(e)}'
        }
        await update.message.reply_text(json.dumps(response))