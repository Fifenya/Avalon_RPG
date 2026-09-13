# deps_manager.py v4.0 — финальная версия для Avalon4.0
import os
import re
import sys
import ast
import subprocess
import importlib
import importlib.metadata
import time
from datetime import datetime
from pathlib import Path

# ===== КОНФИГУРАЦИЯ =====
REPORT_DIR = "reports"
REQ_FILE = "requirements.txt"
PIP_TIMEOUT = 180
RETRY_COUNT = 3
RETRY_DELAY = 15
USE_NO_CACHE = True

# Проверенные диапазоны версий
TESTED_RANGE = {
    "python-telegram-bot": ("20.0", "22.8"),
    "aiohttp":             ("3.8.0", "3.14.3"),
    "aiohttp-socks":       ("0.7.0", "0.12.0"),
    "Pillow":              ("9.0.0", "12.3.0"),
    "requests":            ("2.28.0", "2.34.2"),
    "python-dotenv":       ("1.0.0", "1.2.4"),
    "numpy":               ("1.24.0", "2.4.4"),
}

# Смоук-тесты
SMOKE_TESTS = {
    "python-telegram-bot": "from telegram.ext import Application",
    "aiohttp": "import aiohttp",
    "aiohttp-socks": "from aiohttp_socks import ProxyConnector",
    "Pillow": "from PIL import Image",
    "requests": "import requests",
    "python-dotenv": "from dotenv import load_dotenv",
    "numpy": "import numpy",
}

# Тяжёлые пакеты для Termux (ставим через pkg)
HEAVY_PACKAGES = {"numpy", "scipy", "pandas", "matplotlib", "opencv-python"}

# Чёрный список: локальные модули, которые НЕ нужно устанавливать
# (это файлы/папки внутри Avalon4.0 или соседних проектов)
BLACKLIST_MODULES = {
    # ... существующие записи ...
    "psutil",
    "psycopg2",
    "matplotlib",
    "python-dotenv",
    "shared",
    "prestige_system",
    "mtproto_converter",
    "config",
    "database",
    "logger",
    "keyboards",
    "utils",
    "game_data",
    "classes",
    "main_screen",
    "state_manager",
    "session_manager",
    "rank_system",
    "character_fixer",
    "resource_fixer",
    "console",
    "admin",
    "miniapp",
    "casino",
    "battle",
    "dungeon",
    "tavern",
    "shop",
    "crafting",
    "work",
    "gathering",
    "inventory",
    "resources",
    "equipment",
    "profile",
    "clan",
    "top",
    "quests",
    "daily_quests",
    "arena",
    "destiny",
    "achievements",
    "professions",
    "guardian",
    "smart_ai",
    "ai_phone",
    "bypass",
    "stats",
    "enemy_memory",
    "hospital",
    "race_cities",
    "race_shop",
    "city_themes",
    "deps_manager",
}

# Маппинг: имя импорта -> имя пакета в PyPI
IMPORT_TO_PACKAGE = {
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "attr": "attrs",
    "gi": "PyGObject",
}

LOG_LINES = []
ACTIONS = []

def log(msg):
    print(msg)
    LOG_LINES.append(msg)

def is_termux():
    return sys.platform == "android" or "termux" in sys.executable.lower()

def parse_ver(v):
    parts = []
    for p in re.split(r"[.\-+]", v.strip()):
        if p.isdigit():
            parts.append(int(p))
        else:
            break
    return tuple(parts or (0,))

def ver_cmp(a, b):
    a, b = parse_ver(a), parse_ver(b)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return (a > b) - (a < b)

