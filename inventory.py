# inventory.py - ЭКСПОРТ MAX_INVENTORY_ITEMS
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from keyboards import get_inventory_keyboard
from utils import update_message, is_resource_item

# Максимальное количество предметов в инвентаре (экспортируем для других модулей)
MAX_INVENTORY_ITEMS = 200


def format_inventory_text(player) -> str:
    inventory = player.get('inventory', {'items': [], 'equipped': {}})
    items = inventory.get('items', [])
    equipped = inventory.get('equipped', {})
    
    filtered_items = []
    resource_count = 0
    
    for item in items:
        if is_resource_item(item):
            resource_count += 1
        else:
            filtered_items.append(item)
    
    text = "📦 **ИНВЕНТАРЬ** 📦\n\n"
    
    if filtered_items:
        # Показываем только первые 50, чтобы не перегружать сообщение
        display_items = filtered_items[:50]
        for i, item in enumerate(display_items, 1):
            rarity_icons = {'legendary': '🔴', 'epic': '🟣', 'rare': '🔵', 'uncommon': '🟢', 'common': '⚪'}
            icon = rarity_icons.get(item.get('rarity', 'common'), '⚪')
            item_name = item.get('name', 'Предмет')
            text += f"{i}. {icon} {item_name}\n"
        
        total_displayed = len(display_items)
        total_items = len(filtered_items)
        text += f"\n📊 Всего предметов: {total_items}"
        
        if total_items > total_displayed:
            text += f" (показано {total_displayed})"
        
        if total_items >= MAX_INVENTORY_ITEMS * 0.9:
            text += f"\n⚠️ **Внимание!** Инвентарь почти полон ({total_items}/{MAX_INVENTORY_ITEMS})"
    else:
        text += "В инвентаре нет предметов\n\n🎯 Убивай монстров, чтобы получить предметы!"
    
    if resource_count > 0:
        text += f"\n\n📦 У тебя есть ресурсы ({resource_count} шт.) — смотри в разделе **Ресурсы**"
    
    if equipped:
        text += f"\n\n⚔️ Экипировано предметов: {len(equipped)}"
    
    text += f"\n\n💡 Максимум предметов: {MAX_INVENTORY_ITEMS}"
    
    return text


def can_add_item(player, item) -> bool:
    """Проверяет, можно ли добавить предмет в инвентарь"""
    inventory = player.get('inventory', {'items': []})
    items = inventory.get('items', [])
    non_resource_count = sum(1 for i in items if not is_resource_item(i))
    return non_resource_count < MAX_INVENTORY_ITEMS


async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
        player.save()
    
    text = format_inventory_text(player)
    await update_message(update, context, text, reply_markup=get_inventory_keyboard(), parse_mode='Markdown')