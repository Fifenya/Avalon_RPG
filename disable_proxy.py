# disable_proxy.py — отключение прокси в Avalon4.0
import os
import re

with open("main.py", encoding="utf-8") as f:
    src = f.read()

changed = False

# 1. Убираем .proxy_url(...) из Application.builder()
if ".proxy_url(proxy_manager.get_proxy())" in src:
    src = src.replace("\n        .proxy_url(proxy_manager.get_proxy())", "", 1)
    changed = True
    print("✅ убран .proxy_url() из Application.builder()")

# 2. Убираем логику переключения прокси из error_handler
if "proxy_manager.mark_failed" in src:
    # Находим блок обработки прокси-ошибок и вырезаем его
    src = re.sub(
        r"    # Детект падения прокси\n.*?print\(f\"🔄 Переключаю прокси\.\.\.\"\)\n",
        "",
        src,
        count=1,
        flags=re.DOTALL
    )
    changed = True
    print("✅ убрана логика переключения прокси из error_handler")

# 3. Убираем логирование прокси при старте
if "_proxy = proxy_manager.get_proxy()" in src:
    src = re.sub(
        r"    _proxy = proxy_manager\.get_proxy\(\)\n"
        r"    if _proxy:\n"
        r"        print\(f'🌐 Прокси активен: \{_proxy\}'\)\n"
        r"    else:\n"
        r"        print\('🌐 Работаем без прокси \(прямо\)'\)\n",
        "",
        src,
        count=1
    )
    changed = True
    print("✅ убрано логирование прокси при старте")

if changed:
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(src)

# 4. В .env закомментируем PROXY_URL (если есть)
if os.path.exists(".env"):
    with open(".env", encoding="utf-8") as f:
        env = f.read()
    if "PROXY_URL=" in env and not env.count("#PROXY_URL="):
        env = env.replace("PROXY_URL=", "#PROXY_URL=", 1)
        env = env.replace("PROXY_LIST=", "#PROXY_LIST=", 1)
        env = env.replace("PROXY_FALLBACK=", "#PROXY_FALLBACK=", 1)
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env)
        print("✅ закомментированы PROXY_* в .env")

print()
print("🚀 python3 main.py")
print("   Бот будет работать напрямую, без прокси")
print()
print("💡 Чтобы вернуть прокси:")
print("   1. Раскомментируй PROXY_URL в .env")
print("   2. Запусти: python3 fix_proxy.py")
print("   3. python3 main.py")