# migrate_whitelist.py — перенос белого списка JSON -> sqlite/postgres
# Использование: python3 migrate_whitelist.py sqlite   (или postgres)
import sys
import whitelist
from whitelist import JsonStorage, SqliteStorage, PostgresStorage

target = sys.argv[1] if len(sys.argv) > 1 else ""
ids = JsonStorage().list_all()
if target == "sqlite":
    dst = SqliteStorage()
elif target == "postgres":
    dst = PostgresStorage()
else:
    print("Укажи цель: python3 migrate_whitelist.py sqlite|postgres")
    sys.exit(1)
for i in ids:
    dst.add(i)
print(f"✅ Перенесено {len(ids)} ID в {target}. Не забудь в .env: WHITELIST_BACKEND={target}")