def installed_version(dist):
    try:
        return importlib.metadata.version(dist)
    except Exception:
        pass
    
    if is_termux() and dist.lower() in HEAVY_PACKAGES:
        pkg_name = f"python-{dist.lower()}"
        try:
            r = subprocess.run(["pkg", "list-installed", pkg_name],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and pkg_name in r.stdout:
                return "0.0.0+termux"
        except Exception:
            pass
    
    return None

def pip(*args, timeout=PIP_TIMEOUT):
    extra = ["--timeout", str(timeout), "--retries", "5", "--no-input"]
    if USE_NO_CACHE:
        extra.append("--no-cache-dir")
    
    idx = os.getenv("PIP_INDEX_URL") or os.getenv("PIP_MIRROR")
    if idx:
        host = idx.split("//")[-1].split("/")[0]
        extra += ["--index-url", idx, "--trusted-host", host]
    
    cmd = [sys.executable, "-m", "pip", *extra, *args]
    log(f"💽 Выполняю: {' '.join(cmd)}")
    
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
    except subprocess.TimeoutExpired:
        return False, f"таймаут {timeout}с"
    
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if out: LOG_LINES.append(out)
    if err: LOG_LINES.append(err)
    return r.returncode == 0, out + "\n" + err

def pkg_install(*packages):
    if not is_termux():
        return False, "не Termux"
    
    cmd = ["pkg", "install", "-y", *packages]
    log(f"📦 Устанавливаю через pkg: {' '.join(cmd)}")
    
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, "таймаут pkg install"
    
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if out: LOG_LINES.append(out)
    if err: LOG_LINES.append(err)
    return r.returncode == 0, out + "\n" + err

def install_with_retry(dist, spec):
    if is_termux() and dist.lower() in HEAVY_PACKAGES:
        pkg_name = f"python-{dist.lower()}"
        log(f"📱 Termux: пробую установить {dist} через pkg...")
        ok, detail = pkg_install(pkg_name)
        if ok:
            log(f"✅ {dist} установлен через pkg")
            return True
        else:
            log(f"⚠️ pkg install не сработал, пробую pip...")
    
    for attempt in range(1, RETRY_COUNT + 1):
        log(f"📦 Попытка {attempt}/{RETRY_COUNT}: установка {spec}")
        ok, detail = pip("install", spec)
        if ok:
            log(f"✅ {dist} установлен")
            return True
        else:
            log(f"⏳ Попытка {attempt} не удалась")
            if attempt < RETRY_COUNT:
                log(f"⏸️ Пауза {RETRY_DELAY}с перед повтором...")
                time.sleep(RETRY_DELAY)
    
    return False

def scan_imports_current_dir():
    """
    Сканирует ТОЛЬКО текущую папку (не рекурсивно!).
    Возвращает set имён модулей верхнего уровня.
    """
    imports = set()
    current_dir = Path(".")
    
    for item in current_dir.iterdir():
        if item.is_file() and item.suffix == ".py":
            try:
                with open(item, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(item))
            except Exception:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        imports.add(top)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top = node.module.split(".")[0]
                        imports.add(top)
    
    return imports

def get_all_dependencies():
    """Возвращает список всех зависимостей (явные + скрытые)"""
    deps = {}
    
    # 1. Парсим requirements.txt
    if os.path.exists(REQ_FILE):
        with open(REQ_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                if not line:
                    continue
                m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(.*)$", line)
                if m:
                    dist, spec = m.group(1), m.group(2).strip()
                    deps[dist] = spec
    
    # 2. Сканируем импорты (только текущая папка!)
    log("🔍 Сканирую импорты в Avalon4.0...")
    imports = scan_imports_current_dir()
    
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()
    
    for imp in imports:
        # Пропускаем стандартные модули
        if imp in stdlib or imp.startswith("_"):
            continue
        
        # Пропускаем из чёрного списка
        if imp in BLACKLIST_MODULES:
            continue
        
        # Маппинг: import PIL -> пакет Pillow
        dist = IMPORT_TO_PACKAGE.get(imp, imp)
        
        # Пропускаем локальные модули (если файл есть в текущей папке)
        if os.path.exists(f"{imp}.py") or os.path.isdir(imp):
            continue
        
        # Если пакет ещё не добавлен, проверяем, не встроен ли модуль
        if dist not in deps:
            try:
                importlib.import_module(imp)
            except ImportError:
                deps[dist] = ""
                log(f"📌 Найдена зависимость: {imp} -> {dist}")
    
    return deps

def constraint_ok(version, constraint):
    if not constraint:
        return True
    
    for op, ver in re.findall(r"(>=|<=|==|!=|>|<|~=)\s*([0-9][A-Za-z0-9.\-]*)", constraint):
        c = ver_cmp(version, ver)
        if op == ">=" and not c >= 0: return False
        if op == "<=" and not c <= 0: return False
        if op == "==" and not c == 0: return False
        if op == "!=" and not c != 0: return False
        if op == ">"  and not c > 0:  return False
        if op == "<"  and not c < 0:  return False
        if op == "~=" and c < 0: return False
    
    return True

def auto_update_enabled():
    if "--update" in sys.argv:
        return True
    if os.path.exists(".env"):
        try:
            with open(".env", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("AUTO_UPDATE="):
                        return line.split("=", 1)[1].strip().lower() in ("1", "true", "yes", "on")
        except Exception:
            pass
    return os.getenv("AUTO_UPDATE", "").lower() in ("1", "true", "yes", "on")

def smoke_test():
    failures = {}
    for dist, code in SMOKE_TESTS.items():
        if installed_version(dist) is None:
            continue
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            failures[dist] = r.stderr.strip()
    return failures

def write_report(failures, install_failures):
    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORT_DIR, f"dep_report_{ts}.log")
    
    lines = [
        "=" * 70,
        "ОТЧЁТ О НЕСОВМЕСТИМОСТИ ЗАВИСИМОСТЕЙ",
        f"Дата: {datetime.now().isoformat()}",
        f"Python: {sys.version.split()[0]}",
        f"Платформа: {sys.platform}",
        f"Termux: {'Да' if is_termux() else 'Нет'}",
        f"PIP_INDEX_URL: {os.getenv('PIP_INDEX_URL', '(не задан)')}",
        "=" * 70,
        "",
        "--- Выполненные действия ---"
    ]
    lines.extend(ACTIONS or ["(нет)"])
    
    if install_failures:
        lines += ["", "--- Ошибки установки (сеть/PyPI) ---"]
        for dist, err in install_failures.items():
            lines += [f"### {dist} ###", err, ""]
    
    lines += ["", "--- Установленные версии ---"]
    all_deps = get_all_dependencies()
    for dist in all_deps:
        lines.append(f"{dist}: {installed_version(dist)}")
    
    if failures:
        lines += ["", "--- Ошибки проверки совместимости ---"]
        for dist, err in failures.items():
            lines += [f"### {dist} ###", err, ""]
    
    lines += [
        "",
        "--- Как исправить ---",
        "",
        "1) Если проблема в сети — задай зеркало:",
        '   export PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"',
        "",
    ]
    
    if is_termux():
        lines += [
            "2) Для тяжёлых пакетов используй pkg:",
            "   pkg install python-numpy python-scipy",
            ""
        ]
    
    lines += ["3) Установи конкретные версии:"]
    for dist in list(failures) + list(install_failures):
        lo, hi = TESTED_RANGE.get(dist, ("0", "0"))
        lines.append(f'   pip install --timeout 180 "{dist}>={lo},<={hi}"')
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    
    return path

def ensure_dependencies():
    install_failures = {}
    update = auto_update_enabled()
    
    if update:
        log("🔄 Включено автообновление зависимостей")
    
    all_deps = get_all_dependencies()
    log(f"📋 Найдено зависимостей: {len(all_deps)}")
    
    for dist, spec in all_deps.items():
        ver = installed_version(dist)
        
        if ver is None:
            install_spec = f"{dist}{spec}" if spec else dist
            log(f"📦 Пакет {dist} не найден — скачиваю...")
            if install_with_retry(dist, install_spec):
                ACTIONS.append(f"установлен: {install_spec}")
            else:
                ACTIONS.append(f"ОШИБКА УСТАНОВКИ: {install_spec}")
                install_failures[dist] = f"не удалось скачать {install_spec}"
        else:
            if spec and not constraint_ok(ver, spec):
                log(f"⚠️ {dist} {ver} не соответствует {dist}{spec} — исправляю")
                install_spec = f"{dist}{spec}"
                if install_with_retry(dist, install_spec):
                    ACTIONS.append(f"исправлен: {dist} {ver} -> {install_spec}")
                else:
                    install_failures[dist] = f"не удалось исправить: {install_spec}"
            else:
                log(f"✔️ {dist} {ver} — OK")
    
    if update:
        for dist, (lo, hi) in TESTED_RANGE.items():
            ver = installed_version(dist)
            if ver and ver != "0.0.0+termux" and ver_cmp(ver, hi) < 0:
                log(f"⬆️ Обновляю {dist}: {ver} -> {hi}")
                if install_with_retry(dist, f"{dist}=={hi}"):
                    ACTIONS.append(f"обновлён: {dist} {ver} -> {hi}")
                else:
                    install_failures[dist] = f"не удалось обновить до {hi}"
    
    importlib.invalidate_caches()
    
    for dist, (lo, hi) in TESTED_RANGE.items():
        ver = installed_version(dist)
        if ver and ver != "0.0.0+termux" and ver_cmp(ver, hi) > 0:
            msg = f"⚠️ {dist} {ver} НОВЕЕ проверенной {hi} — возможна несовместимость!"
            log(msg)
            ACTIONS.append(msg)
    
    failures = smoke_test()
    
    if failures or install_failures:
        path = write_report(failures, install_failures)
        print()
        print("❌" * 35)
        print("❌ НЕСОВМЕСТИМОСТЬ ЗАВИСИМОСТЕЙ! РАБОТА БОТА ОСТАНОВЛЕНА.")
        
        if install_failures:
            print("\n📡 Ошибки установки:")
            for dist, err in install_failures.items():
                print(f"   {dist}: {err}")
        
        if failures:
            print("\n❌ Ошибки совместимости:")
            for dist, err in failures.items():
                last = err.splitlines()[-1] if err else "ошибка импорта"
                print(f"   {dist}: {last}")
        
        print(f"\n📄 Отчёт: {path}")
        print()
        print("💡 Быстрый фикс:")
        
        if is_termux():
            heavy_missing = [d for d in install_failures if d.lower() in HEAVY_PACKAGES]
            if heavy_missing:
                pkg_names = " ".join(f"python-{d.lower()}" for d in heavy_missing)
                print(f"   pkg install {pkg_names}")
        
        if install_failures:
            missing = " ".join(install_failures)
            print(f"   pip install --timeout 180 {missing}")
        
        print("   python3 main.py")
        print("❌" * 35)
        sys.exit(1)
    
    log("✅ Все зависимости совместимы. Запускаю бота...")

if __name__ == "__main__":
    ensure_dependencies()