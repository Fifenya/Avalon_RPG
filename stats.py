# stats.py
from database import Player

class StatsSystem:
    """Система детальной статистики"""
    
    @staticmethod
    def update_crit(player: Player, damage: int):
        """Обновляет статистику критов"""
        player['total_crits'] = player.get('total_crits', 0) + 1
        if damage > player.get('max_crit', 0):
            player['max_crit'] = damage
        player.save()
    
    @staticmethod
    def update_damage(player: Player, damage: int, is_crit: bool = False):
        """Обновляет статистику урона"""
        if damage > player.get('max_damage', 0):
            player['max_damage'] = damage
        player.save()
    
    @staticmethod
    def update_block(player: Player, blocked: int):
        """Обновляет статистику блока"""
        player['total_blocked'] = player.get('total_blocked', 0) + blocked
        player.save()
    
    @staticmethod
    def update_dodge(player: Player):
        """Обновляет статистику уворотов"""
        player['total_dodges'] = player.get('total_dodges', 0) + 1
        player.save()
    
    @staticmethod
    def update_regen(player: Player, hp_regen: int, mana_regen: int):
        """Обновляет статистику регенерации"""
        player['total_hp_regen'] = player.get('total_hp_regen', 0) + hp_regen
        player['total_mana_regen'] = player.get('total_mana_regen', 0) + mana_regen
        player.save()
    
    @staticmethod
    def update_earnings(player: Player, earned: int):
        """Обновляет статистику заработка"""
        player['total_earned'] = player.get('total_earned', 0) + earned
        player.save()
    
    @staticmethod
    def update_spending(player: Player, spent: int):
        """Обновляет статистику трат"""
        player['total_spent'] = player.get('total_spent', 0) + spent
        player.save()
    
    @staticmethod
    def update_login_streak(player: Player):
        """Обновляет логин-стрик"""
        import time
        last_login = player.get('last_login')
        today = int(time.time() / 86400)
        
        if last_login:
            if today - last_login == 1:
                player['login_streak'] = player.get('login_streak', 0) + 1
            elif today - last_login > 1:
                player['login_streak'] = 1
        else:
            player['login_streak'] = 1
        
        player['last_login'] = today
        player.save()
        return player.get('login_streak', 0)

stats_system = StatsSystem()