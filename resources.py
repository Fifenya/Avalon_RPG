# resources.py
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from game_data import RESOURCES
from keyboards import get_resources_keyboard
from utils import update_message

def format_resources_text(player) -> str:
    resources = player.get('resources', {})
    
    if not resources:
        return "📦 **РЕСУРСЫ** 📦\n\nУ тебя пока нет ресурсов.\n\n⛏️ Убивай монстров для дропа"
    
    ores, shards, ingots, materials, magic_items, other = [], [], [], [], [], []
    
    for res_id, count in resources.items():
        if res_id in RESOURCES:
            res = RESOURCES[res_id]
            res_info = f"{res['name']}: x{count}"
            res_type = res.get('type', 'other')
            if res_type == 'ore': ores.append(res_info)
            elif res_type == 'shard': shards.append(res_info)
            elif res_type == 'ingot': ingots.append(res_info)
            elif res_type == 'material': materials.append(res_info)
            elif res_type == 'magic': magic_items.append(res_info)
            else: other.append(res_info)
        else:
            other.append(f"{res_id}: x{count}")
    
    text = "📦 **РЕСУРСЫ** 📦\n\n"
    if ores: text += "⛏️ **РУДА:**\n" + "\n".join(ores) + "\n\n"
    if shards: text += "🔮 **ОСКОЛКИ:**\n" + "\n".join(shards) + "\n\n"
    if ingots: text += "🏭 **СЛИТКИ:**\n" + "\n".join(ingots) + "\n\n"
    if materials: text += "🧵 **МАТЕРИАЛЫ:**\n" + "\n".join(materials) + "\n\n"
    if magic_items: text += "✨ **МАГИЧЕСКИЕ ПРЕДМЕТЫ:**\n" + "\n".join(magic_items) + "\n\n"
    if other: text += "📦 **ПРОЧЕЕ:**\n" + "\n".join(other) + "\n"
    
    text += "\n💡 **Как использовать:**\n• 🔥 Плавка: руда + уголь → осколки\n• 🔨 Крафт слитков: 3 осколка → слиток"
    return text

async def show_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
    else:
        user = update.effective_user
    
    uid = str(user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    text = format_resources_text(player)
    await update_message(update, context, text, reply_markup=get_resources_keyboard(), parse_mode='Markdown')