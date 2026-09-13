#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный установщик зависимостей для Avalon Bot
Поддерживает: Windows, Linux, MacOS, Android (Termux), iOS (iSH)
"""

import sys
import platform
import subprocess
import os
import shutil

# ===== ЦВЕТА ДЛЯ ВЫВОДА =====
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.BLUE}📌 {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


# ===== ОПРЕДЕЛЕНИЕ СИСТЕМЫ =====

def detect_system():
    """Определяет операционную систему"""
    system = platform.system().lower()
    
    # Проверка на Termux (Android)
    if 'android' in system.lower() or os.path.exists('/data/data/com.termux'):
        return 'termux'
    
    # Проверка на iOS (iSH)
    if 'ios' in system.lower() or os.path.exists('/private/var/mobile'):
        return 'ios'
    
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'macos'
    else:
        return 'unknown'


# ===== УСТАНОВКА PYTHON (если нет) =====

def check_python():
    """Проверяет версию Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Python {version.major}.{version.minor} — слишком старая версия!")
        print_info("Требуется Python 3.7 или выше")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


# ===== УСТАНОВКА PIP =====

def install_pip():
    """Устанавливает pip если отсутствует"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                      capture_output=True, check=True)
        print_success("Pip уже установлен")
        return True
    except:
        print_warning("Pip не найден, устанавливаю...")
        try:
            subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], check=True)
            print_success("Pip установлен")
            return True
        except:
            print_error("Не удалось установить pip")
            return False


# ===== НАБОРЫ БИБЛИОТЕК =====

def get_packages():
    """Возвращает список необходимых пакетов"""
    return [
        'python-telegram-bot>=20.0',
        'aiohttp>=3.8.0',
        'aiohttp-socks>=0.7.0',
        'Pillow>=9.0.0',
        'requests>=2.28.0',
    ]


def get_optional_packages(system):
    """Возвращает опциональные пакеты в зависимости от системы"""
    optional = []
    
    if system == 'termux':
        optional = ['numpy']  # для Termux может пригодиться
    elif system == 'linux':
        optional = ['python3-venv']  # для создания виртуального окружения
    elif system == 'windows':
        optional = ['pywin32']  # для Windows-specific функций
    
    return optional


# ===== УСТАНОВКА В ЗАВИСИМОСТИ ОТ СИСТЕМЫ =====

def install_packages_linux(packages):
    """Установка на Linux"""
    print_info("Установка через pip3...")
    
    for pkg in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], 
                          check=True, capture_output=True)
            print_success(f"Установлен: {pkg.split('>=')[0]}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка при установке {pkg}: {e}")
    
    # Альтернатива через apt для системных пакетов
    try:
        subprocess.run(['sudo', 'apt', 'update'], capture_output=True)
        subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-pip', 'python3-dev'], 
                      capture_output=True)
        print_success("Системные пакеты обновлены")
    except:
        pass


def install_packages_windows(packages):
    """Установка на Windows"""
    print_info("Установка через pip...")
    
    for pkg in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], 
                          check=True, shell=True)
            print_success(f"Установлен: {pkg.split('>=')[0]}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка при установке {pkg}: {e}")


def install_packages_macos(packages):
    """Установка на MacOS"""
    print_info("Установка через pip3...")
    
    # Проверяем Homebrew
    try:
        subprocess.run(['brew', '--version'], capture_output=True, check=True)
        print_success("Homebrew найден")
    except:
        print_warning("Homebrew не найден. Установите вручную: /bin/bash -c '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'")
    
    for pkg in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], 
                          check=True, capture_output=True)
            print_success(f"Установлен: {pkg.split('>=')[0]}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка при установке {pkg}: {e}")


def install_packages_termux(packages):
    """Установка на Android (Termux)"""
    print_info("Обновление репозиториев Termux...")
    
    # Обновляем пакеты Termux
    subprocess.run(['pkg', 'update', '-y'], capture_output=True)
    subprocess.run(['pkg', 'upgrade', '-y'], capture_output=True)
    
    # Устанавливаем Python если нет
    subprocess.run(['pkg', 'install', '-y', 'python', 'python-pip'], capture_output=True)
    
    print_info("Установка Python пакетов...")
    for pkg in packages:
        try:
            subprocess.run(['pip', 'install', pkg], check=True, capture_output=True)
            print_success(f"Установлен: {pkg.split('>=')[0]}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка при установке {pkg}: {e}")


def install_packages_ios(packages):
    """Установка на iOS (iSH)"""
    print_info("Обновление репозиториев iSH...")
    
    # Обновляем apk
    subprocess.run(['apk', 'update'], capture_output=True)
    subprocess.run(['apk', 'upgrade'], capture_output=True)
    
    # Устанавливаем Python и pip
    subprocess.run(['apk', 'add', 'python3', 'py3-pip'], capture_output=True)
    
    print_info("Установка Python пакетов...")
    for pkg in packages:
        try:
            subprocess.run(['pip3', 'install', pkg], check=True, capture_output=True)
            print_success(f"Установлен: {pkg.split('>=')[0]}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка при установке {pkg}: {e}")


# ===== СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ =====

def create_venv(system):
    """Создаёт виртуальное окружение (опционально)"""
    if os.path.exists('venv'):
        print_info("Виртуальное окружение уже существует")
        return
    
    choice = input(f"\n{Colors.YELLOW}Создать виртуальное окружение? (y/n): {Colors.END}").lower()
    if choice != 'y':
        return
    
    print_info("Создаю виртуальное окружение...")
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print_success("Виртуальное окружение создано")
        
        if system == 'windows':
            print_info("Активация: venv\\Scripts\\activate")
        else:
            print_info("Активация: source venv/bin/activate")
    except Exception as e:
        print_error(f"Ошибка создания venv: {e}")


# ===== ПРОВЕРКА УСТАНОВКИ =====

def verify_installation():
    """Проверяет, что все библиотеки установлены"""
    print_header("ПРОВЕРКА УСТАНОВКИ")
    
    packages = ['telegram', 'aiohttp', 'PIL', 'requests']
    all_ok = True
    
    for pkg in packages:
        try:
            if pkg == 'telegram':
                __import__('telegram')
            elif pkg == 'aiohttp':
                __import__('aiohttp')
            elif pkg == 'PIL':
                __import__('PIL')
            elif pkg == 'requests':
                __import__('requests')
            print_success(f"{pkg} — OK")
        except ImportError:
            print_error(f"{pkg} — НЕ УСТАНОВЛЕН")
            all_ok = False
    
    return all_ok


# ===== СОЗДАНИЕ НЕОБХОДИМЫХ ПАПОК =====

def create_folders():
    """Создаёт необходимые папки"""
    print_header("СОЗДАНИЕ ПАПОК")
    
    folders = [
        'battle_logs',
        'images/locations',
        'images/enemies',
        'images/items',
        'images/destiny'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print_success(f"Создана: {folder}")


# ===== ГЛАВНАЯ ФУНКЦИЯ =====

def main():
    print_header("🛠️ AVALON BOT — УСТАНОВЩИК ЗАВИСИМОСТЕЙ")
    
    # Определяем систему
    system = detect_system()
    
    system_names = {
        'windows': 'Windows',
        'linux': 'Linux',
        'macos': 'macOS',
        'termux': 'Android (Termux)',
        'ios': 'iOS (iSH)',
        'unknown': 'Неизвестная'
    }
    
    print_info(f"Обнаружена система: {system_names.get(system, system)}")
    
    # Проверяем Python
    if not check_python():
        sys.exit(1)
    
    # Устанавливаем pip
    if not install_pip():
        sys.exit(1)
    
    # Получаем список пакетов
    packages = get_packages()
    optional = get_optional_packages(system)
    
    print_info(f"Будут установлены пакеты: {', '.join([p.split('>=')[0] for p in packages])}")
    if optional:
        print_info(f"Опционально: {', '.join(optional)}")
    
    # Устанавливаем в зависимости от системы
    if system == 'linux':
        install_packages_linux(packages)
    elif system == 'windows':
        install_packages_windows(packages)
    elif system == 'macos':
        install_packages_macos(packages)
    elif system == 'termux':
        install_packages_termux(packages)
    elif system == 'ios':
        install_packages_ios(packages)
    else:
        # Универсальный способ через pip
        print_warning("Система не распознана, использую универсальную установку...")
        for pkg in packages:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg])
    
    # Создаём папки
    create_folders()
    
    # Предлагаем создать venv
    create_venv(system)
    
    # Проверяем установку
    if verify_installation():
        print_header("✅ УСТАНОВКА ЗАВЕРШЕНА")
        print_info("Теперь:")
        print_info("  1. Вставь токен бота в config.py")
        print_info("  2. Добавь картинки в папку images/")
        print_info("  3. Запусти бота: python main.py")
        print_info("  4. Или настрой прокси: python bypass.py --update")
    else:
        print_header("❌ УСТАНОВКА НЕ ЗАВЕРШЕНА")
        print_info("Попробуй установить вручную:")
        print_info("  pip install python-telegram-bot aiohttp aiohttp-socks Pillow requests")


if __name__ == "__main__":
    main()