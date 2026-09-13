# guardian.py - Страж Авалона 3.0
# Мемы как часть механики наказания

import time
from functools import wraps
from collections import defaultdict
from telegram import Update
import random

# ===== МЕМНЫЕ НАКАЗАНИЯ =====
# Каждый мем уже содержит в себе механику наказания

PUNISHMENT_MEMES = {
    # Лёгкие нарушения (кулдаун 3 сек)
    "light": [
        {
            "cooldown": 3,
            "text": "🍺 **Бард**\n\n— Ты чего дёргаешься, герой?\n"
                    "Дай гоблинам доиграть в кости.\n"
                    "Сиди тихо **3 секунды**, а то песню спою.\n"
                    "_Бард настраивает лютню._"
        },
        {
            "cooldown": 3,
            "text": "🐉 **Дракон**\n\nДракон приоткрыл глаз:\n"
                    "— Кто там шуршит? Я спать хочу.\n"
                    "Замри на **3 секунды**, пока я не проснулся.\n"
                    "_Дракон зевнул и выпустил струйку дыма._"
        },
        {
            "cooldown": 3,
            "text": "👾 **Гоблин**\n\nГоблин достал песочные часы:\n"
                    "— Ты слишком часто команды тыкаешь!\n"
                    "Смотри, как песок сыплется... **3 секунды** тишины!\n"
                    "_Гоблин перевернул часы._"
        },
    ],
    
    # Средние нарушения (кулдаун 7 сек)
    "medium": [
        {
            "cooldown": 7,
            "text": "📜 **Летописец**\n\nЛетописец макнул перо в чернила:\n"
                    "«Смертный, твоя активность заносится в Книгу Терпения.\n"
                    "**7 секунд** тишины. Используй это время,\n"
                    "чтобы выучить `/help`.»"
        },
        {
            "cooldown": 7,
            "text": "🍺 **Бард**\n\nБард бросил кружку:\n"
                    "— Ты чо, самый нетерпеливый герой в этом сезоне?!\n"
                    "Заткнись на **7 секунд**, пока я песню не сочинил!\n"
                    "_Бард взял лютню._"
        },
        {
            "cooldown": 7,
            "text": "🐉 **Дракон**\n\nДракон высунул морду:\n"
                    "— Ты меня разбудил. Снова.\n"
                    "В наказание ты будешь молчать **7 секунд**.\n"
                    "_Дракон зевнул и спрятался обратно._"
        },
    ],
    
    # Тяжёлые нарушения (изгнание на 30 минут)
    "heavy": [
        {
            "exile_minutes": 30,
            "text": "🏚️ **СТРАЖА АВАЛОНА**\n\n"
                    "Стражник схватил тебя за шкирку:\n"
                    "— Ты нарушил закон! За такое — **изгнание на 30 минут**!\n"
                    "Вали за ворота. Вернёшься, когда остынешь.\n"
                    "_Стражник пнул тебя в сторону выхода._"
        },
        {
            "exile_minutes": 30,
            "text": "📜 **Свиток Судеб**\n\n"
                    "Свиток вспыхнул алым:\n"
                    "«Смертный, за твои прегрешения ты **изгнан из Авалона на 30 минут**.\n"
                    "Пусть это время пойдёт тебе на пользу.\n"
                    "Изучи `/help`.»"
        },
        {
            "exile_minutes": 30,
            "text": "🐉 **Король драконов**\n\n"
                    "Огромный дракон приземлился перед тобой:\n"
                    "— Ты посмел нарушить покой Авалона?\n"
                    "**Изгнание на 30 минут**. Пшёл вон, смертный.\n"
                    "_Дракон взмахнул крыльями._"
        },
    ],
    
    # Усталость от боев (штрафы)
    "fatigue": [
        {
            "penalty": {"power": -5, "crit": -0.02},
            "text": "🩸 **ИСТОЩЕНИЕ**\n\n"
                    "Твои мышцы горят, лёгкие сжимаются.\n"
                    "Ты слишком много дерёшься, герой.\n"
                    "**Штраф: -5 силы, -2% крита**.\n"
                    "Отдохни в таверне (`/rest`), пока не сдох."
        },
        {
            "penalty": {"power": -8},
            "text": "🍺 **Бард**\n\n"
                    "Бард покачал головой:\n"
                    "— Ты чего, решил монстров истребить за один заход?\n"
                    "Отдыхай, герой. **Штраф: -8 силы**.\n"
                    "А то гоблины начнут ставить на тебя ставки."
        },
        {
            "penalty": {"crit": -0.03, "power": -3},
            "text": "💀 **Глас Бездны**\n\n"
                    "Из темноты раздался шёпот:\n"
                    "— Ты истощён, смертный. Твоё тело не железное.\n"
                    "**Штраф: -3 силы, -3% крита**.\n"
                    "_Бездна поглощает твою выносливость._"
        },
    ],
}


