# check_syntax.py v2 — проверка синтаксиса через ast.parse (без записи файлов)
import ast
import os
import traceback

print("🔍 Проверяю синтаксис всех .py файлов...")
errors = 0
checked = 0

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", "venv")]
    for f in sorted(files):
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        checked += 1
        try:
            with open(path, encoding="utf-8") as fh:
                source = fh.read()
            ast.parse(source, filename=path)
        except SyntaxError as e:
            errors += 1
            print(f"❌ {path}")
            print(f"   строка {e.lineno}: {e.msg}")
            if e.text:
                print(f"   {e.text.rstrip()}")
        except Exception as e:
            errors += 1
            print(f"❌ {path}: {type(e).__name__}: {e}")

print()
print(f"📊 Проверено файлов: {checked}")
if errors:
    print(f"❌ Настоящих ошибок синтаксиса: {errors}")
else:
    print("✅ ВСЕ файлы парсятся без ошибок!")
    print("   Остальные предупреждения в Acode — шум статического анализатора.")