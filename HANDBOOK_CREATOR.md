# 👑 AVALON 4.0 — СПРАВОЧНИК СОЗДАТЕЛЯ (Fifenya)

## Архитектура (карта файлов)
| Файл | Назначение |
|---|---|
| main.py | Точка входа: ConversationHandler создания персонажа, text_handler, регистрация хендлеров |
| config.py | Константы из .env и баланса (экономика, бой, таверна, арена, квесты) |
| database.py | Database (синглтон, avalon_data.json) + Player + default_player_data() |
| game_data.py | Расы, локации, ресурсы, рецепты, враги ENEMIES_BY_LEVEL, BOSSES, JOBS_BY_LOCATION |
| battle.py | BattleManager, режим тени (hide_*), ИИ-интеграция |
| dungeon.py | Рейды: DUNGEON_FLOORS (5 этажей, боссы) |
| smart_ai.py, enemy_memory.py, ai_phone.py | Нейросеть врагов (ai_phone требует numpy) |
| travel.py, cities_data.py | Перемещения, города рас, связность, таймеры |
| city_themes.py | Саундтреки городов (CITY_THEMES, /theme) |
| deps_manager.py | Авто-зависимости: TESTED_RANGE, SMOKE_TESTS, OPTIONAL_MODULES, BLACKLIST |
| kb_compat.py | Обход «Inline keyboard expected» при редактировании медиа |
| session_manager.py, state_manager.py | Сессии и состояния (бои/работы) |
| clan.py, shop.py, crafting.py, tavern.py, casino.py... | Игровые системы |

## Данные
- avalon_data.json: игроки + _clans. Фантомы (без расы) чистятся каждые 5 мин и на старте.
- battle_logs/ — логи боёв; reports/ — отчёты зависимостей; backups/ — бэкапы базы.
- enemy_memory.json, global_enemy_memory.json, tactics_*.json — память/тактики ИИ.

## Конфигурация
- .env: BOT_TOKEN, ADMINS, AUTO_UPDATE=1 (опц.).
- Баланс правится в config.py: START_MONEY, штрафы смерти, реген, цены эля, арена, квесты.

## Запуск и зависимости
- python3 main.py | python3 main.py --update (обновление до проверенных версий).
- Termux: тяжёлые пакеты через pkg (pkg install python-numpy); зеркало:
  export PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
- matplotlib — опционален: /ai_graph рисует ASCII-график без него.

## История фиксов (скрипты apply_*.py, бэкапы .bak_*)
1. apply_fixes.py — недостающие клавиатуры (клан/магазин/таверна/тень), роутинг кланов, /theme.
2. apply_deps_patch.py — подключение deps_manager.
3. apply_db_fix.py — баг _temp: новые игроки не сохраняли расу.
4. apply_fix3.py — шим active_crafts, kb_compat, перемещения с таймером и фактами.
5. apply_fix4.py — города рас: Дортон-хаб + 9 городов зверолюдей (связность только через Дортон).
6. make_docs.py — этот справочник.

## Как добавлять контент
- Мобы: game_data ENEMIES_BY_LEVEL / BOSSES; этажи рейда: dungeon DUNGEON_FLOORS.
- Города: cities_data CITIES / CONNECTIONS / TRAVEL_TIME_CITY (в LOCATIONS регистрируются сами).
- Темы городов: city_themes CITY_THEMES + mp3 в music/themes/ (ключ — часть названия).
- Эль: tavern ALE_TYPES; работы: game_data JOBS_BY_LOCATION.
- Рецепты: SMELTING_RECIPES / CRAFT_RECIPES / EQUIPMENT_RECIPES; товары: shop SHOP_ITEMS.
- Ранги: rank_system RANK_DATA / ITEM_RANKS / MONSTER_RANKS.
- Факты в пути: travel MOB_FACTS.

## Известные особенности
- get_main_keyboard() не знает городов → города получают клавиатуру Авалона
  (работа/магазин/крафт). Если «💼 Работа» в городах будет пустой — добавь
  ветки городов в keyboards.get_main_keyboard и JOBS_BY_LOCATION.
- Клавиатура выбора локации — reply (внизу), текущая локация скрыта.
- Редактирование медиа с reply-клавиатурой запрещено Telegram → kb_compat удаляет и шлёт заново.

## Roadmap (идеи)
- Картинки локаций: images/locations/<id>.jpg (бот подхватит сам).
- Гильдейские квесты в городах рас; караваны Дортон ↔ города; фестивали с темами.