# ===== СИСТЕМА ЗАЩИТЫ =====
class Guardian:
    def __init__(self):
        self.violators = defaultdict(lambda: {"count": 0, "last": 0, "ban_until": 0})
        self.fatigue = defaultdict(int)
    
    def check_spam(self, user_id: int, limit: int = 5, window: int = 30) -> dict:
        """Проверка на спам с мемным наказанием"""
        now = time.time()
        v = self.violators[user_id]
        
        if now - v["last"] > 3600:
            v["count"] = 0
        
        v["last"] = now
        v["count"] += 1
        
        # Лёгкое нарушение
        if v["count"] <= limit + 1:
            meme = random.choice(PUNISHMENT_MEMES["light"])
            return {
                "blocked": True,
                "exiled": False,
                "cooldown": meme["cooldown"],
                "message": meme["text"]
            }
        
        # Среднее нарушение
        elif v["count"] <= limit + 3:
            meme = random.choice(PUNISHMENT_MEMES["medium"])
            return {
                "blocked": True,
                "exiled": False,
                "cooldown": meme["cooldown"],
                "message": meme["text"]
            }
        
        # Тяжёлое нарушение — изгнание
        else:
            meme = random.choice(PUNISHMENT_MEMES["heavy"])
            v["ban_until"] = now + meme["exile_minutes"] * 60
            return {
                "blocked": True,
                "exiled": True,
                "ban_until": v["ban_until"],
                "message": meme["text"]
            }
    
    def add_fatigue(self, user_id: int) -> dict:
        """Усталость от боев"""
        self.fatigue[user_id] += 1
        
        if self.fatigue[user_id] >= 4:
            meme = random.choice(PUNISHMENT_MEMES["fatigue"])
            return {
                "fatigued": True,
                "message": meme["text"],
                "penalty": meme["penalty"]
            }
        return {"fatigued": False}
    
    def clear_fatigue(self, user_id: int):
        self.fatigue[user_id] = 0
    
    def is_exiled(self, user_id: int) -> bool:
        return self.violators[user_id]["ban_until"] > time.time()
    
    def get_exile_time(self, user_id: int) -> int:
        remaining = self.violators[user_id]["ban_until"] - time.time()
        return max(0, int(remaining))


guardian = Guardian()


# ===== ДЕКОРАТОР ЗАЩИТЫ =====
def protect(limit: int = 5, window: int = 30):
    """Защита от спама — с мемами"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context, *args, **kwargs):
            uid = update.effective_user.id
            
            # Проверка изгнания
            if guardian.is_exiled(uid):
                remaining = guardian.get_exile_time(uid)
                minutes = remaining // 60
                seconds = remaining % 60
                await update.message.reply_text(
                    f"🏚️ **ТЫ В ИЗГНАНИИ**\n\n"
                    f"Ворота Авалона откроются через {minutes}:{seconds:02d}\n"
                    f"_Стражник у ворот скучает без тебя._",
                    parse_mode='Markdown'
                )
                return
            
            # Лимиты
            now = time.time()
            if 'protect_ts' not in context.user_data:
                context.user_data['protect_ts'] = []
            
            ts = context.user_data['protect_ts']
            ts[:] = [t for t in ts if now - t < window]
            
            if len(ts) >= limit:
                result = guardian.check_spam(uid, limit, window)
                await update.message.reply_text(result["message"], parse_mode='Markdown')
                
                # Искусственная задержка
                if result.get("cooldown"):
                    context.user_data['protect_ts'].append(now + result["cooldown"])
                return
            
            ts.append(now)
            
            # Усталость для боевых команд
            if func.__name__ in ['hunt_start', 'battle_attack']:
                fatigue = guardian.add_fatigue(uid)
                if fatigue["fatigued"]:
                    await update.message.reply_text(fatigue["message"], parse_mode='Markdown')
                    if "penalty" in fatigue:
                        context.user_data['fatigue_penalty'] = fatigue["penalty"]
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


# ===== ДЛЯ АДМИНОВ =====
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        from config import ADMINS
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text(
                "⚔️ **НЕТ ПРАВА**\n\n"
                "Ты не Судья Авалона.\n"
                "_Ступай своей дорогой, путник._",
                parse_mode='Markdown'
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


# ===== КОМАНДА ОТДЫХА =====
async def rest(update: Update, context):
    """Снять усталость в таверне"""
    uid = update.effective_user.id
    guardian.clear_fatigue(uid)
    context.user_data.pop('fatigue_penalty', None)
    
    await update.message.reply_text(
        "🍺 **ТАВЕРНА**\n\n"
        "Ты отдохнул у камина, выпил кружку эля.\n"
        "Бард сыграл тебе песню про подвиги.\n\n"
        "✅ Усталость прошла! Можешь снова в бой.\n\n"
        "_Бард: «Заходи ещё, герой!»_",
        parse_mode='Markdown'
    )