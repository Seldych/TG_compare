import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from urllib.parse import urlparse, parse_qs
import os


class TextComparer:
    """Приложение для отбора новых прокси-серверов Telegram.

    Сравнивает два списка proxy-URL (File_1 — старый, File_2 — новый),
    показывает строки из File_2, отсутствующие в File_1.
    Позволяет просматривать и удалять отдельные записи,
    сохранять итоговый актуальный список в File_3.
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

        self._create_widgets()

    def _create_widgets(self):
        """Создать и разместить все элементы интерфейса."""
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 10), bg="#f5f5f5"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_area.bind("<Control-c>", self._copy_selection)
        self.text_area.bind("<Button-3>", self._show_context_menu)
        self.text_area.bind("<Double-Button-1>", self._on_double_click)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_open = tk.Button(
            btn_frame, text="Открыть", command=self._on_open,
            width=15, height=2
        )
        self.btn_open.pack(side=tk.LEFT, padx=5)

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

    def _set_text(self, text):
        """Заполнить текстовую область новым содержимым (read-only)."""
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
            line = self.text_area.get(line_start, line_end)
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
        self.deleted_count += 1
        text = "\n".join(self.result_lines)
        self._set_text(text)
        self.status_var.set(f"Строк: {len(self.result_lines)}, удалено: {self.deleted_count}")
        if not self.result_lines:
            self.btn_save.config(state=tk.DISABLED)
        popup.destroy()

    def _copy_value(self, text):
        """Скопировать переданный текст в буфер обмена."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _read_file_lines(self, path):
        """Прочитать строки из файла, удалить символы перевода строки."""
        with open(path, "r", encoding="utf-8-sig") as f:
            return [line.rstrip("\n\r") for line in f]

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

            if self.result_lines:
                self._set_text("\n".join(self.result_lines))
                self.status_var.set(
                    f"Найдено строк: {len(self.result_lines)} — "
                    f"{os.path.basename(file1)} / {os.path.basename(file2)}"
                )
                self.btn_save.config(state=tk.NORMAL)
            else:
                self._set_text(
                    "Все строки из File_2 присутствуют в File_1.\n"
                    "Новых строк не найдено."
                )
                self.status_var.set("Новых строк не найдено")
                self.btn_save.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файлы:\n{e}")
            self.status_var.set("Ошибка чтения")

    def _on_save(self):
        """Сохранить отобранный список прокси в файл (File_3)."""
        if not self.result_lines:
            messagebox.showinfo("Информация", "Нет данных для сохранения.")
            return

        file3 = filedialog.asksaveasfilename(
            title="Сохранить результат как File_3",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file3:
            return

        try:
            with open(file3, "w", encoding="utf-8") as f:
                for line in self.result_lines:
                    f.write(line + "\n")
            self.status_var.set(
                f"Сохранено: {os.path.basename(file3)} "
                f"({len(self.result_lines)} строк)"
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
