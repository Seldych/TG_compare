# AGENTS.md

Памятка для opencode по проекту «TG Proxy — отбор прокси».

## Команды

- Запуск приложения: `python text_comparer.py`
- Создание ярлыка: `.\create_shortcut.ps1`
- Пересобрать иконку: `python generate_icon.py`

## Структура

- `text_comparer.py` — TkInter приложение, класс `TextComparer`
  - Сравнение списков прокси через разность множеств
  - Двойной клик → парсинг URL → popup с server/port/secret
  - Кнопки Copy (параметр), Удалить (исключить прокси), Закрыть
  - Статусная строка: счётчик строк и удалений
  - Радиокнопки выбора метода проверки: «Быстрая (TCP/TLS)» / «Точная (Telethon)»
  - Кнопка «Проверить» — маркировка ✓ жива / ✗ мертва
  - Сохранение только живых прокси
- `proxy_checker.py` — модуль проверки прокси
  - `_decode_secret` — определяет TLS-режим по первому байту (ee → plain, dd → TLS)
  - `check_one` — проверка одного прокси через TCP/TLS сокет
  - `check_all_socket` — пул потоков (ThreadPoolExecutor, до 10 одновременных)
  - `check_all_telethon` — заглушка (реализуется при получении ключей Telegram API)
- `generate_icon.py` — скрипт генерации `app.ico` (BMP/ICO формат без библиотек)
- `app.ico` — иконка окна (два документа со стрелкой)
- `create_shortcut.ps1` — PowerShell-скрипт создания ярлыка на рабочем столе
- `AGENTS.md` — данный файл, инструкции для opencode

## Зависимости

Стандартная библиотека Python: `tkinter`, `os`, `urllib.parse`, `socket`, `ssl`, `json`, `concurrent.futures`.

## Тестирование

Логика сравнения строк не имеет внешних зависимостей и тестируется напрямую через Python.
