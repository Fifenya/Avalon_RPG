# session_manager.py
import json
import os
from datetime import datetime
from typing import Dict, Any
import asyncio
from threading import Lock

SESSION_FILE = "sessions.json"
AUTO_SAVE_INTERVAL = 30  # Секунд

class SessionManager:
    """Менеджер сохранения сессий игроков"""
    
    _instance = None
    _lock = Lock()
    _auto_save_task = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sessions: Dict[str, Dict] = {}
        self.active_battles: Dict[str, Any] = {}
        self.active_dungeons: Dict[str, Any] = {}
        self.active_crafts: Dict[str, Any] = {}
        self.active_works: Dict[str, Any] = {}
        self.active_gatherings: Dict[str, Any] = {}
        self.active_tavern_sessions: Dict[str, Any] = {}
        self.arena_requests: Dict[str, Any] = {}
        self.hospital_patients: Dict[str, Any] = {}
        self._auto_save_enabled = False
        self.load()
    
    def start_auto_save(self, loop=None):
        """Запускает фоновое автосохранение (вызывать ПОСЛЕ запуска event loop)"""
        if self._auto_save_enabled:
            return
        self._auto_save_enabled = True
        
        async def auto_save_loop():
            while self._auto_save_enabled:
                await asyncio.sleep(AUTO_SAVE_INTERVAL)
                self.save()
        
        # Если передан loop, используем его, иначе пытаемся получить текущий
        if loop:
            self._auto_save_task = loop.create_task(auto_save_loop())
        else:
            try:
                loop = asyncio.get_running_loop()
                self._auto_save_task = loop.create_task(auto_save_loop())
            except RuntimeError:
                # Нет запущенного цикла — откладываем запуск
                print("⚠️ Автосохранение сессий запустится после старта бота")
                self._auto_save_enabled = False
    
    def stop_auto_save(self):
        """Останавливает автосохранение"""
        self._auto_save_enabled = False
        if self._auto_save_task:
            self._auto_save_task.cancel()
            self._auto_save_task = None
    
    def load(self):
        """Загружает сессии из файла"""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sessions = data.get('sessions', {})
                    # Восстанавливаем данные из сессий
                    self._restore_from_sessions()
                print(f"✅ Загружено {len(self.sessions)} сохранённых сессий")
            except Exception as e:
                print(f"❌ Ошибка загрузки сессий: {e}")
                self.sessions = {}
        else:
            self.sessions = {}
    
    def save(self):
        """Сохраняет сессии в файл"""
        with self._lock:
            try:
                # Обновляем сессии перед сохранением
                self._update_sessions_from_active()
                
                # Очищаем старые сессии (старше 1 часа без активности)
                self._cleanup_expired_sessions()
                
                data = {
                    'sessions': self.sessions,
                    'last_save': datetime.now().isoformat(),
                    'version': 2
                }
                
                # Сохраняем с поддержкой сериализации datetime
                with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            except Exception as e:
                print(f"❌ Ошибка сохранения сессий: {e}")
    
    def _cleanup_expired_sessions(self):
        """Очищает просроченные сессии"""
        from datetime import datetime, timedelta
        now = datetime.now()
        expired = []
        for uid, session in self.sessions.items():
            # Если нет активных действий (battle, dungeon, craft, work, gathering)
            has_active = any(k in session for k in ['battle', 'dungeon', 'craft', 'work', 'gathering', 'hospital', 'tavern_session'])
            if not has_active:
                if 'last_active' in session:
                    last_active = datetime.fromisoformat(session['last_active']) if isinstance(session['last_active'], str) else session['last_active']
                    if now - last_active > timedelta(hours=1):
                        expired.append(uid)
                else:
                    # Если нет отметки активности и сессия старая
                    if 'battle_history' not in session and len(session) == 0:
                        expired.append(uid)
        
        for uid in expired:
            del self.sessions[uid]
        
        if expired:
            print(f"🗑️ Очищено {len(expired)} просроченных сессий")
    
    def _update_sessions_from_active(self):
        """Обновляет данные сессий из активных объектов"""
        from battle import active_battles
        from dungeon import active_dungeon_raids
        from crafting import active_crafts
        from work import active_jobs
        from gathering import active_gathering
        from tavern import active_sessions, player_drinks_history, player_synergies_used, player_achievements, _sleeping_players
        from arena import active_arena_requests
        from hospital import hospital_patients
        
        for uid, battle in active_battles.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['battle'] = self._serialize_battle(battle)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, dungeon in active_dungeon_raids.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['dungeon'] = self._serialize_dungeon(dungeon)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, craft in active_crafts.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['craft'] = self._serialize_craft(craft)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, work in active_jobs.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['work'] = self._serialize_work(work)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, gathering in active_gathering.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['gathering'] = self._serialize_gathering(gathering)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid in active_sessions:
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['tavern_session'] = True
            if uid in player_drinks_history:
                self.sessions[uid]['drinks_history'] = player_drinks_history[uid]
            if uid in player_synergies_used:
                self.sessions[uid]['synergies_used'] = list(player_synergies_used[uid])
            if uid in player_achievements:
                self.sessions[uid]['tavern_achievements'] = list(player_achievements[uid])
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for request_id, request in active_arena_requests.items():
            uid = request.get('uid')
            if uid:
                if uid not in self.sessions:
                    self.sessions[uid] = {}
                self.sessions[uid]['arena_request'] = self._serialize_arena_request(request)
                self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, patient in hospital_patients.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['hospital'] = self._serialize_hospital(patient)
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
        
        for uid, sleep_data in _sleeping_players.items():
            if uid not in self.sessions:
                self.sessions[uid] = {}
            self.sessions[uid]['sleep_until'] = sleep_data.isoformat() if hasattr(sleep_data, 'isoformat') else sleep_data
            self.sessions[uid]['last_active'] = datetime.now().isoformat()
    
    def _restore_from_sessions(self):
        """Восстанавливает активные объекты из сессий"""
        from battle import active_battles, BattleManager
        from dungeon import active_dungeon_raids, DungeonManager
        from crafting import active_crafts
        from work import active_jobs
        from gathering import active_gathering
        from tavern import active_sessions, player_drinks_history, player_synergies_used, player_achievements, _sleeping_players
        from arena import active_arena_requests
        from hospital import hospital_patients
        from database import Player
        from datetime import datetime
        
        for uid, session in self.sessions.items():
            # Восстанавливаем бой
            if 'battle' in session and session['battle']:
                battle_data = session['battle']
                player = Player(uid)
                enemy = self._deserialize_enemy(battle_data['enemy'])
                battle = BattleManager(uid, player, enemy)
                battle.player_hp = battle_data.get('player_hp', player['hp'])
                battle.enemy_hp = battle_data.get('enemy_hp', enemy.hp)
                battle.turn = battle_data.get('turn', 0)
                battle.log = battle_data.get('log', [])
                battle.finished = False
                active_battles[uid] = battle
            
            # Восстанавливаем подземелье
            if 'dungeon' in session and session['dungeon']:
                dungeon_data = session['dungeon']
                player = Player(uid)
                dungeon = DungeonManager(uid, player)
                dungeon.progress = dungeon_data.get('progress', 0)
                dungeon.current_floor = dungeon_data.get('current_floor', 1)
                dungeon.status = dungeon_data.get('status', 'active')
                active_dungeon_raids[uid] = dungeon
            
            # Восстанавливаем крафт (только время в будущем)
            if 'craft' in session and session['craft']:
                craft_data = session['craft']
                finish_time = datetime.fromisoformat(craft_data['finish_time']) if isinstance(craft_data['finish_time'], str) else craft_data['finish_time']
                if finish_time > datetime.now():
                    active_crafts[uid] = {
                        'item_name': craft_data['item_name'],
                        'finish_time': finish_time
                    }
            
            # Восстанавливаем работу
            if 'work' in session and session['work']:
                work_data = session['work']
                finish_time = datetime.fromisoformat(work_data['finish_time']) if isinstance(work_data['finish_time'], str) else work_data['finish_time']
                if finish_time > datetime.now():
                    active_jobs[uid] = {
                        'job': work_data['job'],
                        'finish_time': finish_time
                    }
            
            # Восстанавливаем сбор ресурсов
            if 'gathering' in session and session['gathering']:
                gathering_data = session['gathering']
                finish_time = datetime.fromisoformat(gathering_data['finish_time']) if isinstance(gathering_data['finish_time'], str) else gathering_data['finish_time']
                if finish_time > datetime.now():
                    active_gathering[uid] = {
                        'finish_time': finish_time,
                        'location': gathering_data.get('location', 'forest')
                    }
            
            # Восстанавливаем сессию в таверне
            if session.get('tavern_session'):
                active_sessions[uid] = True
                if 'drinks_history' in session:
                    player_drinks_history[uid] = session['drinks_history']
                if 'synergies_used' in session:
                    player_synergies_used[uid] = set(session['synergies_used'])
                if 'tavern_achievements' in session:
                    player_achievements[uid] = set(session['tavern_achievements'])
            
            # Восстанавливаем запрос на арену
            if 'arena_request' in session and session['arena_request']:
                request_data = session['arena_request']
                request_id = f"arena_{uid}_{datetime.now().timestamp()}"
                active_arena_requests[request_id] = request_data
            
            # Восстанавливаем больницу
            if 'hospital' in session and session['hospital']:
                hospital_data = session['hospital']
                admit_time = datetime.fromisoformat(hospital_data['admit_time']) if isinstance(hospital_data['admit_time'], str) else hospital_data['admit_time']
                hospital_patients[uid] = {
                    'admit_time': admit_time,
                    'required_hp': hospital_data['required_hp'],
                    'heal_rate': hospital_data.get('heal_rate', 1),
                    'last_update': datetime.now()
                }
            
            # Восстанавливаем сон
            if 'sleep_until' in session:
                sleep_until = datetime.fromisoformat(session['sleep_until']) if isinstance(session['sleep_until'], str) else session['sleep_until']
                if sleep_until > datetime.now():
                    _sleeping_players[uid] = sleep_until
    
    def _serialize_battle(self, battle) -> Dict:
        """Сериализует объект боя"""
        return {
            'player_hp': battle.player_hp,
            'enemy_hp': battle.enemy_hp,
            'turn': battle.turn,
            'log': battle.log[-10:],
            'enemy': {
                'name': battle.enemy.name,
                'max_hp': battle.enemy.max_hp,
                'power': battle.enemy.power,
                'armor': battle.enemy.armor,
                'level': battle.enemy.level
            }
        }
    
    def _serialize_dungeon(self, dungeon) -> Dict:
        """Сериализует объект подземелья"""
        return {
            'current_floor': dungeon.current_floor,
            'progress': dungeon.progress,
            'status': dungeon.status
        }
    
    def _serialize_craft(self, craft) -> Dict:
        """Сериализует объект крафта"""
        return {
            'item_name': craft.get('item_name', 'Предмет'),
            'finish_time': craft.get('finish_time', datetime.now()).isoformat()
        }
    
    def _serialize_work(self, work) -> Dict:
        """Сериализует объект работы"""
        return {
            'job': work.get('job', {}),
            'finish_time': work.get('finish_time', datetime.now()).isoformat()
        }
    
    def _serialize_gathering(self, gathering) -> Dict:
        """Сериализует объект сбора"""
        return {
            'finish_time': gathering.get('finish_time', datetime.now()).isoformat(),
            'location': gathering.get('location', 'forest')
        }
    
    def _serialize_arena_request(self, request) -> Dict:
        """Сериализует запрос на арену"""
        return {
            'uid': request.get('uid'),
            'name': request.get('name'),
            'bet': request.get('bet', 0),
            'rating': request.get('rating', 1000),
            'rank': request.get('rank', 'Бронза'),
            'time': request.get('time', datetime.now()).isoformat() if hasattr(request.get('time'), 'isoformat') else str(request.get('time'))
        }
    
    def _serialize_hospital(self, patient) -> Dict:
        """Сериализует пациента больницы"""
        return {
            'admit_time': patient.get('admit_time', datetime.now()).isoformat(),
            'required_hp': patient.get('required_hp', 0),
            'heal_rate': patient.get('heal_rate', 1)
        }
    
    def _deserialize_enemy(self, enemy_data: Dict):
        """Восстанавливает врага из данных"""
        from game_data import Enemy
        return Enemy(
            name=enemy_data['name'],
            hp=enemy_data['max_hp'],
            power=enemy_data['power'],
            armor=enemy_data['armor'],
            reward=100,
            exp=50,
            level=enemy_data['level']
        )
    
    def remove_session(self, uid: str):
        """Удаляет сессию игрока"""
        if uid in self.sessions:
            del self.sessions[uid]
            self.save()


# Глобальный экземпляр (создаётся сразу, но автосохранение не запущено)
session_manager = SessionManager()