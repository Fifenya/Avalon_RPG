# console.py
import threading
import sys
import os
from datetime import datetime


def console_thread():
    """Поток для консольного ввода команд"""
    while True:
        try:
            cmd = input().strip().lower()
            
            if cmd == "exit" or cmd == "quit":
                print("🛑 Остановка бота...")
                os._exit(0)
            
            elif cmd == "status":
                print(f"📊 Статус бота активен | {datetime.now().strftime('%H:%M:%S')}")
                from database import Database
                data = Database.get_all()
                players = sum(1 for uid, p in data.items() if not uid.startswith('_') and isinstance(p, dict) and p.get('race'))
                print(f"👥 Игроков онлайн: {players}")
            
            elif cmd == "save":
                from database import Database
                Database.save()
                print("✅ Данные сохранены")
            
            # ===== УПРАВЛЕНИЕ ПРОКСИ (через bypass.py) =====
            elif cmd.startswith("proxy add "):
                proxy_url = cmd[10:].strip()
                if proxy_url:
                    from bypass import ProxyManager
                    pm = ProxyManager()
                    if pm.add_proxy(proxy_url, 'mtproto'):
                        print(f"✅ Прокси добавлен: {proxy_url[:60]}...")
                    else:
                        print("❌ Не удалось добавить прокси")
                else:
                    print("❌ Укажи прокси: proxy add socks5://IP:PORT")
            
            elif cmd == "proxy list":
                from bypass import ProxyManager
                pm = ProxyManager()
                print(f"\n📋 ВСЕ ПРОКСИ ({len(pm.proxies)}):")
                for i, p in enumerate(pm.proxies):
                    status = "✅" if p in pm.working else "❌"
                    print(f"  {i}. {status} {p[:70]}...")
                print()
            
            elif cmd == "proxy test":
                from bypass import ProxyManager
                pm = ProxyManager()
                pm.test_all_proxies()
            
            elif cmd == "proxy working":
                from bypass import ProxyManager
                pm = ProxyManager()
                print(f"\n⭐ РАБОТАЮЩИЕ ПРОКСИ ({len(pm.working)}):")
                for p in pm.working:
                    print(f"  ✅ {p[:70]}...")
                print()
            
            elif cmd.startswith("proxy remove "):
                try:
                    idx = int(cmd[13:].strip())
                    from bypass import ProxyManager
                    pm = ProxyManager()
                    if 0 <= idx < len(pm.proxies):
                        removed = pm.proxies.pop(idx)
                        pm._save_proxies()
                        if removed in pm.working:
                            pm.working.remove(removed)
                        print(f"✅ Удалён: {removed[:60]}...")
                    else:
                        print(f"❌ Прокси с номером {idx} не найден")
                except ValueError:
                    print("❌ Номер должен быть числом")
            
            # ===== АДМИН-КОМАНДЫ БОТА (через консоль) =====
            elif cmd == "admin broadcast":
                print("📢 Введи сообщение для рассылки (или 'cancel' для отмены):")
                msg = input("> ").strip()
                if msg.lower() != 'cancel':
                    print(f"📤 Отправляю рассылку: {msg[:50]}...")
                    print("⚠️ Рассылка через консоль требует доработки. Используй /broadcast в Telegram")
            
            elif cmd == "admin stats":
                print("📊 Запрос статистики...")
                print("💡 Используй /admin_stats в Telegram для полной статистики")
            
            elif cmd == "admin tech on":
                print("🔧 Включение техработ...")
                print("💡 Используй /tech on в Telegram")
            
            elif cmd == "admin tech off":
                print("🔧 Выключение техработ...")
                print("💡 Используй /tech off в Telegram")
            
            elif cmd == "admin restart":
                print("🔄 Перезапуск бота...")
                print("💡 Используй /restart в Telegram")
            
            elif cmd == "admin stop":
                print("🛑 Экстренная остановка бота...")
                print("💡 Используй /emergency_stop в Telegram")
            
            # ===== БЭКАПЫ =====
            elif cmd == "backup list":
                from resource_fixer import list_backups
                backups = list_backups()
                if not backups:
                    print("📭 Нет сохранённых бэкапов")
                else:
                    print(f"\n📁 БЭКАПЫ ({len(backups)}):")
                    for b in backups[:10]:
                        print(f"  📅 {b['date']} | {b['size']}KB | {b['name']}")
            
            elif cmd.startswith("backup restore "):
                backup_name = cmd[15:].strip()
                if backup_name:
                    from resource_fixer import restore_backup
                    if restore_backup(backup_name):
                        print(f"✅ Бэкап {backup_name} восстановлен")
                    else:
                        print(f"❌ Бэкап {backup_name} не найден")
                else:
                    print("❌ Укажи имя бэкапа: backup restore data_20240101_120000.json")
            
            elif cmd == "backup cleanup":
                from resource_fixer import cleanup_backups
                deleted = cleanup_backups(10)
                print(f"🗑️ Удалено старых бэкапов: {deleted}")
            
            # ===== ДИАГНОСТИКА =====
            elif cmd == "check errors":
                print("🔍 Проверка ошибок в БД...")
                print("💡 Используй /check_errors в Telegram для детального отчёта")
            
            elif cmd == "fix all":
                print("🔧 Исправление ошибок...")
                print("💡 Используй /fix_all в Telegram")
            
            # ===== ИГРОКИ =====
            elif cmd.startswith("player info "):
                player_name = cmd[12:].strip()
                if player_name:
                    from database import Database
                    data = Database.get_all()
                    found = False
                    for uid, p in data.items():
                        if isinstance(p, dict) and p.get('name', '').lower() == player_name.lower():
                            print(f"\n👤 ИГРОК: {p.get('name')}")
                            print(f"  ID: {uid}")
                            print(f"  Раса: {p.get('race', 'Нет')}")
                            print(f"  Уровень: {p.get('level', 1)}")
                            print(f"  Сила: {p.get('power', 50)}")
                            print(f"  Монет: {p.get('money', 0)}")
                            print(f"  Убийств: {p.get('kills', 0)}")
                            print(f"  Локация: {p.get('location', 'city')}")
                            found = True
                            break
                    if not found:
                        print(f"❌ Игрок {player_name} не найден")
                else:
                    print("❌ Укажи имя игрока: player info Имя")
            
            elif cmd == "players list":
                from database import Database
                data = Database.get_all()
                players = []
                for uid, p in data.items():
                    if not uid.startswith('_') and isinstance(p, dict) and p.get('race'):
                        players.append((p.get('name', 'NoName'), p.get('level', 1), p.get('money', 0)))
                players.sort(key=lambda x: x[0])
                print(f"\n👥 СПИСОК ИГРОКОВ ({len(players)}):")
                for name, level, money in players[:20]:
                    print(f"  👤 {name} | ур.{level} | 💰{money}")
                if len(players) > 20:
                    print(f"  ...и ещё {len(players) - 20} игроков")
            
            # ===== HELP =====
            elif cmd == "help" or cmd == "h" or cmd == "?":
                print("\n" + "=" * 70)
                print("📚 **СПРАВОЧНИК КОМАНД КОНСОЛИ**")
                print("=" * 70)
                
                print("\n🖥️ **ОСНОВНЫЕ КОМАНДЫ:**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ exit / quit     │ Остановить бота                               │")
                print("  │ status          │ Показать статус и кол-во игроков              │")
                print("  │ save            │ Сохранить данные вручную                      │")
                print("  │ help / h / ?    │ Показать эту справку                          │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n📡 **УПРАВЛЕНИЕ ПРОКСИ:**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ proxy add <url> │ Добавить прокси (socks5:// или mtproto://)    │")
                print("  │ proxy list      │ Показать все прокси с их статусом             │")
                print("  │ proxy test      │ Проверить все прокси реальным запросом        │")
                print("  │ proxy working   │ Показать только работающие прокси             │")
                print("  │ proxy remove N  │ Удалить прокси по номеру                      │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n💾 **БЭКАПЫ:**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ backup list     │ Показать список всех бэкапов                  │")
                print("  │ backup restore  │ Восстановить бэкап по имени                   │")
                print("  │ backup cleanup  │ Удалить старые бэкапы (оставить 10)           │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n🔧 **ДИАГНОСТИКА:**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ check errors    │ Проверить БД на ошибки                        │")
                print("  │ fix all         │ Автоматически исправить ошибки в БД           │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n👥 **УПРАВЛЕНИЕ ИГРОКАМИ:**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ player info     │ Показать информацию об игроке                 │")
                print("  │ players list    │ Показать список всех игроков                  │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n👑 **АДМИН-КОМАНДЫ (в Telegram):**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ /admin_help     │ Показать справку по админ-командам            │")
                print("  │ /admin_stats    │ Показать статистику бота                      │")
                print("  │ /tech on/off    │ Включить/выключить техработы                  │")
                print("  │ /broadcast      │ Сделать рассылку всем игрокам                 │")
                print("  │ /restart        │ Перезапустить бота                            │")
                print("  │ /emergency_stop │ Экстренная остановка бота                     │")
                print("  │ /fix_tg         │ Заполнить tg_username для всех игроков        │")
                print("  │ /cleanup_phantom│ Удалить фантомных игроков                     │")
                print("  │ /check_player   │ Проверить данные игрока                       │")
                print("  │ /check_errors   │ Проверить ошибки в БД                         │")
                print("  │ /fix_all        │ Исправить ошибки в БД                         │")
                print("  │ /list_backups   │ Показать список бэкапов                       │")
                print("  │ /restore_backup │ Восстановить бэкап                            │")
                print("  │ /cleanup_backups│ Удалить старые бэкапы                         │")
                print("  │ /chatid         │ Узнать ID чата                                │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n🎮 **ИГРОВЫЕ КОМАНДЫ (в Telegram):**")
                print("  ┌─────────────────────────────────────────────────────────────────┐")
                print("  │ /start          │ Начать игру / создать персонажа               │")
                print("  │ /destiny        │ Выбрать карту судьбы                          │")
                print("  │ /quest          │ Показать текущее задание                      │")
                print("  │ /achievements   │ Показать достижения                           │")
                print("  │ /upgrade_rank   │ Улучшить ранг предмета                        │")
                print("  │ /help           │ Показать справку                              │")
                print("  │ /rest           │ Снять усталость в таверне                     │")
                print("  │ /drink /ale     │ Заказать эль в таверне                        │")
                print("  └─────────────────────────────────────────────────────────────────┘")
                
                print("\n💡 **СОВЕТЫ:**")
                print("  • Прокси проверяются реальным запросом к Telegram API")
                print("  • Работающие прокси сохраняются в working_proxies.json")
                print("  • Для админ-команд нужно быть в списке ADMINS в config.py")
                print("  • Бэкапы создаются автоматически перед важными операциями")
                print("\n" + "=" * 70)
            
            else:
                if cmd:
                    print(f"❌ Неизвестная команда: {cmd}")
                    print(f"💡 Введите 'help' для списка всех команд")
        
        except EOFError:
            continue
        except Exception as e:
            print(f"❌ Ошибка в консольном потоке: {e}")