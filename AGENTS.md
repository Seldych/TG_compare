# AGENTS.md

Памятка для opencode по проекту «Сравнение файлов».

## Команды

- Запуск приложения: `python text_comparer.py`
- Создание ярлыка: `.\create_shortcut.ps1`

## Структура

- `text_comparer.py` — TkInter приложение, класс `TextComparer`
- `create_shortcut.ps1` — PowerShell-скрипт создания ярлыка на рабочем столе
- `AGENTS.md` — данный файл, инструкции для opencode

## Зависимости

Стандартная библиотека Python: `tkinter`, `os`.

## Тестирование

Логика сравнения строк не имеет внешних зависимостей и тестируется напрямую через Python.
