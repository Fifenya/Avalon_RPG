# logger.py
from datetime import datetime
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    PURPLE = '\033[35m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

class GameLogger:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            'commands': 0,
            'start': 0,
            'profile': 0,
            'hunts': 0,
            'hunt_wins': 0,
            'hunt_losses': 0,
            'battles': 0,
            'flees': 0,
            'crits': 0,
            'works': 0,
            'shops': 0,
            'buys': 0,
            'clan_creates': 0,
            'clan_joins': 0,
            'clan_leaves': 0,
            'clan_bank': 0,
            'crafts': 0,
            'smelts': 0,
            'equips': 0,
            'errors': 0,
            'messages': 0,
            'buttons': 0
        }
        self.players_online = set()
        self.player_actions = {}
    
    def _timestamp(self):
        return datetime.now().strftime('%H:%M:%S')
    
    def _print(self, color, emoji, category, message, details=""):
        timestamp = self._timestamp()
        log_line = f"{color}[{timestamp}]{Colors.END} {emoji} "
        log_line += f"{Colors.BOLD}{category}{Colors.END} | {message}"
        if details:
            log_line += f" {Colors.DIM}{details}{Colors.END}"
        print(log_line)
        self.stats['messages'] += 1
    
    # ===== СИСТЕМНЫЕ ЛОГИ =====
    def system(self, message, details=""):
        self._print(Colors.CYAN, "🖥️", "СИСТЕМА", message, details)
    
    def command(self, user_id, user_name, command, args=""):
        self.stats['commands'] += 1
        if command == "start":
            self.stats['start'] += 1
        elif command == "profile":
            self.stats['profile'] += 1
        elif command == "shop":
            self.stats['shops'] += 1
        elif command == "work":
            self.stats['works'] += 1
        elif command == "clan":
            self.stats['clan_creates'] += 1
        
        self.players_online.add(user_name)
        
        if user_name not in self.player_actions:
            self.player_actions[user_name] = []
        self.player_actions[user_name].append(f"/{command}")
        
        self._print(Colors.CYAN, "▶️", "КОМАНДА",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"/{command} {args}")
    
    def button(self, user_name, button_name, menu=""):
        self.stats['buttons'] += 1
        self._print(Colors.BLUE, "🔘", "КНОПКА",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"{button_name} | {menu}")
    
    def error(self, user_name, error_type, details=""):
        self.stats['errors'] += 1
        self._print(Colors.RED, "❌", "ОШИБКА",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"{error_type}: {details}")
    
    # ===== ИГРОВЫЕ ЛОГИ =====
    def new_player(self, user_name, race=None, gender=None):
        self.stats['start'] += 1
        race_info = f" | {race} {gender}" if race else ""
        self._print(Colors.GREEN, "🌟", "НОВЫЙ ИГРОК",
                   f"{Colors.BOLD}{user_name}{Colors.END}{race_info}")
    
    def profile(self, user_name, money, power, level, mana, location=None):
        location_info = f" | 📍{location}" if location else ""
        self._print(Colors.BLUE, "📜", "ПРОФИЛЬ",
                   f"{Colors.BOLD}{user_name}{Colors.END}{location_info}",
                   f"ур.{level} | 💰{money} | ⚔️{power} | 💙{mana}")
    
    # ===== ОХОТА И БОИ =====
    def hunt_start(self, user_name, enemy_name, enemy_hp, enemy_power):
        self.stats['hunts'] += 1
        self._print(Colors.MAGENTA, "👾", "ОХОТА",
                   f"{Colors.BOLD}{user_name}{Colors.END} встретил {enemy_name}",
                   f"❤️{enemy_hp} ⚔️{enemy_power}")
    
    def battle_turn(self, user_name, turn, player_hp, enemy_hp, action, damage):
        self.stats['battles'] += 1
        self._print(Colors.YELLOW, "⚔️", f"БОЙ (р.{turn})",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"{action} | урон {damage} | ❤️{player_hp} | 👾{enemy_hp}")
    
    def crit(self, user_name, damage):
        self.stats['crits'] += 1
        self._print(Colors.RED, "💥", "КРИТ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"нанёс {damage} урона!")
    
    def dodge(self, user_name):
        self._print(Colors.CYAN, "💨", "УВОРОТ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   "увернулся от атаки!")
    
    def block(self, user_name, blocked):
        self._print(Colors.BLUE, "🛡️", "БЛОК",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"заблокировал {blocked} урона!")
    
    def flee(self, user_name, success):
        self.stats['flees'] += 1
        status = "✅ успешно" if success else "❌ неудачно"
        self._print(Colors.YELLOW, "🏃", "ПОБЕГ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   status)
    
    def hunt_win(self, user_name, enemy_name, reward, exp, drops=None):
        self.stats['hunt_wins'] += 1
        drop_text = f" | Дроп: {len(drops)} предм." if drops else ""
        self._print(Colors.GREEN, "🏆", "ПОБЕДА",
                   f"{Colors.BOLD}{user_name}{Colors.END} победил {enemy_name}",
                   f"+{reward}💰 +{exp}📚{drop_text}")
    
    def hunt_lose(self, user_name, enemy_name, lost):
        self.stats['hunt_losses'] += 1
        self._print(Colors.RED, "💔", "ПОРАЖЕНИЕ",
                   f"{Colors.BOLD}{user_name}{Colors.END} проиграл {enemy_name}",
                   f"-{lost}💰")
    
    def level_up(self, user_name, new_level, power_gain, hp_gain):
        self._print(Colors.GREEN, "⭐", "УРОВЕНЬ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"достиг {new_level} ур. | +{power_gain}⚔️ | +{hp_gain}❤️")
    
    # ===== ЭКОНОМИКА =====
    def work(self, user_name, earned, total, race):
        self.stats['works'] += 1
        self._print(Colors.GREEN, "💼", "РАБОТА",
                   f"{Colors.BOLD}{user_name}{Colors.END} ({race})",
                   f"+{earned}💰 | Всего: {total}💰")
    
    def shop(self, user_name, action, items_count=None):
        self.stats['shops'] += 1
        details = f"товаров: {items_count}" if items_count else ""
        self._print(Colors.YELLOW, "🏪", "МАГАЗИН",
                   f"{Colors.BOLD}{user_name}{Colors.END} {action}",
                   details)
    
    def buy(self, user_name, item, price, balance):
        self.stats['buys'] += 1
        emoji = "⚔️" if "меч" in item.lower() or "оружи" in item.lower() else "🛡️" if "щит" in item.lower() else "🧪"
        self._print(Colors.YELLOW, emoji, "ПОКУПКА",
                   f"{Colors.BOLD}{user_name}{Colors.END} купил {item}",
                   f"-{price}💰 | Осталось: {balance}💰")
    
    # ===== КРАФТ =====
    def craft_start(self, user_name, item_name, time):
        self.stats['crafts'] += 1
        self._print(Colors.PURPLE, "🔨", "КРАФТ",
                   f"{Colors.BOLD}{user_name}{Colors.END} начал создавать {item_name}",
                   f"⏱️ {time}")
    
    def craft_complete(self, user_name, item_name, count):
        self._print(Colors.GREEN, "✅", "КРАФТ",
                   f"{Colors.BOLD}{user_name}{Colors.END} создал {item_name}",
                   f"x{count}")
    
    def smelt_start(self, user_name, item_name, time):
        self.stats['smelts'] += 1
        self._print(Colors.PURPLE, "🔥", "ПЛАВКА",
                   f"{Colors.BOLD}{user_name}{Colors.END} начал плавить {item_name}",
                   f"⏱️ {time}")
    
    # ===== ИНВЕНТАРЬ =====
    def equip(self, user_name, item_name, slot):
        self.stats['equips'] += 1
        self._print(Colors.BLUE, "📦", "ЭКИПИРОВКА",
                   f"{Colors.BOLD}{user_name}{Colors.END} надел {item_name}",
                   f"в слот {slot}")
    
    def unequip(self, user_name, item_name, slot):
        self._print(Colors.BLUE, "📦", "СНЯТО",
                   f"{Colors.BOLD}{user_name}{Colors.END} снял {item_name}",
                   f"из слота {slot}")
    
    def drop_received(self, user_name, items_count, monster_name):
        self._print(Colors.MAGENTA, "🎁", "ДРОП",
                   f"{Colors.BOLD}{user_name}{Colors.END} получил {items_count} предм.",
                   f"от {monster_name}")
    
    # ===== КЛАНЫ =====
    def clan_create(self, user_name, clan_name, price):
        self.stats['clan_creates'] += 1
        self._print(Colors.CYAN, "🏰", "КЛАН СОЗДАН",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"'{clan_name}' | -{price}💰")
    
    def clan_join(self, user_name, clan_name):
        self.stats['clan_joins'] += 1
        self._print(Colors.GREEN, "👥", "ВСТУПЛЕНИЕ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"присоединился к клану '{clan_name}'")
    
    def clan_leave(self, user_name, clan_name):
        self.stats['clan_leaves'] += 1
        self._print(Colors.YELLOW, "👋", "ВЫХОД",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"покинул клан '{clan_name}'")
    
    def clan_bank(self, user_name, action, resource, amount):
        self.stats['clan_bank'] += 1
        action_emoji = "📥" if action == "положил" else "📤"
        self._print(Colors.YELLOW, action_emoji, "БАНК",
                   f"{Colors.BOLD}{user_name}{Colors.END} {action} в банк",
                   f"{resource} x{amount}")
    
    # ===== ЛОКАЦИИ =====
    def location_change(self, user_name, from_loc, to_loc):
        self._print(Colors.CYAN, "🗺️", "ПЕРЕМЕЩЕНИЕ",
                   f"{Colors.BOLD}{user_name}{Colors.END}",
                   f"{from_loc} → {to_loc}")
    
    # ===== АДМИН-ДЕЙСТВИЯ =====
    def admin_action(self, admin_name, action, target=None, details=""):
        target_info = f" | 👤 {target}" if target else ""
        self._print(Colors.RED, "👑", "АДМИН",
                   f"{Colors.BOLD}{admin_name}{Colors.END}{target_info}",
                   f"{action} {details}")
    
    def broadcast(self, admin_name, recipients_count, silent_target=None):
        silent_info = f" (тихо для {silent_target})" if silent_target else ""
        self._print(Colors.MAGENTA, "📢", "РАССЫЛКА",
                   f"{Colors.BOLD}{admin_name}{Colors.END}",
                   f"{recipients_count} игроков{silent_info}")
    
    def tech_works(self, admin_name, status):
        status_text = "ВКЛ" if status else "ВЫКЛ"
        self._print(Colors.RED, "🔧", "ТЕХРАБОТЫ",
                   f"{Colors.BOLD}{admin_name}{Colors.END}",
                   f"{status_text}")
    
    def duel_result(self, winner, loser, amount, winner_power, loser_power):
        self._print(Colors.GREEN, "⚔️", "ДУЭЛЬ",
                   f"{winner} vs {loser}",
                   f"ставка: {amount}💰 | {winner_power}⚔️ vs {loser_power}⚔️")
    
    # ===== СТАТИСТИКА =====
    def status(self):
        uptime = datetime.now() - self.start_time
        total_secs = int(uptime.total_seconds())
        days = total_secs // 86400
        hours = (total_secs % 86400) // 3600
        minutes = (total_secs % 3600) // 60
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}📊 СТАТИСТИКА БОТА{Colors.END}")
        print(f"{Colors.DIM}{'='*60}{Colors.END}")
        
        time_str = f"{days}д {hours}ч {minutes}м" if days else f"{hours}ч {minutes}м"
        print(f"🕐 Время работы: {time_str}")
        print(f"👥 Игроков сегодня: {len(self.players_online)}")
        
        print(f"\n{Colors.BOLD}⚔️ БОЕВЫЕ ДЕЙСТВИЯ:{Colors.END}")
        print(f"  👾 Охот начато: {self.stats['hunts']}")
        print(f"  🏆 Побед: {self.stats['hunt_wins']}")
        print(f"  💔 Поражений: {self.stats['hunt_losses']}")
        print(f"  ⚔️ Раундов боёв: {self.stats['battles']}")
        print(f"  💥 Критов: {self.stats['crits']}")
        print(f"  🏃 Побегов: {self.stats['flees']}")
        
        print(f"\n{Colors.BOLD}💰 ЭКОНОМИКА:{Colors.END}")
        print(f"  💼 Работ: {self.stats['works']}")
        print(f"  🏪 Посещений магазина: {self.stats['shops']}")
        print(f"  🛒 Покупок: {self.stats['buys']}")
        print(f"  🔨 Крафтов: {self.stats['crafts']}")
        print(f"  🔥 Плавок: {self.stats['smelts']}")
        
        print(f"\n{Colors.BOLD}🏰 КЛАНЫ:{Colors.END}")
        print(f"  🏰 Создано кланов: {self.stats['clan_creates']}")
        print(f"  👥 Вступлений: {self.stats['clan_joins']}")
        print(f"  👋 Выходов: {self.stats['clan_leaves']}")
        print(f"  🏦 Операций с банком: {self.stats['clan_bank']}")
        
        print(f"\n{Colors.BOLD}📊 ОБЩЕЕ:{Colors.END}")
        print(f"  📋 Команд: {self.stats['commands']}")
        print(f"  🔘 Нажатий кнопок: {self.stats['buttons']}")
        print(f"  📨 Сообщений: {self.stats['messages']}")
        print(f"  ❌ Ошибок: {self.stats['errors']}")
        
        if self.players_online:
            print(f"\n{Colors.BOLD}👥 АКТИВНЫЕ ИГРОКИ:{Colors.END}")
            players_list = sorted(list(self.players_online))[:10]
            print(f"  {', '.join(players_list)}")
            if len(self.players_online) > 10:
                print(f"  ...и ещё {len(self.players_online) - 10}")
        
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")