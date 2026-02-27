from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.exceptions import AppError
from app.services.document_service import DocumentService
from app.services.key_service import KeyService
from app.services.public_key_service import PublicKeyService


class MainWindow(ctk.CTk):
    def __init__(
        self,
        key_service: KeyService,
        public_key_service: PublicKeyService,
        document_service: DocumentService,
    ) -> None:
        super().__init__()
        self._key_service = key_service
        self._public_key_service = public_key_service
        self._document_service = document_service

        self._current_user: str | None = None
        self._current_private_key = None

        self._default_title = "Подписанный документ"
        self.title(self._default_title)
        self.geometry("980x700")
        self.minsize(840, 560)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self._create_menu()
        self._build_layout()
        self._lock_username_entry()

    def _create_menu(self) -> None:
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Создать", command=self.create_document)
        file_menu.add_command(label="Загрузить", command=self.load_document)
        file_menu.add_command(label="Сохранить", command=self.save_document)
        file_menu.add_separator()
        file_menu.add_command(label="О программе", command=self.show_about)
        file_menu.add_command(label="Выход", command=self.destroy)

        key_menu = tk.Menu(menu_bar, tearoff=0)
        key_menu.add_command(label="Экспорт открытого ключа", command=self.export_public_key)
        key_menu.add_command(label="Импорт открытого ключа", command=self.import_public_key)
        key_menu.add_command(label="Удаление пары ключей", command=self.delete_key_pair)
        key_menu.add_command(label="Выбор закрытого ключа", command=self.select_private_key)

        menu_bar.add_cascade(label="Файл", menu=file_menu)
        menu_bar.add_cascade(label="Управление ключами", menu=key_menu)

        self.config(menu=menu_bar)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        top.grid_columnconfigure(1, weight=1)

        self._username_label = ctk.CTkLabel(top, text="Имя пользователя")
        self._username_label.grid(row=0, column=0, padx=(12, 8), pady=12)

        self._username_var = tk.StringVar(value="")
        self._username_entry = ctk.CTkEntry(top, textvariable=self._username_var)
        self._username_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=12)
        self._username_entry.bind("<Return>", self._on_username_submitted)
        self._username_entry.bind("<FocusOut>", self._on_username_focus_out)

        self._select_user_button = ctk.CTkButton(top, text="Выбрать пользователя", command=self.select_private_key)
        self._select_user_button.grid(row=0, column=2, padx=(0, 8), pady=12)

        self._load_button = ctk.CTkButton(top, text="Загрузить документ", command=self.load_document)
        self._load_button.grid(row=0, column=3, padx=(0, 8), pady=12)

        self._save_button = ctk.CTkButton(top, text="Сохранить документ", command=self.save_document)
        self._save_button.grid(row=0, column=4, padx=(0, 12), pady=12)

        editor_frame = ctk.CTkFrame(self)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        self._text = ctk.CTkTextbox(editor_frame, wrap="word")
        self._text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _lock_username_entry(self) -> None:
        self._username_entry.configure(state="disabled")

    def _unlock_username_entry(self) -> None:
        self._username_entry.configure(state="normal")
        self._username_entry.focus_set()
        self._username_entry.select_range(0, tk.END)

    def _on_username_submitted(self, _: tk.Event) -> None:
        self._apply_username_selection()

    def _on_username_focus_out(self, _: tk.Event) -> None:
        if self._username_entry.cget("state") == "normal":
            self._apply_username_selection()

    def _apply_username_selection(self) -> None:
        raw_name = self._username_var.get()
        if not raw_name.strip():
            return
        try:
            username = self._key_service.validate_username(raw_name)
            self._current_private_key = self._key_service.ensure_user(username)
            self._current_user = username
            self._username_var.set(username)
            self._lock_username_entry()
            messagebox.showinfo("Пользователь", f"Выбран пользователь: {username}")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))

    def _require_user_context(self) -> tuple[str, object]:
        if self._current_user is None or self._current_private_key is None:
            raise AppError("Сначала выберите пользователя")
        return self._current_user, self._current_private_key

    def _reset_title(self) -> None:
        self.title(self._default_title)

    def create_document(self) -> None:
        self._text.delete("1.0", tk.END)
        self._reset_title()

    def save_document(self) -> None:
        try:
            username, private_key = self._require_user_context()
            target = filedialog.asksaveasfilename(
                title="Сохранить подписанный документ",
                defaultextension=".sd",
                filetypes=[("Signed Document", "*.sd"), ("All Files", "*.*")],
            )
            if not target:
                return
            text = self._text.get("1.0", tk.END).rstrip("\n")
            self._document_service.save_document(Path(target), username, private_key, text)
            messagebox.showinfo("Успешно", "Документ сохранен")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось сохранить документ: {error}")

    def load_document(self) -> None:
        try:
            _, private_key = self._require_user_context()
            source = filedialog.askopenfilename(
                title="Загрузить подписанный документ",
                filetypes=[("Signed Document", "*.sd"), ("All Files", "*.*")],
            )
            if not source:
                return
            document = self._document_service.load_document(Path(source))
            verifier_public_key = private_key.public_key()
            author_public_key = self._public_key_service.load_and_verify_public_key(document.author, verifier_public_key)
            if not self._document_service.verify_document(document, author_public_key):
                raise AppError("Подпись документа не подтверждена")
            self._text.delete("1.0", tk.END)
            self._text.insert("1.0", document.text)
            self.title(f"Подписанный документ {document.author}")
            messagebox.showinfo("Успешно", "Документ проверен и загружен")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось загрузить документ: {error}")

    def export_public_key(self) -> None:
        try:
            username, private_key = self._require_user_context()
            target = filedialog.asksaveasfilename(
                title="Экспорт открытого ключа",
                initialfile=f"{username}.pub",
                defaultextension=".pub",
                filetypes=[("Public Key", "*.pub"), ("All Files", "*.*")],
            )
            if not target:
                return
            self._public_key_service.export_public_key(username, private_key, Path(target))
            messagebox.showinfo("Успешно", "Открытый ключ экспортирован")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать ключ: {error}")

    def import_public_key(self) -> None:
        try:
            _, private_key = self._require_user_context()
            source = filedialog.askopenfilename(
                title="Импорт открытого ключа",
                filetypes=[("Public Key", "*.pub *.spub"), ("All Files", "*.*")],
            )
            if not source:
                return
            owner = self._public_key_service.import_public_key(Path(source), private_key)
            messagebox.showinfo("Успешно", f"Ключ пользователя {owner} импортирован")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось импортировать ключ: {error}")

    def delete_key_pair(self) -> None:
        try:
            username, _ = self._require_user_context()
            if not messagebox.askyesno("Подтверждение", f"Удалить пару ключей пользователя {username}?"):
                return
            self._key_service.delete_user_keys(username)
            self._current_user = None
            self._current_private_key = None
            self._username_var.set("")
            self._unlock_username_entry()
            self.create_document()
            messagebox.showinfo("Успешно", "Пара ключей удалена")
        except AppError as error:
            messagebox.showerror("Ошибка", str(error))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось удалить ключи: {error}")

    def select_private_key(self) -> None:
        self.create_document()
        self._unlock_username_entry()

    def show_about(self) -> None:
        messagebox.showinfo(
            "О программе",
            "Лабораторная работа 1\nЭлектронная подпись\nВариант 16",
        )
