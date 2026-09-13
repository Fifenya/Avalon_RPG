# casino.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger

logger = GameLogger()

# Мемные фразы
LOSSES = [
    "Бард спел про твоё поражение на всю таверну.",
    "Гоблин украл твои монеты и показал язык.",
    "Кот в сапогах обыграл тебя в кости и скрылся.",
    "Ты проиграл сам себе. В зеркале. Это было жалкое зрелище.",
]

WINS = [
    "Бард сложил оду в твою честь! (пока бесплатно)",
    "Гоблин вернул монеты и добавил свои. Видимо, перепутал.",
    "Ты выиграл! Даже бард удивился.",
    "Фортуна поцеловала тебя в лоб. Осталась помада.",
]


@require_character
async def casino_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню казино"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    text = f"🎰 **КАЗИНО 'КРИВОЙ КЛЫК'** 🎰\n\n"
    text += f"💰 На счету: {player['money']} монет\n\n"
    text += "**Доступные игры:**\n\n"
    text += "🎲 **Кости** (50💰)\n"
    text += "🎰 **Слоты** (100💰)\n"
    text += "🃏 **Блэкджек** (200💰)\n"
    text += "🍺 **Пьяный гоблин** (50💰)\n"
    text += "💀 **Русская рулетка** (500💰)\n"
    
    keyboard = [
        [InlineKeyboardButton("🎲 Кости (50💰)", callback_data="casino_dice")],
        [InlineKeyboardButton("🎰 Слоты (100💰)", callback_data="casino_slots")],
        [InlineKeyboardButton("🃏 Блэкджек (200💰)", callback_data="casino_blackjack")],
        [InlineKeyboardButton("🍺 Пьяный гоблин (50💰)", callback_data="casino_goblin")],
        [InlineKeyboardButton("💀 Русская рулетка (500💰)", callback_data="casino_roulette")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ]
    
    await update_message(update, context, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@require_character
async def casino_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=50):
    """Кости с гоблином"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if player['money'] < bet:
        await query.answer(f"💸 Нужно {bet} монет!", show_alert=True)
        return
    
    player_dice = random.randint(1, 6)
    goblin_dice = random.randint(1, 6)
    
    if random.random() < 0.3:
        goblin_dice = max(goblin_dice, random.randint(4, 6))
        cheat = " (гоблин жульничает!)"
    else:
        cheat = ""
    
    if player_dice > goblin_dice:
        win = bet * 2
        player['money'] += win
        result_text = f"🎉 **ВЫИГРЫШ!** +{win}💰\n{random.choice(WINS)}"
    elif player_dice < goblin_dice:
        player['money'] -= bet
        result_text = f"💔 **ПРОИГРЫШ!** -{bet}💰\n{random.choice(LOSSES)}"
    else:
        result_text = f"🤝 **НИЧЬЯ!** Ставка возвращена."
    
    player.save()
    
    text = f"{result_text}\n\n🎲 Твой бросок: {player_dice}\n🎲 Бросок гоблина: {goblin_dice}{cheat}\n\n💰 Баланс: {player['money']}💰"
    
    keyboard = [[InlineKeyboardButton("🎲 Играть ещё", callback_data="casino_dice")],
                [InlineKeyboardButton("🔙 В меню", callback_data="casino_back")]]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def casino_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=100):
    """Слоты"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if player['money'] < bet:
        await query.answer(f"💸 Нужно {bet} монет!", show_alert=True)
        return
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "💎", "7️⃣", "🐉", "🍺"]
    result = [random.choice(symbols) for _ in range(3)]
    
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            win = bet * 5
            prize_text = f"🎉 **ДЖЕКПОТ!** +{win}💰"
        elif result[0] == "🐉":
            win = bet * 3
            prize_text = f"🐉 **ДРАКОН!** +{win}💰"
        else:
            win = bet * 2
            prize_text = f"🎉 **ТРИ ОДИНАКОВЫХ!** +{win}💰"
        player['money'] += win
    elif result[0] == result[1] or result[1] == result[2]:
        win = bet
        player['money'] += win
        prize_text = f"🎉 **ДВА ОДИНАКОВЫХ!** +{win}💰"
    else:
        player['money'] -= bet
        prize_text = f"💔 **ПРОИГРЫШ!** -{bet}💰\n{random.choice(LOSSES)}"
    
    player.save()
    
    text = f"{prize_text}\n\n{' '.join(result)}\n\n💰 Баланс: {player['money']}💰"
    
    keyboard = [[InlineKeyboardButton("🎰 Крутануть ещё", callback_data="casino_slots")],
                [InlineKeyboardButton("🔙 В меню", callback_data="casino_back")]]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def casino_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=200):
    """Блэкджек у барда"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if player['money'] < bet:
        await query.answer(f"💸 Нужно {bet} монет!", show_alert=True)
        return
    
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        if card == 'A':
            return 11
        return int(card)
    
    cards = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    
    player_cards = [random.choice(cards), random.choice(cards)]
    bard_cards = [random.choice(cards), random.choice(cards)]
    
    player_score = sum(card_value(c) for c in player_cards)
    bard_score = sum(card_value(c) for c in bard_cards)
    
    while bard_score < 17:
        bard_cards.append(random.choice(cards))
        bard_score = sum(card_value(c) for c in bard_cards)
    
    if player_score > 21:
        player['money'] -= bet
        result_text = f"💔 **ПЕРЕБОР!** -{bet}💰\n{random.choice(LOSSES)}"
    elif bard_score > 21:
        win = bet * 2
        player['money'] += win
        result_text = f"🎉 **ВЫИГРЫШ!** +{win}💰\n{random.choice(WINS)}"
    elif player_score > bard_score:
        win = bet * 2
        player['money'] += win
        result_text = f"🎉 **ВЫИГРЫШ!** +{win}💰\n{random.choice(WINS)}"
    elif player_score < bard_score:
        player['money'] -= bet
        result_text = f"💔 **ПРОИГРЫШ!** -{bet}💰\n{random.choice(LOSSES)}"
    else:
        result_text = f"🤝 **НИЧЬЯ!** Ставка возвращена."
    
    player.save()
    
    text = f"{result_text}\n\n🃏 Твои карты: {' '.join(player_cards)} ({player_score})\n🃏 Карты барда: {' '.join(bard_cards[:2])} + ?\n\n💰 Баланс: {player['money']}💰"
    
    keyboard = [[InlineKeyboardButton("🃏 Сыграть ещё", callback_data="casino_blackjack")],
                [InlineKeyboardButton("🔙 В меню", callback_data="casino_back")]]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def casino_goblin(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=50):
    """Пьяный гоблин"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if player['money'] < bet:
        await query.answer(f"💸 Нужно {bet} монет!", show_alert=True)
        return
    
    goblin_drinks = random.randint(1, 5)
    player_drinks = random.randint(1, 3)
    
    if goblin_drinks > player_drinks:
        player['money'] -= bet
        result_text = f"🍺 **ГОБЛИН ПЕРЕПИЛ!** -{bet}💰\nГоблин упал под стол, но успел стырить твои монеты."
    elif goblin_drinks < player_drinks:
        win = bet * 2
        player['money'] += win
        result_text = f"🍺 **ТЫ ПЕРЕПИЛ ГОБЛИНА!** +{win}💰\nГоблин отдал монеты и попросил пощады."
    else:
        player['money'] -= bet
        result_text = f"🍺 **НИЧЬЯ!** Гоблин забирает {bet}💰\nВы оба не помните, что было."
    
    player.save()
    
    text = f"{result_text}\n\n🍺 Ты выпил: {player_drinks} кружек\n🍺 Гоблин выпил: {goblin_drinks} кружек\n\n💰 Баланс: {player['money']}💰"
    
    keyboard = [[InlineKeyboardButton("🍺 Ещё раз", callback_data="casino_goblin")],
                [InlineKeyboardButton("🔙 В меню", callback_data="casino_back")]]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def casino_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=500):
    """Русская рулетка"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if player['money'] < bet:
        await query.answer(f"💸 Нужно {bet} монет!", show_alert=True)
        return
    
    chamber = random.randint(1, 6)
    pull = random.randint(1, 6)
    
    if chamber == pull:
        player['money'] -= bet
        result_text = f"💥 **БАХ!** ...\nТы поседел и потерял {bet}💰"
    else:
        win = bet * 3
        player['money'] += win
        result_text = f"🔫 **КЛИК!** ...\nПусто! Ты выиграл {win}💰"
    
    player.save()
    
    text = f"{result_text}\n\n💰 Баланс: {player['money']}💰"
    
    keyboard = [[InlineKeyboardButton("💀 Рискнуть ещё", callback_data="casino_roulette")],
                [InlineKeyboardButton("🔙 В меню", callback_data="casino_back")]]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def casino_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню казино"""
    await casino_menu(update, context)


@require_character
async def casino_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок казино"""
    query = update.callback_query
    data = query.data
    
    if data == "casino_dice":
        await casino_dice(update, context)
    elif data == "casino_slots":
        await casino_slots(update, context)
    elif data == "casino_blackjack":
        await casino_blackjack(update, context)
    elif data == "casino_goblin":
        await casino_goblin(update, context)
    elif data == "casino_roulette":
        await casino_roulette(update, context)
    elif data == "casino_back":
        await casino_back(update, context)