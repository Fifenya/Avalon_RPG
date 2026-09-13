# arena.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import random
from datetime import datetime, timedelta
from typing import Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from logger import GameLogger
from utils import require_character
from config import ARENA_SEASON_DAYS, ARENA_MIN_BET, ARENA_MAX_BET

logger = GameLogger()

arena_ratings = {}
arena_battles = {}
active_arena_requests = {}


class ArenaSystem:
    RANKS = {
        "Бронза": {"min": 0, "emoji": "🥉", "reward": 500},
        "Серебро": {"min": 1100, "emoji": "🥈", "reward": 1000},
        "Золото": {"min": 1200, "emoji": "🥇", "reward": 2000},
        "Платина": {"min": 1300, "emoji": "💎", "reward": 4000},
        "Алмаз": {"min": 1450, "emoji": "✨", "reward": 8000},
        "Мастер": {"min": 1600, "emoji": "👑", "reward": 15000},
        "Грандмастер": {"min": 1800, "emoji": "⭐", "reward": 30000},
        "Легенда": {"min": 2000, "emoji": "🏆", "reward": 50000}
    }
    
    def __init__(self):
        self.season_start = datetime.now()
        self.season_end = self.season_start + timedelta(days=ARENA_SEASON_DAYS)
    
    def get_rating(self, uid: str) -> int:
        return arena_ratings.get(uid, 1000)
    
    def get_rank(self, uid: str) -> Tuple[str, str, int]:
        rating = self.get_rating(uid)
        for rank_name, rank_data in sorted(self.RANKS.items(), key=lambda x: x[1]["min"], reverse=True):
            if rating >= rank_data["min"]:
                return rank_name, rank_data["emoji"], rank_data["reward"]
        return "Бронза", "🥉", 500
    
    def calculate_elo_change(self, winner_rating: int, loser_rating: int) -> Tuple[int, int]:
        expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        k = 32 if winner_rating < 1500 else 24 if winner_rating < 2000 else 16
        winner_change = int(k * (1 - expected_winner))
        loser_change = int(k * (0 - (1 - expected_winner)))
        return winner_change, abs(loser_change)
    
    @require_character
    async def request_arena_fight(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int = 0):
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name
        player = Player(uid)
        
        if bet < ARENA_MIN_BET:
            await update.message.reply_text(f"❌ Минимальная ставка: {ARENA_MIN_BET}💰")
            return
        if bet > ARENA_MAX_BET:
            await update.message.reply_text(f"❌ Максимальная ставка: {ARENA_MAX_BET}💰")
            return
        if player["money"] < bet:
            await update.message.reply_text("❌ У тебя недостаточно денег для этой ставки!")
            return
        
        for bid, data in active_arena_requests.items():
            if data["uid"] == uid:
                await update.message.reply_text("⏳ У тебя уже есть активный запрос на бой!")
                return
        
        request_id = f"arena_{uid}_{datetime.now().timestamp()}"
        active_arena_requests[request_id] = {
            "uid": uid, "name": name, "bet": bet,
            "rating": self.get_rating(uid), "rank": self.get_rank(uid)[0],
            "time": datetime.now()
        }
        
        rating, rank, _ = self.get_rank(uid)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⚔️ Принять вызов", callback_data=f"arena_accept_{request_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"arena_cancel_{request_id}")
        ]])
        
        await update.message.reply_text(
            f"⚔️ **ВЫЗОВ НА АРЕНУ!** ⚔️\n\n"
            f"👤 {name} вызывает на бой!\n"
            f"🏆 Рейтинг: {rating} ({rank})\n"
            f"💰 Ставка: {bet} монет\n\n"
            "_Нажми «Принять» чтобы сразиться!_",
            parse_mode='Markdown', reply_markup=keyboard
        )
    
    @require_character
    async def accept_arena_fight(self, update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: str):
        query = update.callback_query
        
        if request_id not in active_arena_requests:
            await query.edit_message_text("❌ Этот вызов уже недействителен")
            return
        
        request = active_arena_requests[request_id]
        challenger_uid = request["uid"]
        acceptor_uid = str(query.from_user.id)
        acceptor_name = query.from_user.first_name
        
        if acceptor_uid == challenger_uid:
            await query.answer("❌ Нельзя принять свой вызов!", show_alert=True)
            return
        
        for bid, data in active_arena_requests.items():
            if data["uid"] == acceptor_uid:
                await query.answer("⏳ У тебя уже есть активный запрос!", show_alert=True)
                return
        
        challenger = Player(challenger_uid)
        acceptor = Player(acceptor_uid)
        bet = request["bet"]
        
        if challenger["money"] < bet:
            await query.edit_message_text(f"❌ {request['name']} больше не может позволить себе эту ставку!")
            del active_arena_requests[request_id]
            return
        if acceptor["money"] < bet:
            await query.answer("❌ У тебя недостаточно денег для этой ставки!", show_alert=True)
            return
        
        challenger["money"] -= bet
        acceptor["money"] -= bet
        challenger.save()
        acceptor.save()
        
        result = await self.simulate_fight(challenger, acceptor)
        
        challenger_rating = self.get_rating(challenger_uid)
        acceptor_rating = self.get_rating(acceptor_uid)
        
        if result["winner_uid"] == challenger_uid:
            winner_change, loser_change = self.calculate_elo_change(challenger_rating, acceptor_rating)
            arena_ratings[challenger_uid] = challenger_rating + winner_change
            arena_ratings[acceptor_uid] = max(0, acceptor_rating - loser_change)
            challenger["money"] += bet * 2
            challenger["wins"] = challenger.get("wins", 0) + 1
            acceptor["losses"] = acceptor.get("losses", 0) + 1
        else:
            winner_change, loser_change = self.calculate_elo_change(acceptor_rating, challenger_rating)
            arena_ratings[acceptor_uid] = acceptor_rating + winner_change
            arena_ratings[challenger_uid] = max(0, challenger_rating - loser_change)
            acceptor["money"] += bet * 2
            acceptor["wins"] = acceptor.get("wins", 0) + 1
            challenger["losses"] = challenger.get("losses", 0) + 1
        
        challenger.save()
        acceptor.save()
        
        winner_rank, winner_rank_emoji, _ = self.get_rank(result["winner_uid"])
        loser_rank, loser_rank_emoji, _ = self.get_rank(result["loser_uid"])
        
        result_text = (
            f"⚔️ **РЕЗУЛЬТАТ АРЕНЫ!** ⚔️\n\n"
            f"👑 **ПОБЕДИТЕЛЬ:** {result['winner_name']}\n"
            f"   🏆 Рейтинг: {winner_rank_emoji} {winner_rank}\n\n"
            f"💔 **ПРОИГРАВШИЙ:** {result['loser_name']}\n"
            f"   📉 Рейтинг: {loser_rank_emoji} {loser_rank}\n\n"
            f"📊 **Изменение ELO:**\n"
            f"   {result['winner_name']}: +{winner_change}\n"
            f"   {result['loser_name']}: -{loser_change}\n\n"
            f"💰 **Призовые:** {bet * 2} монет\n"
            f"   ({bet} от каждого)\n\n"
            f"🏆 **Новый рейтинг:** {arena_ratings[result['winner_uid']]}"
        )
        
        await query.edit_message_text(result_text, parse_mode='Markdown')
        logger.arena_fight(result['winner_name'], result['loser_name'], bet, winner_change, loser_change)
        del active_arena_requests[request_id]
    
    async def simulate_fight(self, player1: Player, player2: Player) -> Dict:
        p1_power = self._get_combat_power(player1)
        p2_power = self._get_combat_power(player2)
        total_power = p1_power + p2_power
        p1_chance = (p1_power / total_power) * 100 if total_power > 0 else 50
        
        winner = player1 if random.random() * 100 < p1_chance else player2
        loser = player2 if winner == player1 else player1
        
        return {
            "winner_uid": winner.uid, "winner_name": winner["name"],
            "loser_uid": loser.uid, "loser_name": loser["name"]
        }
    
    def _get_combat_power(self, player: Player) -> int:
        base_power = player.get("power", 50)
        inventory = player.get("inventory", {})
        equipped = inventory.get("equipped", {})
        equipment_bonus = sum(item.get("stats", {}).get("power", 0) for item in equipped.values())
        
        player_class = player.get("class")
        if player_class:
            from classes import CLASS_DATA, CharacterClass
            for cls, data in CLASS_DATA.items():
                if cls.value == player_class:
                    equipment_bonus += data["base_stats"].get("power", 0)
                    break
        
        return base_power + equipment_bonus
    
    @require_character
    async def show_arena_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        player = Player(uid)
        rating = self.get_rating(uid)
        rank_name, rank_emoji, season_reward = self.get_rank(uid)
        days_left = (self.season_end - datetime.now()).days
        
        text = (
            f"⚔️ **АРЕНА АВАЛОНА** ⚔️\n\n"
            f"👤 **{player['name']}**\n"
            f"🏆 Рейтинг ELO: **{rating}**\n"
            f"{rank_emoji} Ранг: **{rank_name}**\n\n"
            f"📊 **Статистика:**\n"
            f"   🎯 Побед: {player.get('wins', 0)}\n"
            f"   💔 Поражений: {player.get('losses', 0)}\n\n"
            f"🎁 **Награда за сезон:** {season_reward}💰\n\n"
            f"⏰ До конца сезона: **{days_left} дней**\n\n"
            f"📝 **Как участвовать:**\n"
            f"   `/arena 100` — вызвать на бой со ставкой 100💰"
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏆 Топ арены", callback_data="arena_top")
        ]])
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
        else:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @require_character
    async def show_arena_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sorted_ratings = sorted(arena_ratings.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not sorted_ratings:
            await update.callback_query.edit_message_text("📊 Пока нет игроков на арене!")
            return
        
        text = "🏆 **ТОП АРЕНЫ** 🏆\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, (uid, rating) in enumerate(sorted_ratings):
            player = Player(uid)
            rank_name, rank_emoji, _ = self.get_rank(uid)
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} **{player['name']}**\n"
            text += f"   🏆 {rating} ELO — {rank_emoji} {rank_name}\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Назад", callback_data="arena_back")
        ]])
        
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)


arena = ArenaSystem()