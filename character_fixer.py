# character_fixer.py
"""
Система восстановления персонажа (только когда нет расы/пола/класса)
Вызывается автоматически при входе в игру
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from logger import GameLogger
from keyboards import get_races_inline, get_genders_inline, get_class_keyboard, get_beast_folk_inline

logger = GameLogger()


class CharacterFixer:
    """Класс для восстановления повреждённых персонажей"""
    
    REQUIRED_FIELDS = ['race', 'gender', 'class']
    
    FIELD_DISPLAY = {
        'race': '🧬 Раса',
        'gender': '⚥ Пол',
        'class': '🎭 Класс'
    }
    
    @staticmethod
    def is_complete(player: Player) -> tuple:
        """Проверяет, полностью ли создан персонаж"""
        missing = []
        for field in CharacterFixer.REQUIRED_FIELDS:
            if not player.get(field):
                missing.append(field)
        return (len(missing) == 0, missing)
    
    @staticmethod
    async def check_and_fix(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player) -> bool:
        """Проверяет персонажа и запускает фикс если нужно"""
        is_complete, missing = CharacterFixer.is_complete(player)
        
        if is_complete:
            return True
        
        await CharacterFixer.start_fix_process(update, context, player, missing)
        return False
    
    @staticmethod
    async def start_fix_process(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player, missing_fields: list):
        """Начинает процесс восстановления персонажа"""
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            message_func = query.edit_message_text
        else:
            message_func = update.message.reply_text
        
        uid = player.uid
        player_name = player.get('name', 'герой')
        
        context.user_data['fixing_character'] = True
        context.user_data['fix_uid'] = uid
        
        if 'race' in missing_fields:
            context.user_data['fix_step'] = 'race'
            text = (
                f"📜 **ГИЛЬДИЯ ГЕРОЕВ АВАЛОНА** 📜\n\n"
                f"При проверке твоих документов, **{player_name}**,\n"
                f"Канцелярия Гильдии обнаружила一些问题.\n\n"
                f"⚠️ **Ошибка в анкете героя**\n"
                f"📋 Пустое поле: {CharacterFixer.FIELD_DISPLAY['race']}\n\n"
                f"*«Без расы тебя не внесут в Книгу Героев!»*\n"
                f"— сказал суровый **Секретарь Гильдии**.\n\n"
                f"🎭 Выбери свою расу:"
            )
            await message_func(text, parse_mode='Markdown', reply_markup=get_races_inline())
            
        elif 'gender' in missing_fields:
            context.user_data['fix_step'] = 'gender'
            text = (
                f"📜 **ГИЛЬДИЯ ГЕРОЕВ АВАЛОНА** 📜\n\n"
                f"Продолжаем оформление твоей анкеты, **{player_name}**.\n\n"
                f"⚠️ **Ошибка в анкете героя**\n"
                f"📋 Пустое поле: {CharacterFixer.FIELD_DISPLAY['gender']}\n\n"
                f"*«Как к тебе обращаться, герой?»*\n"
                f"— спросила **Хранительница Реестра**.\n\n"
                f"🎭 Выбери свой пол:"
            )
            await message_func(text, parse_mode='Markdown', reply_markup=get_genders_inline())
            
        elif 'class' in missing_fields:
            context.user_data['fix_step'] = 'class'
            text = (
                f"📜 **ГИЛЬДИЯ ГЕРОЕВ АВАЛОНА** 📜\n\n"
                f"Последний шаг оформления, **{player_name}**.\n\n"
                f"⚠️ **Ошибка в анкете героя**\n"
                f"📋 Пустое поле: {CharacterFixer.FIELD_DISPLAY['class']}\n\n"
                f"*«Какой путь ты изберёшь, воин?»*\n"
                f"— **Мастер Ордена** протягивает свиток.\n\n"
                f"🎭 Выбери свой класс:"
            )
            await message_func(text, parse_mode='Markdown', reply_markup=get_class_keyboard())
    
    @staticmethod
    async def handle_fix_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Обрабатывает callback-запросы во время фикса персонажа"""
        from classes import CLASS_DATA, apply_class_stats
        from main_screen import show_main_screen
        
        if not context.user_data.get('fixing_character'):
            return False
        
        query = update.callback_query
        data = query.data
        uid = str(query.from_user.id)
        
        fix_uid = context.user_data.get('fix_uid')
        if fix_uid and fix_uid != uid:
            await query.answer("❌ Это не твоя анкета!", show_alert=True)
            return True
        
        player = Player(uid)
        player_name = player.get('name', 'герой')
        fix_step = context.user_data.get('fix_step')
        
        # Выбор расы
        if fix_step == 'race':
            if data.startswith("race_"):
                race = data.replace("race_", "")
                if race == "🐾 ЗВЕРОЛЮДЫ":
                    await query.edit_message_text(
                        "🐾 **Выбери тип зверолюда:**",
                        reply_markup=get_beast_folk_inline()
                    )
                    return True
                
                player['race'] = race
                player.save()
                await CharacterFixer.next_step(update, context, player, query)
                return True
                
            elif data.startswith("beast_"):
                beast = data.replace("beast_", "")
                player['race'] = beast
                player.save()
                await CharacterFixer.next_step(update, context, player, query)
                return True
        
        # Выбор пола
        elif fix_step == 'gender' and data.startswith("gender_"):
            gender = data.replace("gender_", "")
            player['gender'] = gender
            player.save()
            await CharacterFixer.next_step(update, context, player, query)
            return True
        
        # Выбор класса
        elif fix_step == 'class' and data.startswith("class_"):
            class_value = data.replace("class_", "")
            for cls, cls_data in CLASS_DATA.items():
                if cls.value == class_value:
                    apply_class_stats(player, cls)
                    break
            
            CharacterFixer.clear_fix_state(context)
            
            await query.edit_message_text(
                f"✅ **АНКЕТА ЗАВЕРШЕНА!**\n\n"
                f"📋 **Твой герой:**\n"
                f"• {CharacterFixer.FIELD_DISPLAY['race']}: {player.get('race')}\n"
                f"• {CharacterFixer.FIELD_DISPLAY['gender']}: {player.get('gender')}\n"
                f"• {CharacterFixer.FIELD_DISPLAY['class']}: {player.get('class')}\n\n"
                f"*«Добро пожаловать в Гильдию, {player_name}!»*\n"
                f"— **Секретарь** ставит печать в твою анкету.\n\n"
                f"🎉 Теперь ты официально зарегистрирован в Авалоне!",
                parse_mode='Markdown'
            )
            
            await show_main_screen(update, context)
            return True
        
        return False
    
    @staticmethod
    async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player, query):
        """Переход к следующему шагу восстановления"""
        _, missing = CharacterFixer.is_complete(player)
        
        if 'gender' in missing:
            text = (
                f"📜 **ГИЛЬДИЯ ГЕРОЕВ АВАЛОНА** 📜\n\n"
                f"Отлично, **{player.get('name')}**! Раса выбрана.\n\n"
                f"⚠️ **Ошибка в анкете героя**\n"
                f"📋 Пустое поле: {CharacterFixer.FIELD_DISPLAY['gender']}\n\n"
                f"*«Как к тебе обращаться, герой?»*\n"
                f"— спросила **Хранительница Реестра**.\n\n"
                f"🎭 Выбери свой пол:"
            )
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_genders_inline())
            context.user_data['fix_step'] = 'gender'
            
        elif 'class' in missing:
            text = (
                f"📜 **ГИЛЬДИЯ ГЕРОЕВ АВАЛОНА** 📜\n\n"
                f"Отлично, **{player.get('name')}**! Пол выбран.\n\n"
                f"⚠️ **Ошибка в анкете героя**\n"
                f"📋 Пустое поле: {CharacterFixer.FIELD_DISPLAY['class']}\n\n"
                f"*«Какой путь ты изберёшь, воин?»*\n"
                f"— **Мастер Ордена** протягивает свиток.\n\n"
                f"🎭 Выбери свой класс:"
            )
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_class_keyboard())
            context.user_data['fix_step'] = 'class'
            
        else:
            CharacterFixer.clear_fix_state(context)
            from main_screen import show_main_screen
            await show_main_screen(update, context)
    
    @staticmethod
    def clear_fix_state(context):
        """Очищает состояние фикса"""
        context.user_data.pop('fixing_character', None)
        context.user_data.pop('fix_step', None)
        context.user_data.pop('fix_uid', None)


character_fixer = CharacterFixer()