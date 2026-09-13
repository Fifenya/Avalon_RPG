# bypass.py - УЛЬТИМАТИВНАЯ ВЕРСИЯ
import os
import re
import asyncio
import aiohttp
import random
import time
from typing import Optional, List, Dict
from datetime import datetime
from collections import deque
from aiohttp_socks import ProxyConnector

# ===== НАСТРОЙКИ =====
MT_PROXY_FILE = "mtproxies.txt"
PROXY_CHECK_INTERVAL = 300  # Проверка каждые 5 минут
PROXY_FAILURE_THRESHOLD = 3  # После 3 ошибок прокси считается мёртвым
MAX_PROXY_AGE_HOURS = 48  # Максимальный возраст прокси (часов)

class ProxyManager:
    def __init__(self):
        self.proxies = []  # Все прокси
        self.working = []  # Работающие
        self.current = None
        self.proxy_stats = {}  # Статистика по каждому прокси
        self._lock = asyncio.Lock()
        self._update_task = None
        self.load_proxies()
    
    def load_proxies(self):
        """Загрузить прокси из файла"""
        self.proxies = []
        
        # Загружаем из mtproxies.txt
        if os.path.exists(MT_PROXY_FILE):
            with open(MT_PROXY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        converted = self._convert_to_mtproto(line)
                        if converted:
                            self.proxies.append(converted)
        
        # Добавляем рабочие из сохранённого файла
        self._load_working_proxies()
        
        print(f"📂 Загружено {len(self.proxies)} прокси")
    
    def _load_working_proxies(self):
        """Загрузить ранее работавшие прокси"""
        if os.path.exists("working_proxies.json"):
            try:
                import json
                with open("working_proxies.json", 'r') as f:
                    data = json.load(f)
                    for proxy in data.get("working", []):
                        if proxy not in self.proxies:
                            self.proxies.append(proxy)
                            self.working.append(proxy)
            except:
                pass
    
    def _convert_to_mtproto(self, url: str) -> Optional[str]:
        """Конвертирует ссылку в формат mtproto://"""
        if url.startswith('mtproto://') or url.startswith('socks5://'):
            return url
        
        if url.startswith('tg://proxy?'):
            server_match = re.search(r'server=([^&]+)', url)
            port_match = re.search(r'port=(\d+)', url)
            secret_match = re.search(r'secret=([a-f0-9]+)', url)
            if server_match and port_match and secret_match:
                return f"mtproto://{server_match.group(1)}:{port_match.group(1)}?secret={secret_match.group(1)}"
        
        return None
    
    async def test_proxy_real(self, proxy_url: str, bot_token: str) -> tuple[bool, float]:
        """Реальная проверка прокси с замером скорости"""
        start_time = time.time()
        proxy_type = None
        
        if proxy_url.startswith('socks5://'):
            proxy_type = 'socks5'
            proxy = proxy_url
        elif proxy_url.startswith('mtproto://'):
            # Для MTProto используем локальный конвертер
            local_port = self._start_local_socks5(proxy_url)
            if local_port:
                proxy = f"socks5://127.0.0.1:{local_port}"
                proxy_type = 'socks5'
            else:
                return False, 0
        else:
            return False, 0
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            
            if proxy_type == 'socks5':
                connector = ProxyConnector.from_url(proxy)
            else:
                connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            elapsed = time.time() - start_time
                            return True, elapsed
            return False, 0
        except Exception as e:
            return False, 0
        finally:
            if proxy_url.startswith('mtproto://'):
                self._stop_local_socks5()
    
    def _start_local_socks5(self, mtproto_url: str) -> Optional[int]:
        """Запускает локальный SOCKS5 прокси для MTProto"""
        import subprocess
        import socket
        import sys
        import platform
        
        parsed = self._parse_mtproto_url(mtproto_url)
        if not parsed:
            return None
        
        server, port, secret = parsed
        
        # Находим свободный порт
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        local_port = sock.getsockname()[1]
        sock.close()
        
        # Создаём конфиг
        config_content = f'''port = {local_port}
users = {{}}

proxy = {{
    server = "{server}",
    port = {port},
    secret = "{secret}"
}}

verbose = False
'''
        
        config_file = f"mtproto_config_{local_port}.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        try:
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    [sys.executable, "-m", "mtprotoproxy", config_file],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, "-m", "mtprotoproxy", config_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Сохраняем процесс для последующей остановки
            if not hasattr(self, '_mtproto_processes'):
                self._mtproto_processes = {}
            self._mtproto_processes[local_port] = (process, config_file)
            
            return local_port
        except:
            return None
    
    def _stop_local_socks5(self, port=None):
        """Останавливает локальный SOCKS5 прокси"""
        if hasattr(self, '_mtproto_processes'):
            if port and port in self._mtproto_processes:
                process, config_file = self._mtproto_processes[port]
                process.terminate()
                if os.path.exists(config_file):
                    os.remove(config_file)
                del self._mtproto_processes[port]
            elif not port:
                for p, (proc, cfg) in list(self._mtproto_processes.items()):
                    proc.terminate()
                    if os.path.exists(cfg):
                        os.remove(cfg)
                self._mtproto_processes.clear()
    
    def _parse_mtproto_url(self, url: str) -> Optional[tuple]:
        """Разобрать MTProto URL"""
        if not url.startswith('mtproto://'):
            return None
        
        url = url.replace('mtproto://', '')
        
        if '?' not in url:
            return None
        
        server_part, secret_part = url.split('?')
        secret = secret_part.replace('secret=', '')
        
        if ':' not in server_part:
            return None
        
        server, port = server_part.split(':')
        
        return (server, int(port), secret)
    
    async def update_proxies_async(self, bot_token: str):
        """Асинхронное обновление списка прокси"""
        print("🔄 Обновление списка прокси...")
        
        working = []
        
        for proxy in self.proxies:
            is_working, latency = await self.test_proxy_real(proxy, bot_token)
            if is_working:
                working.append(proxy)
                # Обновляем статистику
                if proxy not in self.proxy_stats:
                    self.proxy_stats[proxy] = {'failures': 0, 'last_success': time.time(), 'latency': latency}
                else:
                    self.proxy_stats[proxy]['last_success'] = time.time()
                    self.proxy_stats[proxy]['latency'] = latency
                    self.proxy_stats[proxy]['failures'] = 0
        
        # Обновляем список работающих
        self.working = working
        
        # Сохраняем в файл
        self._save_working_proxies()
        
        print(f"✅ Найдено {len(working)} работающих прокси")
        
        # Выбираем лучший по скорости
        if working:
            self.current = min(working, key=lambda p: self.proxy_stats.get(p, {}).get('latency', 999))
            print(f"⭐ Выбран прокси: {self.current[:60]}... (задержка: {self.proxy_stats.get(self.current, {}).get('latency', 0):.2f}с)")
    
    def _save_working_proxies(self):
        """Сохраняет работающие прокси в файл"""
        import json
        data = {
            "working": self.working,
            "last_update": datetime.now().isoformat()
        }
        with open("working_proxies.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    async def get_working_proxy(self) -> Optional[str]:
        """Возвращает работающий прокси с автоматической ротацией при проблемах"""
        async with self._lock:
            if not self.working:
                return None
            
            current = self.current
            
            # Проверяем текущий прокси
            if current:
                stats = self.proxy_stats.get(current, {})
                failures = stats.get('failures', 0)
                
                # Если прокси слишком много ошибок или устарел
                if failures >= PROXY_FAILURE_THRESHOLD:
                    print(f"⚠️ Прокси {current[:50]}... перестал работать, переключаюсь...")
                    self.working.remove(current)
                    if current in self.proxy_stats:
                        del self.proxy_stats[current]
                    
                    if self.working:
                        # Выбираем следующий по скорости
                        self.current = min(self.working, key=lambda p: self.proxy_stats.get(p, {}).get('latency', 999))
                    else:
                        self.current = None
                    self._save_working_proxies()
            
            return self.current
    
    def mark_failure(self, proxy_url: str):
        """Отмечает прокси как отказавший"""
        if proxy_url in self.proxy_stats:
            self.proxy_stats[proxy_url]['failures'] += 1
            print(f"❌ Прокси {proxy_url[:50]}... ошибка #{self.proxy_stats[proxy_url]['failures']}")
    
    def add_proxy(self, proxy_url: str) -> bool:
        """Добавить новый прокси и проверить его"""
        converted = self._convert_to_mtproto(proxy_url)
        if not converted:
            return False
        
        if converted in self.proxies:
            return False
        
        self.proxies.append(converted)
        
        # Сохраняем в файл
        with open(MT_PROXY_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{converted}")
        
        return True
    
    async def start_auto_update(self, bot_token: str):
        """Запускает автоматическое обновление прокси"""
        # Первоначальная проверка
        await self.update_proxies_async(bot_token)
        
        # Запускаем фоновую задачу
        self._update_task = asyncio.create_task(self._auto_update_loop(bot_token))
    
    async def _auto_update_loop(self, bot_token: str):
        """Фоновая задача для автоматического обновления"""
        while True:
            await asyncio.sleep(PROXY_CHECK_INTERVAL)
            await self.update_proxies_async(bot_token)


# ===== ДОБАВЛЯЕМ АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ИЗ ВНЕШНИХ ИСТОЧНИКОВ =====

async def fetch_proxies_from_github() -> List[str]:
    """Забирает свежие прокси с GitHub репозиториев"""
    proxies = []
    
    # Источники свежих MTProto прокси (обновляются каждые 12 часов)
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/main/all_proxies.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/mtproto-proxy/master/mtproto.txt",
    ]
    
    for source in sources:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source, timeout=15) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        for line in text.splitlines():
                            line = line.strip()
                            if line.startswith('tg://') or line.startswith('mtproto://'):
                                proxies.append(line)
                        print(f"📥 Загружено прокси из {source}: {len(proxies)}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки из {source}: {e}")
    
    return proxies


async def auto_fetch_proxies(proxy_manager: ProxyManager, bot_token: str):
    """Автоматически загружает и добавляет новые прокси"""
    print("🔍 Поиск свежих прокси из внешних источников...")
    
    new_proxies = await fetch_proxies_from_github()
    
    added = 0
    for proxy in new_proxies:
        if proxy_manager.add_proxy(proxy):
            added += 1
    
    if added > 0:
        print(f"✅ Добавлено {added} новых прокси")
        # Перепроверяем все прокси
        await proxy_manager.update_proxies_async(bot_token)
    else:
        print("📭 Новых прокси не найдено")