# work.py - ИСПРАВЛЕННАЯ (убраны глобальные вызовы session_manager.save())
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from game_data import JOBS_BY_LOCATION, RACES
from keyboards import get_work_keyboard
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger

logger = GameLogger()

# Активные работы
active_jobs = {}


@require_character
async def work_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные работы"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    if uid in active_jobs:
        job_data = active_jobs[uid]
        remaining = job_data['finish_time'] - datetime.now()
        total_secs = max(0, int(remaining.total_seconds()))
        minutes = total_secs // 60
        seconds = total_secs % 60
        await update_message(update, context, f"⏳ Ты уже работаешь! Осталось: {minutes}:{seconds:02d}")
        return
    
    current_loc = player.get('location', 'city')
    loc_jobs = JOBS_BY_LOCATION.get(current_loc, JOBS_BY_LOCATION['city'])
    
    text = f"💼 **РАБОТА**\n📍 {loc_jobs['name']}\n\n**Доступные профессии:**\n\n"
    
    jobs_list = []
    for job in loc_jobs['jobs']:
        can_work = True
        req_text = ""
        
        if 'level' in job.get('requirements', {}):
            if player['level'] < job['requirements']['level']:
                can_work = False
                req_text += f" ❌ (нужен ур.{job['requirements']['level']})"
        
        if 'power' in job.get('requirements', {}):
            if player['power'] < job['requirements']['power']:
                can_work = False
                req_text += f" ❌ (нужно ⚔️{job['requirements']['power']})"
        
        status = "✅" if can_work else "❌"
        text += f"{status} **{job['name']}**{req_text}\n"
        text += f"   {job['desc']}\n"
        text += f"   💰 {job['min_earn']}-{job['max_earn']} | 📚 +{job['exp_reward']} | ⏱️ {job['time']} сек\n\n"
        
        if can_work:
            jobs_list.append(job)
    
    context.user_data['available_jobs'] = jobs_list
    
    await update_message(update, context, text, reply_markup=get_work_keyboard(jobs_list), parse_mode='Markdown')


@require_character
async def start_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        job_name = query.data.replace("work_", "")
        user = query.from_user
    else:
        job_name = update.message.text.replace("💼 ", "")
        user = update.effective_user
    
    uid = str(user.id)
    player = Player(uid)
    
    if uid in active_jobs:
        await update_message(update, context, "⏳ Ты уже работаешь! Дождись завершения.")
        return
    
    available_jobs = context.user_data.get('available_jobs', [])
    selected_job = None
    
    for job in available_jobs:
        if job['name'] == job_name:
            selected_job = job
            break
    
    if not selected_job:
        await update_message(update, context, "❌ Работа не найдена или недоступна!")
        return
    
    finish_time = datetime.now() + timedelta(seconds=selected_job['time'])
    active_jobs[uid] = {
        'job': selected_job,
        'finish_time': finish_time,
        'context': context
    }
    
    await update_message(update, context, 
        f"💼 Ты начал работать: **{selected_job['name']}**\n"
        f"⏱️ Время: {selected_job['time']} сек\n\n"
        f"_Работай усердно..._",
        parse_mode='Markdown'
    )
    
    asyncio.create_task(finish_work(uid, selected_job, context))


async def finish_work(uid, job, context):
    """Завершение работы с проверкой существования игрока"""
    await asyncio.sleep(job['time'])
    
    if uid not in active_jobs:
        return
    
    job_data = active_jobs.get(uid)
    if not job_data:
        return
    
    try:
        player = Player(uid)
        
        # Проверяем, существует ли игрок
        if player.data.get('_temp') or not player.get('race'):
            del active_jobs[uid]
            print(f"⚠️ Игрок {uid} не найден при завершении работы")
            return
        
        # Базовая награда
        earned = random.randint(job['min_earn'], job['max_earn'])
        
        # Расовый бонус
        race_bonus = RACES.get(player.get('race'), {}).get('mult', 1.0)
        earned = int(earned * race_bonus)
        
        player['money'] += earned
        player['exp'] += job['exp_reward']
        player['works_done'] = player.get('works_done', 0) + 1
        
        # Проверка уровня
        level_up_text = ""
        exp_needed = player['level'] * 100
        if player['exp'] >= exp_needed:
            player['level'] += 1
            player['power'] += 5
            player['max_hp'] += 20
            player['hp'] = player['max_hp']
            player['exp'] -= exp_needed
            level_up_text = f"\n\n🎉 **УРОВЕНЬ ПОВЫШЕН!** Теперь уровень {player['level']}! 🎉"
            logger.level_up(player['name'], player['level'], 5, 20)
        
        # Шанс получить ресурсы
        if job.get('resources'):
            if random.random() < 0.3:
                if 'resources' not in player.data:
                    player['resources'] = {}
                for res, amount in job['resources'].items():
                    player['resources'][res] = player['resources'].get(res, 0) + amount
        
        # Проверка достижений
        from achievements import AchievementsSystem
        ach = AchievementsSystem()
        new_achs = ach.check_achievements(uid)
        ach_text = ""
        if new_achs:
            ach_text = "\n\n🏆 **НОВЫЕ ДОСТИЖЕНИЯ!** 🏆\n"
            for a in new_achs:
                ach_text += f"{a['emoji']} {a['name']} +{a['reward']}💰\n"
        
        player.save()
        del active_jobs[uid]
        
        logger.work(player['name'], earned, player['money'], player.get('race', ''))
        
        await context.bot.send_message(
            chat_id=int(uid),
            text=f"✅ **Работа завершена!**\n\n"
                 f"Ты заработал: {earned}💰\n"
                 f"Получено опыта: {job['exp_reward']}📚{level_up_text}{ach_text}",
            parse_mode='Markdown'
        )
        await show_main_screen(None, context)
        
    except Exception as e:
        print(f"❌ Ошибка завершения работы для {uid}: {e}")
        if uid in active_jobs:
            del active_jobs[uid]