# core/state_manager.py
"""
Централизованное управление всеми активными состояниями бота.
Все состояния сохраняются в JSON и восстанавливаются при перезапуске.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict, field

DATA_DIR = "data"
STATE_FILE = f"{DATA_DIR}/active_states.json"
os.makedirs(DATA_DIR, exist_ok=True)


@dataclass
class BattleState:
    """Состояние боя"""
    uid: str
    enemy_name: str
    enemy_hp: int
    enemy_max_hp: int
    enemy_power: int
    enemy_armor: int
    player_hp: int
    turn: int
    defending: bool
    enemy_type: str
    dungeon_mode: bool
    hidden: bool
    hidden_turns: int
    last_update: str


@dataclass
class JobState:
    """Состояние работы"""
    uid: str
    job_name: str
    finish_time: str
    min_earn: int
    max_earn: int
    exp_reward: int
    time_seconds: int


@dataclass
class GatheringState:
    """Состояние сбора ресурсов"""
    uid: str
    finish_time: str
    location: str


@dataclass
class CraftState:
    """Состояние крафта"""
    uid: str
    item_name: str
    finish_time: str
    recipe_id: str


@dataclass
class TavernSessionState:
    """Состояние сессии в таверне"""
    uid: str
    drinks_history: list = field(default_factory=list)
    synergies_used: set = field(default_factory=set)
    achievements: set = field(default_factory=set)
    last_activity: str = ""


@dataclass
class ArenaRequestState:
    """Запрос на арену"""
    request_id: str
    uid: str
    name: str
    bet: int
    rating: int
    rank: str
    created_at: str


@dataclass
class HospitalPatientState:
    """Пациент больницы"""
    uid: str
    admit_time: str
    required_hp: int
    heal_rate: int
    last_update: str


class StateManager:
    """Единый менеджер всех состояний"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Состояния
        self.active_battles: Dict[str, BattleState] = {}
        self.active_dungeon_raids: Dict[str, dict] = {}
        self.active_jobs: Dict[str, JobState] = {}
        self.active_gathering: Dict[str, GatheringState] = {}
        self.active_crafts: Dict[str, CraftState] = {}
        self.active_sessions: Dict[str, TavernSessionState] = {}
        self.active_arena_requests: Dict[str, ArenaRequestState] = {}
        self.hospital_patients: Dict[str, HospitalPatientState] = {}
        self.arena_ratings: Dict[str, int] = {}
        
        # Ожидания ввода
        self.awaiting_equip: set = set()
        self.awaiting_unequip: set = set()
        self.awaiting_upgrade: set = set()
        
        # Таверна
        self.sleeping_players: Dict[str, datetime] = {}
        self.player_drinks_history: Dict[str, list] = {}
        self.player_synergies_used: Dict[str, set] = {}
        self.player_achievements: Dict[str, set] = {}
        
        self._load()
    
    def _load(self):
        """Загружает состояния из файла"""
        if not os.path.exists(STATE_FILE):
            return
        
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Восстанавливаем активные бои
            for uid, s in data.get('active_battles', {}).items():
                self.active_battles[uid] = BattleState(**s)
            
            # Восстанавливаем работы
            for uid, s in data.get('active_jobs', {}).items():
                self.active_jobs[uid] = JobState(**s)
            
            # Восстанавливаем сборы
            for uid, s in data.get('active_gathering', {}).items():
                self.active_gathering[uid] = GatheringState(**s)
            
            # Восстанавливаем крафты
            for uid, s in data.get('active_crafts', {}).items():
                self.active_crafts[uid] = CraftState(**s)
            
            # Восстанавливаем сессии таверны
            for uid, s in data.get('active_sessions', {}).items():
                s['synergies_used'] = set(s.get('synergies_used', []))
                s['achievements'] = set(s.get('achievements', []))
                self.active_sessions[uid] = TavernSessionState(**s)
            
            # Восстанавливаем пациентов больницы
            for uid, s in data.get('hospital_patients', {}).items():
                self.hospital_patients[uid] = HospitalPatientState(**s)
            
            # Восстанавливаем запросы арены
            for rid, s in data.get('active_arena_requests', {}).items():
                self.active_arena_requests[rid] = ArenaRequestState(**s)
            
            # Восстанавливаем рейтинги арены
            self.arena_ratings = data.get('arena_ratings', {})
            
            # Восстанавливаем подземелья
            self.active_dungeon_raids = data.get('active_dungeon_raids', {})
            
            # Восстанавливаем таверну
            self.sleeping_players = {
                uid: datetime.fromisoformat(t) for uid, t in data.get('sleeping_players', {}).items()
            }
            self.player_drinks_history = data.get('player_drinks_history', {})
            self.player_synergies_used = {
                uid: set(lst) for uid, lst in data.get('player_synergies_used', {}).items()
            }
            self.player_achievements = {
                uid: set(lst) for uid, lst in data.get('player_achievements', {}).items()
            }
            
            # Очищаем устаревшие состояния
            self._cleanup_expired()
            
            print(f"📂 Загружено состояний: боёв={len(self.active_battles)}, работ={len(self.active_jobs)}")
        
        except Exception as e:
            print(f"⚠️ Ошибка загрузки состояний: {e}")
    
    def _cleanup_expired(self):
        """Удаляет устаревшие состояния"""
        now = datetime.now()
        
        # Очищаем устаревшие бои (старше 1 часа)
        expired_battles = []
        for uid, state in self.active_battles.items():
            try:
                last_update = datetime.fromisoformat(state.last_update)
                if (now - last_update).total_seconds() > 3600:
                    expired_battles.append(uid)
            except:
                expired_battles.append(uid)
        
        for uid in expired_battles:
            del self.active_battles[uid]
        
        # Очищаем устаревшие работы
        expired_jobs = []
        for uid, state in self.active_jobs.items():
            try:
                finish_time = datetime.fromisoformat(state.finish_time)
                if finish_time < now:
                    expired_jobs.append(uid)
            except:
                expired_jobs.append(uid)
        
        for uid in expired_jobs:
            del self.active_jobs[uid]
        
        # Очищаем устаревшие сборы
        expired_gathering = []
        for uid, state in self.active_gathering.items():
            try:
                finish_time = datetime.fromisoformat(state.finish_time)
                if finish_time < now:
                    expired_gathering.append(uid)
            except:
                expired_gathering.append(uid)
        
        for uid in expired_gathering:
            del self.active_gathering[uid]
        
        # Очищаем устаревшие крафты
        expired_crafts = []
        for uid, state in self.active_crafts.items():
            try:
                finish_time = datetime.fromisoformat(state.finish_time)
                if finish_time < now:
                    expired_crafts.append(uid)
            except:
                expired_crafts.append(uid)
        
        for uid in expired_crafts:
            del self.active_crafts[uid]
        
        # Очищаем устаревшие запросы арены (старше 5 минут)
        expired_requests = []
        for rid, state in self.active_arena_requests.items():
            try:
                created_at = datetime.fromisoformat(state.created_at)
                if (now - created_at).total_seconds() > 300:
                    expired_requests.append(rid)
            except:
                expired_requests.append(rid)
        
        for rid in expired_requests:
            del self.active_arena_requests[rid]
        
        if expired_battles or expired_jobs:
            print(f"🧹 Очищено устаревших: боёв={len(expired_battles)}, "
                  f"работ={len(expired_jobs)}, запросов арены={len(expired_requests)}")
    
    def save(self):
        """Сохраняет все состояния в файл"""
        try:
            data = {
                'active_battles': {uid: asdict(s) for uid, s in self.active_battles.items()},
                'active_dungeon_raids': self.active_dungeon_raids,
                'active_jobs': {uid: asdict(s) for uid, s in self.active_jobs.items()},
                'active_gathering': {uid: asdict(s) for uid, s in self.active_gathering.items()},
                'active_crafts': {uid: asdict(s) for uid, s in self.active_crafts.items()},
                'active_sessions': {},
                'active_arena_requests': {rid: asdict(s) for rid, s in self.active_arena_requests.items()},
                'hospital_patients': {uid: asdict(s) for uid, s in self.hospital_patients.items()},
                'arena_ratings': self.arena_ratings,
                'sleeping_players': {uid: t.isoformat() for uid, t in self.sleeping_players.items()},
                'player_drinks_history': self.player_drinks_history,
                'player_synergies_used': {uid: list(s) for uid, s in self.player_synergies_used.items()},
                'player_achievements': {uid: list(s) for uid, s in self.player_achievements.items()},
                'last_save': datetime.now().isoformat()
            }
            
            # Сериализуем сессии таверны
            for uid, s in self.active_sessions.items():
                data['active_sessions'][uid] = {
                    'uid': s.uid,
                    'drinks_history': s.drinks_history,
                    'synergies_used': list(s.synergies_used),
                    'achievements': list(s.achievements),
                    'last_activity': s.last_activity
                }
            
            # Атомарная запись
            temp_file = f"{STATE_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            os.replace(temp_file, STATE_FILE)
        
        except Exception as e:
            print(f"⚠️ Ошибка сохранения состояний: {e}")
    
    def cleanup_all(self):
        """Полная очистка всех состояний"""
        self.active_battles.clear()
        self.active_dungeon_raids.clear()
        self.active_jobs.clear()
        self.active_gathering.clear()
        self.active_crafts.clear()
        self.active_sessions.clear()
        self.active_arena_requests.clear()
        self.hospital_patients.clear()
        self.arena_ratings.clear()
        self.save()
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С БОЯМИ =====
    
    def start_battle(self, uid: str, battle_data: dict) -> None:
        """Начинает бой"""
        self.active_battles[uid] = BattleState(
            uid=uid,
            enemy_name=battle_data.get('enemy_name', ''),
            enemy_hp=battle_data.get('enemy_hp', 0),
            enemy_max_hp=battle_data.get('enemy_max_hp', 0),
            enemy_power=battle_data.get('enemy_power', 0),
            enemy_armor=battle_data.get('enemy_armor', 0),
            player_hp=battle_data.get('player_hp', 0),
            turn=battle_data.get('turn', 0),
            defending=battle_data.get('defending', False),
            enemy_type=battle_data.get('enemy_type', 'humanoid'),
            dungeon_mode=battle_data.get('dungeon_mode', False),
            hidden=battle_data.get('hidden', False),
            hidden_turns=battle_data.get('hidden_turns', 0),
            last_update=datetime.now().isoformat()
        )
        self.save()
    
    def get_battle(self, uid: str) -> Optional[BattleState]:
        """Возвращает состояние боя"""
        return self.active_battles.get(uid)
    
    def end_battle(self, uid: str) -> None:
        """Завершает бой"""
        if uid in self.active_battles:
            del self.active_battles[uid]
            self.save()
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ =====
    
    def start_job(self, uid: str, job_name: str, finish_time: datetime,
                  min_earn: int, max_earn: int, exp_reward: int, time_seconds: int) -> None:
        """Начинает работу"""
        self.active_jobs[uid] = JobState(
            uid=uid,
            job_name=job_name,
            finish_time=finish_time.isoformat(),
            min_earn=min_earn,
            max_earn=max_earn,
            exp_reward=exp_reward,
            time_seconds=time_seconds
        )
        self.save()
    
    def get_job(self, uid: str) -> Optional[JobState]:
        """Возвращает состояние работы"""
        return self.active_jobs.get(uid)
    
    def end_job(self, uid: str) -> Optional[JobState]:
        """Завершает работу и возвращает её данные"""
        job = self.active_jobs.pop(uid, None)
        self.save()
        return job
    
    # ===== МЕТОДЫ ДЛЯ СБОРА РЕСУРСОВ =====
    
    def start_gathering(self, uid: str, finish_time: datetime, location: str) -> None:
        """Начинает сбор ресурсов"""
        self.active_gathering[uid] = GatheringState(
            uid=uid,
            finish_time=finish_time.isoformat(),
            location=location
        )
        self.save()
    
    def get_gathering(self, uid: str) -> Optional[GatheringState]:
        """Возвращает состояние сбора"""
        return self.active_gathering.get(uid)
    
    def end_gathering(self, uid: str) -> Optional[GatheringState]:
        """Завершает сбор ресурсов"""
        gathering = self.active_gathering.pop(uid, None)
        self.save()
        return gathering
    
    # ===== МЕТОДЫ ДЛЯ КРАФТА =====
    
    def start_craft(self, uid: str, item_name: str, finish_time: datetime, recipe_id: str) -> None:
        """Начинает крафт"""
        self.active_crafts[uid] = CraftState(
            uid=uid,
            item_name=item_name,
            finish_time=finish_time.isoformat(),
            recipe_id=recipe_id
        )
        self.save()
    
    def get_craft(self, uid: str) -> Optional[CraftState]:
        """Возвращает состояние крафта"""
        return self.active_crafts.get(uid)
    
    def end_craft(self, uid: str) -> Optional[CraftState]:
        """Завершает крафт"""
        craft = self.active_crafts.pop(uid, None)
        self.save()
        return craft
    
    # ===== МЕТОДЫ ДЛЯ ТАВЕРНЫ =====
    
    def start_tavern_session(self, uid: str) -> None:
        """Начинает сессию в таверне"""
        self.active_sessions[uid] = TavernSessionState(
            uid=uid,
            drinks_history=[],
            synergies_used=set(),
            achievements=set(),
            last_activity=datetime.now().isoformat()
        )
        self.save()
    
    def get_tavern_session(self, uid: str) -> Optional[TavernSessionState]:
        """Возвращает сессию в таверне"""
        return self.active_sessions.get(uid)
    
    def end_tavern_session(self, uid: str) -> None:
        """Завершает сессию в таверне"""
        if uid in self.active_sessions:
            del self.active_sessions[uid]
            self.save()
    
    def add_drink(self, uid: str, ale_id: str) -> None:
        """Добавляет выпитый эль в историю"""
        session = self.active_sessions.get(uid)
        if session:
            session.drinks_history.append(ale_id)
            session.last_activity = datetime.now().isoformat()
            self.save()
    
    def add_synergy(self, uid: str, synergy_name: str) -> None:
        """Добавляет использованную синергию"""
        session = self.active_sessions.get(uid)
        if session:
            session.synergies_used.add(synergy_name)
            self.save()
    
    def add_tavern_achievement(self, uid: str, achievement_id: str) -> None:
        """Добавляет достижение"""
        session = self.active_sessions.get(uid)
        if session:
            session.achievements.add(achievement_id)
            self.save()
    
    # ===== МЕТОДЫ ДЛЯ АРЕНЫ =====
    
    def get_arena_rating(self, uid: str) -> int:
        """Возвращает рейтинг арены"""
        return self.arena_ratings.get(uid, 1000)
    
    def set_arena_rating(self, uid: str, rating: int) -> None:
        """Устанавливает рейтинг арены"""
        self.arena_ratings[uid] = rating
        self.save()
    
    def add_arena_request(self, request_id: str, uid: str, name: str,
                          bet: int, rating: int, rank: str) -> None:
        """Добавляет запрос на бой"""
        self.active_arena_requests[request_id] = ArenaRequestState(
            request_id=request_id,
            uid=uid,
            name=name,
            bet=bet,
            rating=rating,
            rank=rank,
            created_at=datetime.now().isoformat()
        )
        self.save()
    
    def get_arena_request(self, request_id: str) -> Optional[ArenaRequestState]:
        """Возвращает запрос на бой"""
        return self.active_arena_requests.get(request_id)
    
    def remove_arena_request(self, request_id: str) -> None:
        """Удаляет запрос на бой"""
        if request_id in self.active_arena_requests:
            del self.active_arena_requests[request_id]
            self.save()
    
    # ===== МЕТОДЫ ДЛЯ БОЛЬНИЦЫ =====
    
    def admit_patient(self, uid: str, required_hp: int) -> None:
        """Госпитализирует игрока"""
        self.hospital_patients[uid] = HospitalPatientState(
            uid=uid,
            admit_time=datetime.now().isoformat(),
            required_hp=required_hp,
            heal_rate=1,
            last_update=datetime.now().isoformat()
        )
        self.save()
    
    def get_patient(self, uid: str) -> Optional[HospitalPatientState]:
        """Возвращает данные пациента"""
        return self.hospital_patients.get(uid)
    
    def discharge_patient(self, uid: str) -> None:
        """Выписывает пациента"""
        if uid in self.hospital_patients:
            del self.hospital_patients[uid]
            self.save()
    
    # ===== СОСТОЯНИЯ ОЖИДАНИЯ =====
    
    def set_awaiting_equip(self, uid: str) -> None:
        """Устанавливает состояние ожидания экипировки"""
        self.awaiting_equip.add(uid)
    
    def clear_awaiting_equip(self, uid: str) -> None:
        """Снимает состояние ожидания экипировки"""
        self.awaiting_equip.discard(uid)
    
    def is_awaiting_equip(self, uid: str) -> bool:
        """Проверяет состояние ожидания экипировки"""
        return uid in self.awaiting_equip
    
    def set_awaiting_unequip(self, uid: str) -> None:
        """Устанавливает состояние ожидания снятия"""
        self.awaiting_unequip.add(uid)
    
    def clear_awaiting_unequip(self, uid: str) -> None:
        """Снимает состояние ожидания снятия"""
        self.awaiting_unequip.discard(uid)
    
    def is_awaiting_unequip(self, uid: str) -> bool:
        """Проверяет состояние ожидания снятия"""
        return uid in self.awaiting_unequip


# Глобальный экземпляр
state_manager = StateManager()