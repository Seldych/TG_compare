import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from urllib.parse import urlparse, parse_qs
import os
import json
import concurrent.futures

from proxy_checker import check_all_socket, check_all_telethon


class TextComparer:
    """Приложение для отбора и проверки MTProto-прокси Telegram.

    Сравнивает два списка proxy-URL (File_1 — старый, File_2 — новый),
    находит новые записи, проверяет их через TCP/TLS сокет (или Telethon),
    маркирует живые (✓) и мёртвые (✗), позволяет удалять лишние
    и сохраняет только живые в итоговый файл (File_3).
    """

    def __init__(self, root):
        """Инициализация окна, установка заголовка, размера, иконки."""
        self.root = root
        self.root.title("TG Proxy — отбор прокси")
        self.root.geometry("1200x600")
        self.root.minsize(400, 300)
        try:
            self.root.iconbitmap("app.ico")
        except Exception:
            pass

        self.result_lines = []
        self.deleted_count = 0
        self.alive = {}
        self._checking = False
        self.check_method = tk.StringVar(value="socket")

        self._create_widgets()

    def _create_widgets(self):
        """Создать и разместить все элементы интерфейса: текстовую область, радиокнопки выбора метода проверки, кнопки действий, статус-бар."""
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 10), bg="#f5f5f5"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self.text_area.bind("<Control-c>", self._copy_selection)
        self.text_area.bind("<Button-3>", self._show_context_menu)
        self.text_area.bind("<Double-Button-1>", self._on_double_click)

        # Переключатель метода проверки
        method_frame = tk.Frame(self.root)
        method_frame.pack(pady=(0, 5))
        tk.Label(method_frame, text="Метод проверки:").pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(
            method_frame, text="Быстрая (TCP/TLS)",
            variable=self.check_method, value="socket"
        ).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(
            method_frame, text="Точная (Telethon)",
            variable=self.check_method, value="telethon"
        ).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        self.btn_open = tk.Button(
            btn_frame, text="Открыть", command=self._on_open,
            width=15, height=2
        )
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.btn_check = tk.Button(
            btn_frame, text="Проверить", command=self._on_check,
            width=15, height=2, state=tk.DISABLED
        )
        self.btn_check.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(
            btn_frame, text="Сохранить", command=self._on_save,
            width=15, height=2, state=tk.DISABLED
        )
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_close = tk.Button(
            btn_frame, text="Закрыть", command=self._on_close,
            width=15, height=2
        )
        self.btn_close.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Готов к работе")
        status_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=2)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_var,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            status_frame, text="written by Seldych\u2122 2026",
            anchor=tk.E
        ).pack(side=tk.RIGHT)

    def _refresh_display(self):
        """Обновить текст в окне с префиксами ✓/✗ для живых/мёртвых прокси."""
        lines = []
        for l in self.result_lines:
            if l in self.alive:
                prefix = "\u2713 " if self.alive[l] else "\u2717 "
            else:
                prefix = ""
            lines.append(prefix + l)
        text = "\n".join(lines)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)
        self.text_area.config(state=tk.DISABLED)

    def _copy_selection(self, event=None):
        """Скопировать выделенный текст в буфер обмена."""
        try:
            selected = self.text_area.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def _show_context_menu(self, event):
        """Показать контекстное меню с пунктом «Копировать»."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Копировать", command=self._copy_selection)
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def _on_double_click(self, event):
        """Двойной клик по proxy-строке — извлечь и показать параметры server/port/secret."""
        try:
            index = self.text_area.index(tk.CURRENT)
            line_start = f"{index.split('.')[0]}.0"
            line_end = f"{index.split('.')[0]}.end"
            raw = self.text_area.get(line_start, line_end)
            line = raw.lstrip("\u2713 \u2717 ")
            self._parse_and_show(line)
        except tk.TclError:
            pass

    def _parse_and_show(self, line):
        """Разобрать proxy-URL Telegram и показать popup с server/port/secret."""
        parsed = urlparse(line.strip())
        params = parse_qs(parsed.query)
        server = params.get("server", [""])[0]
        port = params.get("port", [""])[0]
        secret = params.get("secret", [""])[0]
        self._show_popup(line, server, port, secret)

    def _show_popup(self, line, server, port, secret):
        """Всплывающее окно с параметрами прокси, кнопками Copy, Удалить, Закрыть."""
        popup = tk.Toplevel(self.root)
        popup.title("Параметры строки")
        popup.geometry("520x260")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        fields = [
            ("server", server, 0),
            ("port", port, 1),
            ("secret", secret, 2),
        ]

        for label_text, value, row in fields:
            lbl = tk.Label(popup, text=label_text + ":", font=("Consolas", 10))
            lbl.grid(row=row, column=0, padx=(10, 5), pady=10, sticky="e")

            entry = tk.Entry(popup, width=50, font=("Consolas", 10))
            entry.insert(0, value)
            entry.config(state="readonly")
            entry.grid(row=row, column=1, padx=5, pady=10)

            btn = tk.Button(
                popup, text="Copy", width=6,
                command=lambda v=value: self._copy_value(v)
            )
            btn.grid(row=row, column=2, padx=(5, 10), pady=10)

        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=15)

        tk.Button(
            btn_frame, text="Удалить", width=10,
            command=lambda: self._delete_line(line, popup)
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="Закрыть", width=10,
            command=popup.destroy
        ).pack(side=tk.LEFT, padx=5)

    def _delete_line(self, line, popup):
        """Удалить прокси из списка, обновить окно и счётчик статуса."""
        self.result_lines = [l for l in self.result_lines if l != line]
        self.alive.pop(line, None)
        self.deleted_count += 1
        self._refresh_display()
        self.status_var.set(f"Строк: {len(self.result_lines)}, удалено: {self.deleted_count}")
        if not self.result_lines:
            self.btn_save.config(state=tk.DISABLED)
            self.btn_check.config(state=tk.DISABLED)
        popup.destroy()

    def _copy_value(self, text):
        """Скопировать переданный текст в буфер обмена."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _read_file_lines(self, path):
        """Прочитать строки из файла, удалить символы перевода строки."""
        with open(path, "r", encoding="utf-8-sig") as f:
            return [line.rstrip("\n\r") for line in f]

    def _load_config(self):
        """Загрузить config.json, вернуть (api_id, api_hash) или None."""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return (cfg["api_id"], cfg["api_hash"])
        except Exception:
            return None

    def _save_config(self, api_id, api_hash):
        """Сохранить api_id/api_hash в config.json."""
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash}, f)

    def _show_config_dialog(self):
        """Показать диалог ввода api_id и api_hash."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки API Telegram")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="api_id:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_id = tk.Entry(dialog, width=35)
        entry_id.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(dialog, text="api_hash:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_hash = tk.Entry(dialog, width=35)
        entry_hash.grid(row=1, column=1, padx=10, pady=10)

        result = {"ok": False}

        def _save():
            try:
                api_id = int(entry_id.get().strip())
                api_hash = entry_hash.get().strip()
                if not api_hash:
                    raise ValueError
                self._save_config(api_id, api_hash)
                result["ok"] = True
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "api_id должен быть числом, api_hash — непустой строкой.")

        tk.Button(dialog, text="Сохранить", command=_save).grid(row=2, column=0, columnspan=2, pady=15)
        self.root.wait_window(dialog)
        return result["ok"]

    def _on_check(self):
        """Запустить проверку прокси выбранным методом."""
        if self._checking or not self.result_lines:
            return

        method = self.check_method.get()

        if method == "telethon":
            config = self._load_config()
            if config is None:
                ok = self._show_config_dialog()
                if not ok:
                    return
                config = self._load_config()
                if config is None:
                    return
            api_id, api_hash = config
            check_func = check_all_telethon
            check_kwargs = {"api_id": api_id, "api_hash": api_hash}
        else:
            check_func = check_all_socket
            check_kwargs = {}

        self._checking = True
        self.btn_check.config(state=tk.DISABLED, text="Проверка...")
        self.btn_open.config(state=tk.DISABLED)
        self.status_var.set("Проверка прокси...")

        def _run():
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        check_func, self.result_lines, **check_kwargs
                    )
                    results = future.result(timeout=300)
                self.root.after(0, self._finish_check, results)
            except NotImplementedError as e:
                self.root.after(0, lambda: self._fail_check(str(e)))
            except Exception as e:
                self.root.after(0, lambda: self._fail_check(str(e)))

        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _finish_check(self, results):
        """Обработать результаты проверки."""
        for line, ok in results:
            self.alive[line] = ok

        alive_count = sum(1 for v in self.alive.values() if v)
        dead_count = sum(1 for v in self.alive.values() if not v)

        self._refresh_display()
        self.status_var.set(f"Живых: {alive_count}, мёртвых: {dead_count}")
        self._checking = False
        self.btn_check.config(state=tk.NORMAL, text="Проверить")
        self.btn_open.config(state=tk.NORMAL)

    def _fail_check(self, error):
        """Обработать ошибку проверки."""
        self.status_var.set(f"Ошибка проверки: {error}")
        self._checking = False
        self.btn_check.config(state=tk.NORMAL, text="Проверить")
        self.btn_open.config(state=tk.NORMAL)

    def _on_open(self):
        """Выбрать старый (эталон) и новый списки прокси, найти новые записи."""
        file1 = filedialog.askopenfilename(
            title="Выберите File_1 (эталонный файл)",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file1:
            return

        file2 = filedialog.askopenfilename(
            title="Выберите File_2 (файл для проверки)",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file2:
            return

        try:
            lines1 = set(self._read_file_lines(file1))
            lines2 = set(self._read_file_lines(file2))
            self.result_lines = list(lines2 - lines1)
            self.deleted_count = 0
            self.alive = {}

            if self.result_lines:
                self._refresh_display()
                self.status_var.set(
                    f"Найдено строк: {len(self.result_lines)} — "
                    f"{os.path.basename(file1)} / {os.path.basename(file2)}"
                )
                self.btn_save.config(state=tk.NORMAL)
                self.btn_check.config(state=tk.NORMAL)
            else:
                self._refresh_display()
                self.status_var.set("Новых строк не найдено")
                self.btn_save.config(state=tk.DISABLED)
                self.btn_check.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файлы:\n{e}")
            self.status_var.set("Ошибка чтения")

    def _on_save(self):
        """Сохранить только живые прокси в файл (File_3)."""
        if not self.result_lines:
            messagebox.showinfo("Информация", "Нет данных для сохранения.")
            return

        if self.alive:
            to_save = [l for l in self.result_lines if self.alive.get(l, False)]
            if not to_save:
                messagebox.showinfo("Информация", "Нет живых прокси для сохранения.")
                return
        else:
            to_save = self.result_lines

        file3 = filedialog.asksaveasfilename(
            title="Сохранить результат как File_3",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file3:
            return

        try:
            with open(file3, "w", encoding="utf-8") as f:
                for line in to_save:
                    f.write(line + "\n")
            self.status_var.set(
                f"Сохранено: {os.path.basename(file3)} "
                f"({len(to_save)} прокси)"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def _on_close(self):
        """Закрыть приложение."""
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextComparer(root)
    root.mainloop()
