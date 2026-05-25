# AGENTS.md

Памятка для opencode по проекту «Сравнение файлов».

## Команды

- Запуск приложения: `python text_comparer.py`
- Создание ярлыка: `.\create_shortcut.ps1`
- Пересобрать иконку: `python generate_icon.py`

## Структура

- `text_comparer.py` — TkInter приложение, класс `TextComparer`
- `generate_icon.py` — скрипт генерации `app.ico` (BMP/ICO формат без библиотек)
- `app.ico` — иконка окна (два документа со стрелкой)
- `create_shortcut.ps1` — PowerShell-скрипт создания ярлыка на рабочем столе
- `AGENTS.md` — данный файл, инструкции для opencode

## Зависимости

Стандартная библиотека Python: `tkinter`, `os`.

## Тестирование

Логика сравнения строк не имеет внешних зависимостей и тестируется напрямую через Python.
