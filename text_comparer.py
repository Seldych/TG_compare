import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os


class TextComparer:
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнение файлов")
        self.root.geometry("800x600")
        self.root.minsize(400, 300)

        self.result_lines = []

        self._create_widgets()

    def _create_widgets(self):
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 10), bg="#f5f5f5"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_area.bind("<Control-c>", self._copy_selection)
        self.text_area.bind("<Button-3>", self._show_context_menu)

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
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _set_text(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)
        self.text_area.config(state=tk.DISABLED)

    def _copy_selection(self, event=None):
        try:
            selected = self.text_area.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Копировать", command=self._copy_selection)
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def _read_file_lines(self, path):
        with open(path, "r", encoding="utf-8-sig") as f:
            return [line.rstrip("\n\r") for line in f]

    def _on_open(self):
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
            lines2 = self._read_file_lines(file2)

            self.result_lines = [l for l in lines2 if l not in lines1]

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
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextComparer(root)
    root.mainloop()
