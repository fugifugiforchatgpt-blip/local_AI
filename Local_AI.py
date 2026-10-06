import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import ollama
import time
import requests
import psutil
import subprocess
import os
import re
import shutil
import json
from datetime import datetime

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def get_system_info():
    info = {"ram_gb": 0, "vram_gb": 0, "cpu_cores": os.cpu_count() or 1}
    try:
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        info["ram_gb"] = 0
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            vram_mb = int(result.stdout.strip().split("\n")[0])
            info["vram_gb"] = round(vram_mb / 1024, 1)
    except Exception:
        info["vram_gb"] = 0
    return info


MODEL_CATALOG = [
    {"id": "qwen2.5:0.5b", "name": "Qwen 2.5 0.5B", "description": "Самая маленькая Qwen. Для простых задач.", "min_ram": 2, "min_vram": 1, "size": "0.4 ГБ"},
    {"id": "qwen3:0.6b", "name": "Qwen 3 0.6B", "description": "Новое поколение Qwen. Самая маленькая версия.", "min_ram": 2, "min_vram": 1, "size": "0.5 ГБ"},
    {"id": "qwen3.5:0.8b", "name": "Qwen 3.5 0.8B", "description": "Самая лёгкая Qwen 3.5. Для быстрых ответов.", "min_ram": 2, "min_vram": 1, "size": "0.6 ГБ"},
    {"id": "gemma3:1b", "name": "Gemma 3 1B", "description": "Самая лёгкая Gemma 3. Работает на 4 ГБ ОЗУ.", "min_ram": 2, "min_vram": 1, "size": "0.8 ГБ"},
    {"id": "llama3.2:1b", "name": "Llama 3.2 1B", "description": "Компактная Llama от Meta. Быстрая.", "min_ram": 3, "min_vram": 1, "size": "1.3 ГБ"},
    {"id": "tinyllama:1.1b", "name": "TinyLlama 1.1B", "description": "Крошечная модель. Работает даже на слабых ПК.", "min_ram": 2, "min_vram": 1, "size": "0.6 ГБ"},
    {"id": "qwen2.5-coder:0.5b", "name": "Qwen 2.5 Coder 0.5B", "description": "Крошечная модель для кода.", "min_ram": 2, "min_vram": 1, "size": "0.4 ГБ"},
    {"id": "granite3-moe:1b", "name": "IBM Granite 3 MoE 1B", "description": "Лёгкая MoE-модель IBM.", "min_ram": 2, "min_vram": 1, "size": "0.7 ГБ"},
    {"id": "smollm2:1.7b", "name": "SmolLM2 1.7B", "description": "Компактная модель для диалогов.", "min_ram": 3, "min_vram": 2, "size": "1.0 ГБ"},
    {"id": "olmo2:1b", "name": "OLMo 2 1B", "description": "Модель для науки и математики.", "min_ram": 2, "min_vram": 1, "size": "0.8 ГБ"},
    {"id": "minicpm5:1b", "name": "MiniCPM5 1B", "description": "Мультиязычная крошечная модель.", "min_ram": 2, "min_vram": 1, "size": "0.7 ГБ"},
    {"id": "qwen2.5:1.5b", "name": "Qwen 2.5 1.5B", "description": "Лёгкая модель для чата. Знает русский.", "min_ram": 4, "min_vram": 2, "size": "1.0 ГБ"},
    {"id": "qwen3:1.7b", "name": "Qwen 3 1.7B", "description": "Лёгкая и быстрая модель.", "min_ram": 4, "min_vram": 2, "size": "1.1 ГБ"},
    {"id": "gemma2:2b", "name": "Gemma 2 2B", "description": "Модель от Google. Лёгкая и быстрая.", "min_ram": 4, "min_vram": 2, "size": "1.6 ГБ"},
    {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Средняя модель от Meta.", "min_ram": 6, "min_vram": 3, "size": "2.0 ГБ"},
    {"id": "phi3:mini", "name": "Phi-3 Mini (3.8B)", "description": "Компактная модель Microsoft.", "min_ram": 6, "min_vram": 4, "size": "2.5 ГБ"},
    {"id": "qwen2.5:3b", "name": "Qwen 2.5 3B", "description": "Баланс качества и скорости.", "min_ram": 6, "min_vram": 3, "size": "1.9 ГБ"},
    {"id": "qwen2.5-coder:3b", "name": "Qwen 2.5 Coder 3B", "description": "Лёгкая модель для кода.", "min_ram": 6, "min_vram": 3, "size": "1.9 ГБ"},
    {"id": "codegemma:2b", "name": "CodeGemma 2B", "description": "Модель Google для кода.", "min_ram": 4, "min_vram": 2, "size": "1.6 ГБ"},
    {"id": "starcoder:1b", "name": "StarCoder 1B", "description": "Модель для программирования.", "min_ram": 2, "min_vram": 1, "size": "1.0 ГБ"},
    {"id": "stablelm-2:1.6b", "name": "StableLM 2 1.6B", "description": "Лёгкая модель для диалогов.", "min_ram": 3, "min_vram": 2, "size": "1.0 ГБ"},
    {"id": "dolphin-phi:2.7b", "name": "Dolphin Phi 2.7B", "description": "Лёгкая модель для диалогов.", "min_ram": 5, "min_vram": 3, "size": "1.6 ГБ"},
    {"id": "qwen3:4b", "name": "Qwen 3 4B", "description": "Средняя Qwen 3.", "min_ram": 8, "min_vram": 4, "size": "2.5 ГБ"},
    {"id": "qwen3.5:4b", "name": "Qwen 3.5 4B", "description": "Средняя Qwen 3.5.", "min_ram": 8, "min_vram": 4, "size": "2.5 ГБ"},
    {"id": "gemma3:4b", "name": "Gemma 3 4B", "description": "Лёгкая Gemma 3. Видит картинки.", "min_ram": 8, "min_vram": 4, "size": "3.3 ГБ"},
    {"id": "llama3.1:8b", "name": "Llama 3.1 8B", "description": "Классическая Meta.", "min_ram": 10, "min_vram": 6, "size": "4.7 ГБ"},
    {"id": "mistral:7b", "name": "Mistral 7B", "description": "Классика для кода.", "min_ram": 10, "min_vram": 6, "size": "4.1 ГБ"},
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "description": "Мощная модель для кода.", "min_ram": 10, "min_vram": 6, "size": "4.7 ГБ"},
    {"id": "qwen2.5-coder:7b", "name": "Qwen 2.5 Coder 7B", "description": "Отличная для программирования.", "min_ram": 10, "min_vram": 6, "size": "4.7 ГБ"},
    {"id": "deepseek-r1:7b", "name": "DeepSeek-R1 7B", "description": "Мощная reasoning-модель.", "min_ram": 10, "min_vram": 6, "size": "4.7 ГБ"},
    {"id": "deepseek-r1:8b", "name": "DeepSeek-R1 8B", "description": "Улучшенная R1.", "min_ram": 12, "min_vram": 8, "size": "4.9 ГБ"},
    {"id": "zephyr:7b", "name": "Zephyr 7B", "description": "Полезные ответы.", "min_ram": 10, "min_vram": 6, "size": "4.1 ГБ"},
    {"id": "openchat:7b", "name": "OpenChat 7B", "description": "Открытые диалоги.", "min_ram": 10, "min_vram": 6, "size": "4.1 ГБ"},
    {"id": "orca-mini:7b", "name": "Orca Mini 7B", "description": "Средняя Orca.", "min_ram": 10, "min_vram": 6, "size": "3.8 ГБ"},
    {"id": "vicuna:7b", "name": "Vicuna 7B", "description": "Классика чата.", "min_ram": 10, "min_vram": 6, "size": "3.8 ГБ"},
    {"id": "starling-lm:7b", "name": "Starling LM 7B", "description": "Обучена на отзывах.", "min_ram": 10, "min_vram": 6, "size": "4.1 ГБ"},
    {"id": "codellama:7b", "name": "Code Llama 7B", "description": "Модель Meta для кода.", "min_ram": 10, "min_vram": 6, "size": "3.8 ГБ"},
    {"id": "llava:7b", "name": "LLaVA 7B", "description": "Видит картинки.", "min_ram": 10, "min_vram": 6, "size": "4.5 ГБ"},
    {"id": "granite3.3:8b", "name": "IBM Granite 3.3 8B", "description": "Модель IBM для бизнеса.", "min_ram": 10, "min_vram": 6, "size": "4.9 ГБ"},
    {"id": "moondream2:1.4b", "name": "Moondream 2 1.4B", "description": "Крошечная модель для картинок.", "min_ram": 3, "min_vram": 2, "size": "0.8 ГБ"},
    {"id": "qwen2.5:14b", "name": "Qwen 2.5 14B", "description": "Мощная Qwen 2.5.", "min_ram": 18, "min_vram": 10, "size": "9.0 ГБ"},
    {"id": "qwen3:14b", "name": "Qwen 3 14B", "description": "Очень мощная Qwen 3.", "min_ram": 20, "min_vram": 12, "size": "9.3 ГБ"},
    {"id": "gemma3:12b", "name": "Gemma 3 12B", "description": "Средняя Gemma 3.", "min_ram": 16, "min_vram": 10, "size": "8.1 ГБ"},
    {"id": "phi4:14b", "name": "Phi-4 14B", "description": "Мощная Microsoft.", "min_ram": 18, "min_vram": 10, "size": "9.1 ГБ"},
    {"id": "deepseek-r1:14b", "name": "DeepSeek-R1 14B", "description": "Серьёзная reasoning.", "min_ram": 20, "min_vram": 12, "size": "9.0 ГБ"},
    {"id": "llama3.2-vision:11b", "name": "Llama 3.2 Vision 11B", "description": "Llama для картинок.", "min_ram": 16, "min_vram": 8, "size": "7.9 ГБ"},
    {"id": "llava:13b", "name": "LLaVA 13B", "description": "Мощная мультимодальная.", "min_ram": 18, "min_vram": 10, "size": "8.0 ГБ"},
    {"id": "qwen2.5:14b-instruct", "name": "Qwen 2.5 14B Instruct", "description": "Инструктивная 14B.", "min_ram": 18, "min_vram": 10, "size": "9.0 ГБ"},
    {"id": "nomic-embed-text", "name": "Nomic Embed Text", "description": "Эмбеддинги для поиска.", "min_ram": 2, "min_vram": 1, "size": "0.3 ГБ"},
]


def check_compatibility(model, sys_info):
    ram_ok = sys_info["ram_gb"] >= model["min_ram"]
    vram_ok = sys_info["vram_gb"] >= model["min_vram"]
    if ram_ok and vram_ok:
        if sys_info["ram_gb"] >= model["min_ram"] * 1.5 and sys_info["vram_gb"] >= model["min_vram"] * 1.5:
            return "🟢 Хорошо", "#4CAF50"
        else:
            return "🟡 Средне", "#FF9800"
    else:
        return "🔴 Плохо", "#F44336"


# ==================== ОКНО ГЕНЕРАЦИИ КАРТИНОК ====================

class ImageGeneratorWindow:
    """Отдельное окно для генерации картинок через Z-Image."""

    def __init__(self, parent, app):
        self.app = app
        self.parent = parent

        self.win = tk.Toplevel(parent)
        self.win.title("🎨 Генератор картинок (Z-Image)")
        self.win.geometry("600x650")
        self.win.configure(bg="#1e1e1e")

        self._outputs_dir = os.path.join(app._zimage_dir, "outputs")
        self._last_files = set()
        self._generation_start = 0
        self._monitoring = False
        self._current_prompt_en = ""

        self._build_ui()
        self._refresh_state()

    def _build_ui(self):
        # Заголовок
        tk.Label(
            self.win, text="🎨 Генератор картинок",
            font=("Arial", 16, "bold"),
            bg="#1e1e1e", fg="#9C27B0"
        ).pack(pady=(15, 5))

        # Статус Z-Image
        self.status_frame = tk.Frame(self.win, bg="#2d2d2d")
        self.status_frame.pack(fill=tk.X, padx=15, pady=5)

        self.status_label = tk.Label(
            self.status_frame, text="Проверка...",
            font=("Arial", 11, "bold"),
            bg="#2d2d2d", fg="#888888"
        )
        self.status_label.pack(pady=10, padx=10, anchor="w")

        # Блок команд (если Z-Image не запущен)
        self.cmd_frame = tk.Frame(self.win, bg="#2d2d2d")
        self.cmd_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(
            self.cmd_frame, text="📋 Команды для запуска Z-Image:",
            font=("Arial", 11, "bold"),
            bg="#2d2d2d", fg="#8fdc8f"
        ).pack(anchor="w", padx=10, pady=(10, 5))

        cmd_text = tk.Text(
            self.cmd_frame, height=3, wrap=tk.WORD,
            bg="#1e1e1e", fg="#00ff00",
            font=("Consolas", 10), relief=tk.FLAT,
            padx=10, pady=8
        )
        cmd_text.pack(fill=tk.X, padx=10, pady=(0, 5))
        cmd_text.insert("1.0", f"cd /d {self.app._zimage_dir}\nstart_zimage.bat")
        cmd_text.config(state="disabled")

        tk.Button(
            self.cmd_frame, text="📋 Скопировать команды",
            command=self._copy_commands,
            bg="#555", fg="white", font=("Arial", 10),
            relief=tk.FLAT, padx=10, pady=5
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Блок генерации (если Z-Image запущен)
        self.gen_frame = tk.Frame(self.win, bg="#2d2d2d")
        self.gen_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(
            self.gen_frame, text="📝 Промт (по-русски):",
            font=("Arial", 11, "bold"),
            bg="#2d2d2d", fg="#8fdc8f"
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.prompt_entry = tk.Entry(
            self.gen_frame, font=("Consolas", 12),
            bg="#1e1e1e", fg="white",
            insertbackground="white", relief=tk.FLAT
        )
        self.prompt_entry.pack(fill=tk.X, padx=10, pady=(0, 8), ipady=8)
        self.prompt_entry.bind("<Return>", lambda e: self._on_generate())

        tk.Button(
            self.gen_frame, text="🌐 Перевести и получить промт",
            command=self._on_generate,
            bg="#9C27B0", fg="white", font=("Arial", 11, "bold"),
            relief=tk.FLAT, padx=15, pady=8
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Английский промт
        tk.Label(
            self.gen_frame, text="🇬🇧 Промт (EN) — вставь в браузер Z-Image:",
            font=("Arial", 11, "bold"),
            bg="#2d2d2d", fg="#8fdc8f"
        ).pack(anchor="w", padx=10, pady=(5, 5))

        self.prompt_en_text = tk.Text(
            self.gen_frame, height=3, wrap=tk.WORD,
            bg="#1e1e1e", fg="#00ddff",
            font=("Consolas", 10), relief=tk.FLAT,
            padx=10, pady=8
        )
        self.prompt_en_text.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.prompt_en_text.config(state="disabled")

        tk.Button(
            self.gen_frame, text="📋 Скопировать промт (EN)",
            command=self._copy_prompt_en,
            bg="#2196F3", fg="white", font=("Arial", 10),
            relief=tk.FLAT, padx=10, pady=5
        ).pack(anchor="w", padx=10, pady=(0, 5))

        tk.Button(
            self.gen_frame, text="🌐 Открыть Z-Image в браузере",
            command=self._open_zimage_browser,
            bg="#555", fg="white", font=("Arial", 10),
            relief=tk.FLAT, padx=10, pady=5
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Прогресс
        self.progress_label = tk.Label(
            self.win, text="",
            font=("Arial", 11, "bold"),
            bg="#1e1e1e", fg="#FFA500"
        )
        self.progress_label.pack(pady=10)

        # Кнопка "Я нажал Generate"
        self.start_monitor_btn = tk.Button(
            self.win, text="▶ Я нажал Generate в браузере",
            command=self._start_monitoring,
            bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
            relief=tk.FLAT, padx=20, pady=10
        )
        self.start_monitor_btn.pack(pady=5)

        # Показ картинки
        self.image_label = tk.Label(self.win, bg="#1e1e1e")
        self.image_label.pack(pady=5)

        self._refresh_state_loop()

    # ---------- обновление состояния Z-Image ----------
    def _refresh_state(self):
        if self.app._zimage_ready:
            self.status_label.config(text="✅ Z-Image работает!", fg="#4CAF50")
            self.cmd_frame.pack_forget()
            self.gen_frame.pack(fill=tk.X, padx=15, pady=5)
        else:
            self.status_label.config(text="⏸ Z-Image не запущен", fg="#FF9800")
            self.gen_frame.pack_forget()
            self.cmd_frame.pack(fill=tk.X, padx=15, pady=5)

    def _refresh_state_loop(self):
        try:
            self._refresh_state()
        except Exception:
            pass
        try:
            self.win.after(2000, self._refresh_state_loop)
        except Exception:
            pass

    # ---------- действия ----------
    def _copy_commands(self):
        text = f"cd /d {self.app._zimage_dir}\nstart_zimage.bat"
        self.win.clipboard_clear()
        self.win.clipboard_append(text)
        messagebox.showinfo("Скопировано", "Команды скопированы в буфер обмена.\n\nВставь их в консоль (Win+R → cmd) и нажми Enter.")

    def _copy_prompt_en(self):
        if not self._current_prompt_en:
            messagebox.showinfo("Пусто", "Сначала переведи промт.")
            return
        self.win.clipboard_clear()
        self.win.clipboard_append(self._current_prompt_en)
        messagebox.showinfo("Скопировано", "Промт (EN) скопирован.\n\nВставь его в поле Prompt на странице Z-Image.")

    def _open_zimage_browser(self):
        import webbrowser
        webbrowser.open(self.app._zimage_url)

    def _on_generate(self):
        prompt_ru = self.prompt_entry.get().strip()
        if not prompt_ru:
            messagebox.showinfo("Промт", "Введи промт по-русски.")
            return

        self.prompt_en_text.config(state="normal")
        self.prompt_en_text.delete("1.0", tk.END)
        self.prompt_en_text.insert("1.0", "⏳ Перевожу...")
        self.prompt_en_text.config(state="disabled")

        threading.Thread(target=self._translate_and_show, args=(prompt_ru,), daemon=True).start()

    def _translate_and_show(self, prompt_ru):
        try:
            prompt_en = self.app._translate_prompt(prompt_ru)
        except Exception:
            prompt_en = prompt_ru + ", masterpiece, best quality, detailed"

        self._current_prompt_en = prompt_en

        self.win.after(0, lambda: self._show_translation(prompt_en))

    def _show_translation(self, prompt_en):
        self.prompt_en_text.config(state="normal")
        self.prompt_en_text.delete("1.0", tk.END)
        self.prompt_en_text.insert("1.0", prompt_en)
        self.prompt_en_text.config(state="disabled")

        # Автоматически копируем в буфер
        self.win.clipboard_clear()
        self.win.clipboard_append(prompt_en)

        # Автоматически открываем браузер
        import webbrowser
        webbrowser.open(self.app._zimage_url)

        self.progress_label.config(
            text="✅ Промт переведён и скопирован!\n"
                 "Вставь его в браузере (Ctrl+V) и нажми Generate.\n"
                 "Потом нажми кнопку ниже.",
            fg="#4CAF50"
        )

    def _start_monitoring(self):
        if self._monitoring:
            messagebox.showinfo("Уже идёт", "Мониторинг уже запущен.")
            return
        if not self._current_prompt_en:
            messagebox.showinfo("Промт", "Сначала переведи промт.")
            return

        self._monitoring = True
        self._generation_start = time.time()
        self._last_files = set(os.listdir(self._outputs_dir)) if os.path.exists(self._outputs_dir) else set()

        self.start_monitor_btn.config(state=tk.DISABLED, text="⏳ Жду картинку...")
        threading.Thread(target=self._monitor_outputs, daemon=True).start()

    def _monitor_outputs(self):
        timeout = 600  # 10 минут
        while self._monitoring:
            elapsed = int(time.time() - self._generation_start)

            if elapsed > timeout:
                self.win.after(0, lambda: self.progress_label.config(
                    text=f"⚠️ Прошло {timeout} секунд — картинка не появилась.",
                    fg="#F44336"))
                self.win.after(0, lambda: self.start_monitor_btn.config(
                    state=tk.NORMAL, text="▶ Я нажал Generate в браузере"))
                self._monitoring = False
                return

            # Обновляем прогресс
            self.win.after(0, lambda e=elapsed: self.progress_label.config(
                text=f"⏳ Жду картинку... {e} сек", fg="#FFA500"))

            # Проверяем новые файлы
            if os.path.exists(self._outputs_dir):
                current_files = set(os.listdir(self._outputs_dir))
                new_files = current_files - self._last_files
                for f in new_files:
                    if f.endswith(".png"):
                        path = os.path.join(self._outputs_dir, f)
                        self._monitoring = False
                        self.win.after(0, lambda p=path: self._on_image_ready(p))
                        return

            time.sleep(2)

    def _on_image_ready(self, image_path):
        self.progress_label.config(
            text=f"✅ Картинка готова за {int(time.time() - self._generation_start)} сек!",
            fg="#4CAF50")
        self.start_monitor_btn.config(state=tk.NORMAL, text="▶ Сгенерировать ещё")

        # Показываем в окне
        if HAS_PIL:
            try:
                img = Image.open(image_path)
                img.thumbnail((500, 500))
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.image_label.image = photo
            except Exception as e:
                print(f"[IMG] {e}")

        # Добавляем сообщение в основной чат
        self.app.add_message("Система", f"🎨 Картинка готова: {os.path.basename(image_path)}", tag="image")

        # Открываем папку (опционально)
        # os.startfile(self.app._generated_dir)


# ==================== ГЛАВНОЕ ПРИЛОЖЕНИЕ ====================

class LocalChatApp:
    def __init__(self, root):
        self.root = root
        root.title("Локальный чат — Qwen / DeepSeek")
        root.geometry("1100x720")
        root.configure(bg="#1e1e1e")

        self.sys_info = get_system_info()

        self.base_models = {
            "Qwen 3.5 2B": "qwen3.5:2b",
            "DeepSeek-R1 1.5B": "hf.co/mradermacher/DeepSeek-R1-Distill-Qwen-1.5B-Multilingual-i1-GGUF:Q4_K_M",
        }
        self.model_map = dict(self.base_models)
        self.available_models = list(self.model_map.keys())

        self.temperature_var = tk.DoubleVar(value=0.8)
        self.num_ctx_var = tk.IntVar(value=4096)
        self.top_k_var = tk.IntVar(value=40)
        self.top_p_var = tk.DoubleVar(value=0.9)
        self.current_model = tk.StringVar(value=self.available_models[0])

        self.think_var = tk.BooleanVar(value=False)
        self.stop_flag = False
        self.is_dark = True
        self._ctx_after_id = None
        self._thinking_started = False
        self._answer_started = False
        self.is_generating = False
        self._pull_progress = None

        self.sidebar_visible = True

        self.colors = {
            "dark": {"bg": "#1e1e1e", "panel": "#2d2d2d", "sidebar": "#252525",
                     "sidebar_item": "#333333", "sidebar_item_active": "#3a3a3a",
                     "input": "#3c3c3c", "fg": "#ffffff", "meta": "#888888",
                     "thinking": "#888888", "btn_send": "#4CAF50", "btn_stop": "#D32F2F",
                     "btn_neutral": "#555555", "btn_clear": "#666666", "btn_shop": "#2196F3",
                     "btn_image": "#9C27B0"},
            "light": {"bg": "#f0f0f0", "panel": "#e0e0e0", "sidebar": "#d8d8d8",
                      "sidebar_item": "#cccccc", "sidebar_item_active": "#c0c0c0",
                      "input": "#ffffff", "fg": "#000000", "meta": "#666666",
                      "thinking": "#888888", "btn_send": "#4CAF50", "btn_stop": "#D32F2F",
                      "btn_neutral": "#888888", "btn_clear": "#999999", "btn_shop": "#1976D2",
                      "btn_image": "#7B1FA2"}
        }

        # ==================== ВЕРХНЯЯ ПАНЕЛЬ ====================
        self.top_frame = tk.Frame(root, bg=self.colors["dark"]["panel"], pady=8)
        self.top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.toggle_sidebar_btn = tk.Button(
            self.top_frame, text="◀ Чаты", command=self.toggle_sidebar,
            bg=self.colors["dark"]["btn_neutral"], fg="white",
            font=("Arial", 10, "bold"), relief=tk.FLAT, padx=10
        )
        self.toggle_sidebar_btn.pack(side=tk.LEFT, padx=(10, 5))

        tk.Label(self.top_frame, text="🤖 Модель:", bg=self.colors["dark"]["panel"],
                 fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5, 2))
        self.model_combo = ttk.Combobox(self.top_frame, textvariable=self.current_model,
                                        values=self.available_models, state="readonly",
                                        width=22, font=("Consolas", 10))
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        self.refresh_btn = tk.Button(
            self.top_frame, text="🔄", command=self.manual_refresh_models,
            bg=self.colors["dark"]["btn_neutral"], fg="white",
            font=("Arial", 11, "bold"), relief=tk.FLAT, padx=8
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.think_check = tk.Checkbutton(self.top_frame, text="🧠 Мышление", variable=self.think_var,
                                          bg=self.colors["dark"]["panel"], fg="white",
                                          selectcolor=self.colors["dark"]["panel"],
                                          activebackground=self.colors["dark"]["panel"],
                                          activeforeground="white",
                                          font=("Arial", 10, "bold"), command=self.on_think_toggle)
        self.think_check.pack(side=tk.LEFT, padx=10)

        self.think_status = tk.Label(self.top_frame, text="Выкл",
                                     bg=self.colors["dark"]["panel"], fg="#888888", font=("Arial", 9))
        self.think_status.pack(side=tk.LEFT, padx=2)

        self.token_counter = tk.Label(self.top_frame, text="📊 0 / 4096",
                                      bg=self.colors["dark"]["panel"], fg="#00BCD4", font=("Arial", 10, "bold"))
        self.token_counter.pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(self.top_frame, text="Готова",
                                     bg=self.colors["dark"]["panel"], fg="#4CAF50", font=("Arial", 10, "italic"))
        self.status_label.pack(side=tk.RIGHT, padx=15)

        self.shop_btn = tk.Button(self.top_frame, text="🏪 Магазин", command=self.open_shop,
                                  bg=self.colors["dark"]["btn_shop"], fg="white", font=("Arial", 10, "bold"),
                                  relief=tk.FLAT, padx=10)
        self.shop_btn.pack(side=tk.RIGHT, padx=5)

        self.clear_ram_btn = tk.Button(self.top_frame, text="🧹 Очистить ОЗУ", command=self.clear_ram,
                                       bg=self.colors["dark"]["btn_neutral"], fg="white", font=("Arial", 10),
                                       relief=tk.FLAT, padx=10)
        self.clear_ram_btn.pack(side=tk.RIGHT, padx=5)

        self.open_folder_btn = tk.Button(
            self.top_frame, text="📁 Картинки",
            command=self.open_generated_folder,
            bg=self.colors["dark"]["btn_neutral"], fg="white",
            font=("Arial", 10), relief=tk.FLAT, padx=10
        )
        self.open_folder_btn.pack(side=tk.RIGHT, padx=5)

        self.theme_btn = tk.Button(self.top_frame, text="☀️ Светлая", command=self.toggle_theme,
                                   bg=self.colors["dark"]["btn_neutral"], fg="white", font=("Arial", 10),
                                   relief=tk.FLAT, padx=10)
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        self.settings_btn = tk.Button(self.top_frame, text="⚙️ Настройки", command=self.open_settings,
                                      bg=self.colors["dark"]["btn_neutral"], fg="white", font=("Arial", 10),
                                      relief=tk.FLAT, padx=10)
        self.settings_btn.pack(side=tk.RIGHT, padx=5)

        self.clear_btn = tk.Button(self.top_frame, text="Очистить чат", command=self.clear_chat,
                                   bg=self.colors["dark"]["btn_clear"], fg="white", font=("Arial", 10),
                                   relief=tk.FLAT, padx=10)
        self.clear_btn.pack(side=tk.RIGHT, padx=5)

        # ==================== ОСНОВНАЯ ЗОНА ====================
        self.main_frame = tk.Frame(root, bg=self.colors["dark"]["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        self.sidebar_frame = tk.Frame(self.main_frame, bg=self.colors["dark"]["sidebar"], width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.sidebar_frame.pack_propagate(False)

        sidebar_header = tk.Frame(self.sidebar_frame, bg=self.colors["dark"]["panel"])
        sidebar_header.pack(fill=tk.X)
        tk.Label(sidebar_header, text="💬 История чатов",
                 bg=self.colors["dark"]["panel"], fg="white",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=8, pady=6)

        del_all_btn = tk.Button(sidebar_header, text="🗑", command=self.delete_all_chats,
                                bg="#D32F2F", fg="white", font=("Arial", 11, "bold"),
                                relief=tk.FLAT, padx=6, pady=2)
        del_all_btn.pack(side=tk.RIGHT, padx=(0, 3), pady=4)

        new_chat_btn = tk.Button(sidebar_header, text="＋", command=self.new_chat,
                                 bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                 relief=tk.FLAT, padx=8, pady=2)
        new_chat_btn.pack(side=tk.RIGHT, padx=5, pady=4)

        self.chats_listbox_frame = tk.Frame(self.sidebar_frame, bg=self.colors["dark"]["sidebar"])
        self.chats_listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.chats_canvas = tk.Canvas(self.chats_listbox_frame,
                                      bg=self.colors["dark"]["sidebar"],
                                      highlightthickness=0)
        self.chats_scrollbar = tk.Scrollbar(self.chats_listbox_frame,
                                            orient="vertical",
                                            command=self.chats_canvas.yview)
        self.chats_inner = tk.Frame(self.chats_canvas, bg=self.colors["dark"]["sidebar"])

        self.chats_canvas.configure(yscrollcommand=self.chats_scrollbar.set)
        self.chats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._chats_window = self.chats_canvas.create_window(
            (0, 0), window=self.chats_inner, anchor="nw"
        )

        self.chats_inner.bind("<Configure>", self._on_chats_inner_configure)
        self.chats_canvas.bind("<Configure>", self._on_chats_canvas_configure)
        self.chats_canvas.bind("<MouseWheel>", self._on_chats_mousewheel)
        self.chats_inner.bind("<MouseWheel>", self._on_chats_mousewheel)

        self.chat_frame = tk.Frame(self.main_frame, bg=self.colors["dark"]["bg"])
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state='disabled',
                                                   bg=self.colors["dark"]["bg"], fg=self.colors["dark"]["fg"],
                                                   font=("Consolas", 11), insertbackground="white")
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self.chat_area.tag_config("meta", foreground="#888888", font=("Consolas", 9))
        self.chat_area.tag_config("thinking", foreground=self.colors["dark"]["thinking"],
                                  font=("Consolas", 10, "italic"))
        self.chat_area.tag_config("image", foreground="#9C27B0", font=("Consolas", 10, "bold"))

        # ==================== ПОЛЕ ВВОДА ====================
        self.input_frame = tk.Frame(root, bg=self.colors["dark"]["bg"])
        self.input_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.copy_btn = tk.Button(self.input_frame, text="📋", command=self.copy_last_response,
                                  bg=self.colors["dark"]["btn_neutral"], fg="white", font=("Arial", 10),
                                  relief=tk.FLAT, padx=10)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.input_entry = tk.Entry(self.input_frame, font=("Consolas", 12),
                                    bg=self.colors["dark"]["input"], fg="white",
                                    insertbackground="white", relief=tk.FLAT)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=8)
        self.input_entry.bind("<Return>", self.send_message)
        self.input_entry.bind("<Control-v>", self.paste_text)
        self.input_entry.bind("<Control-V>", self.paste_text)
        self.input_entry.bind("<Control-c>", self.copy_text)
        self.input_entry.bind("<Control-C>", self.copy_text)
        self.input_entry.bind("<Control-x>", self.cut_text)
        self.input_entry.bind("<Control-X>", self.cut_text)

        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#3c3c3c", fg="white",
                                    activebackground="#4CAF50", activeforeground="white")
        self.context_menu.add_command(label="Вставить", command=self.paste_text)
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Вырезать", command=self.cut_text)
        self.input_entry.bind("<Button-3>", self.show_context_menu)

        self.image_btn = tk.Button(self.input_frame, text="🎨 Картинка", command=self.open_image_generator,
                                   bg=self.colors["dark"]["btn_image"], fg="white",
                                   font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15)
        self.image_btn.pack(side=tk.RIGHT, padx=(0, 5))

        self.send_btn = tk.Button(self.input_frame, text="Отправить", command=self.send_message,
                                  bg=self.colors["dark"]["btn_send"], fg="white",
                                  font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15)
        self.send_btn.pack(side=tk.RIGHT)

        self.stop_btn = tk.Button(self.input_frame, text="Остановить", command=self.stop_generation,
                                  bg=self.colors["dark"]["btn_stop"], fg="white",
                                  font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15)

        # ==================== ДАННЫЕ ====================
        self.messages = []
        self.last_response = ""
        self._image_windows = []
        self._generator_window = None

        self._script_dir = os.path.dirname(os.path.abspath(__file__))
        self._chats_dir = os.path.join(self._script_dir, "chats")
        self._generated_dir = os.path.join(self._script_dir, "generated")
        os.makedirs(self._generated_dir, exist_ok=True)
        self._current_chat_file = None
        self._active_chat_btn = None

        # Z-Image
        self._zimage_dir = r"D:\Z-Image-Turbo-Windows-main"
        self._zimage_url = "http://127.0.0.1:9000"
        self._zimage_ready = False

        self.refresh_models()
        self.refresh_chats_sidebar()

        self.add_message("Система", f"Привет! Модель: {self.current_model.get()}")
        self.add_message("Система",
                         f"💻 Ваш ПК: {self.sys_info['ram_gb']} ГБ ОЗУ, "
                         f"{self.sys_info['vram_gb']} ГБ VRAM, "
                         f"{self.sys_info['cpu_cores']} ядер CPU")
        self.add_message("Система", "💡 Откройте «🏪 Магазин», чтобы скачать новые модели.")
        self.add_message("Система", "🎨 Кнопка «Картинка» — генератор через Z-Image.")

        # Постоянная проверка Z-Image
        threading.Thread(target=self._check_zimage_loop, daemon=True).start()

    # ==================== Z-IMAGE ====================

    def _check_zimage_loop(self):
        """Каждые 5 секунд проверяет, запущен ли Z-Image."""
        first = True
        while True:
            try:
                r = requests.get(self._zimage_url, timeout=2)
                new_state = (r.status_code == 200)
            except Exception:
                new_state = False

            if new_state != self._zimage_ready:
                self._zimage_ready = new_state
                if new_state:
                    self.root.after(0, lambda: self.add_message(
                        "Система", "✅ Z-Image обнаружен! Кнопка «Картинка» активна.", tag="image"))
                else:
                    self.root.after(0, lambda: self.add_message(
                        "Система", "⏸ Z-Image не запущен.", tag="meta"))

            if first:
                first = False
                if not self._zimage_ready:
                    self.root.after(0, lambda: self.add_message(
                        "Система",
                        "⚠️ Z-Image не запущен.\n"
                        "   Нажми «🎨 Картинка» — там будут команды для запуска.", tag="meta"))

            time.sleep(5)

    def open_image_generator(self):
        """Открывает окно генерации картинок."""
        if self._generator_window is not None and self._generator_window.win.winfo_exists():
            self._generator_window.win.lift()
            self._generator_window.win.focus()
            return

        self._generator_window = ImageGeneratorWindow(self.root, self)

    def _translate_prompt(self, prompt_ru):
        """Переводит промт на английский через Qwen 0.5B."""
        try:
            response = ollama.chat(
                model="qwen2.5:0.5b",
                messages=[
                    {"role": "system", "content": "Ты — переводчик. Переведи текст на английский. Ответь ТОЛЬКО переводом, без пояснений. Добавь в конце: masterpiece, best quality, detailed"},
                    {"role": "user", "content": prompt_ru},
                ],
                stream=False,
            )
            return response["message"]["content"].strip()
        except Exception:
            return prompt_ru + ", masterpiece, best quality, detailed"

    def open_generated_folder(self):
        try:
            os.makedirs(self._generated_dir, exist_ok=True)
            os.startfile(self._generated_dir)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")

    # ==================== ОБНОВЛЕНИЕ МОДЕЛЕЙ ====================

    def manual_refresh_models(self):
        self.refresh_models()
        self.status_label.config(text="Список обновлён", fg="#4CAF50")
        self.add_message("Система", f"🔄 Список моделей обновлён. Доступно: {len(self.available_models)}.")

    # ==================== ПАНЕЛЬ ЧАТОВ ====================

    def _on_chats_inner_configure(self, event):
        self.chats_canvas.configure(scrollregion=self.chats_canvas.bbox("all"))

    def _on_chats_canvas_configure(self, event):
        self.chats_canvas.itemconfig(self._chats_window, width=event.width)

    def _on_chats_mousewheel(self, event):
        self.chats_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
            self.toggle_sidebar_btn.config(text="▶ Чаты")
            self.sidebar_visible = False
        else:
            self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5), before=self.chat_frame)
            self.toggle_sidebar_btn.config(text="◀ Чаты")
            self.sidebar_visible = True

    def refresh_chats_sidebar(self):
        for widget in self.chats_inner.winfo_children():
            widget.destroy()
        self._active_chat_btn = None

        if not os.path.exists(self._chats_dir):
            tk.Label(self.chats_inner, text="Нет чатов",
                     bg=self.colors["dark"]["sidebar"], fg="#666666",
                     font=("Arial", 9)).pack(pady=10)
            return

        files = []
        for f in os.listdir(self._chats_dir):
            if f.endswith(".json"):
                full_path = os.path.join(self._chats_dir, f)
                files.append((os.path.getmtime(full_path), full_path, f))
        files.sort(reverse=True)

        if not files:
            tk.Label(self.chats_inner, text="Нет чатов",
                     bg=self.colors["dark"]["sidebar"], fg="#666666",
                     font=("Arial", 9)).pack(pady=10)
            return

        for mtime, full_path, filename in files:
            self._make_chat_button(full_path, filename)

    def _make_chat_button(self, full_path, filename):
        title = filename.replace(".json", "")
        msg_count = 0
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            msgs = data.get("messages", [])
            msg_count = len(msgs)
            for m in msgs:
                if m.get("role") == "user":
                    text = m.get("text", "")
                    title = text[:22] + "…" if len(text) > 22 else text
                    break
        except Exception:
            pass

        is_active = (full_path == self._current_chat_file)
        bg_color = "#4a4a4a" if is_active else self.colors["dark"]["sidebar_item"]

        btn_frame = tk.Frame(self.chats_inner, bg=bg_color, pady=2)
        btn_frame.pack(fill=tk.X, padx=4, pady=2)

        btn = tk.Button(
            btn_frame, text=title, anchor="w",
            bg=bg_color, fg="white", font=("Arial", 9),
            relief=tk.FLAT, padx=6, pady=4, wraplength=120, justify=tk.LEFT,
            command=lambda p=full_path: self.load_chat(p)
        )
        btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        count_lbl = tk.Label(btn_frame, text=str(msg_count),
                             bg=bg_color, fg="#888888", font=("Arial", 8))
        count_lbl.pack(side=tk.LEFT, padx=(0, 2))

        del_btn = tk.Button(
            btn_frame, text="🗑", bg="#8B0000", fg="white",
            font=("Arial", 9), relief=tk.FLAT, padx=4, pady=3,
            command=lambda p=full_path: self.delete_chat(p)
        )
        del_btn.pack(side=tk.RIGHT, padx=(0, 3))

        if is_active:
            self._active_chat_btn = btn_frame

    def delete_chat(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            msgs = data.get("messages", [])
            preview = ""
            for m in msgs:
                if m.get("role") == "user":
                    preview = m.get("text", "")[:40]
                    break
            label = f"«{preview}»" if preview else os.path.basename(filepath)
        except Exception:
            label = os.path.basename(filepath)

        if not messagebox.askyesno("Удалить чат", f"Удалить чат {label}?"):
            return

        try:
            os.remove(filepath)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{e}")
            return

        if self._current_chat_file == filepath:
            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state='disabled')
            self.messages = []
            self.last_response = ""
            self._current_chat_file = None
            self.update_token_counter()
            self.add_message("Система", "🗑 Чат удалён. Начните новый!")

        self.refresh_chats_sidebar()

    def delete_all_chats(self):
        if not os.path.exists(self._chats_dir):
            messagebox.showinfo("Нет чатов", "Папка с чатами пуста.")
            return

        files = [f for f in os.listdir(self._chats_dir) if f.endswith(".json")]
        if not files:
            messagebox.showinfo("Нет чатов", "Нет сохранённых чатов.")
            return

        if not messagebox.askyesno(
            "Удалить все чаты",
            f"Удалить все {len(files)} чатов?\nЭто действие нельзя отменить!"
        ):
            return

        errors = 0
        for f in files:
            try:
                os.remove(os.path.join(self._chats_dir, f))
            except Exception:
                errors += 1

        self.chat_area.config(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state='disabled')
        self.messages = []
        self.last_response = ""
        self._current_chat_file = None
        self.update_token_counter()

        if errors:
            self.add_message("Система", f"⚠️ Удалено с ошибками ({errors} файлов не удалось).")
        else:
            self.add_message("Система", f"🗑 Все {len(files)} чатов удалены!")

        self.refresh_chats_sidebar()

    def load_chat(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть чат:\n{e}")
            return

        self.chat_area.config(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state='disabled')
        self.messages = []
        self.last_response = ""

        self._current_chat_file = filepath

        for msg in data.get("messages", []):
            role = msg.get("role", "")
            text = msg.get("text", "")
            time_str = msg.get("time", "")

            if role == "user":
                self.add_message("Ты", text, f"[{time_str}]" if time_str else "")
                self.messages.append({"role": "user", "content": text})
            elif role == "assistant":
                self.add_message("ИИ", text, f"[{time_str}]" if time_str else "")
                self.messages.append({"role": "assistant", "content": text})

        self.update_token_counter()
        self.refresh_chats_sidebar()

    def new_chat(self):
        self.chat_area.config(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state='disabled')
        self.messages = []
        self.last_response = ""
        self._current_chat_file = None
        self.update_token_counter()
        self.add_message("Система", "✨ Новый чат начат!")
        self.refresh_chats_sidebar()

    # ==================== СОХРАНЕНИЕ ЧАТОВ ====================

    def _start_new_chat_file(self):
        os.makedirs(self._chats_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._current_chat_file = os.path.join(self._chats_dir, f"{timestamp}.json")
        data = {
            "started": datetime.now().isoformat(),
            "model": self.current_model.get(),
            "messages": []
        }
        with open(self._current_chat_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.root.after(0, self.refresh_chats_sidebar)

    def _save_message_to_file(self, role, text):
        if self._current_chat_file is None:
            self._start_new_chat_file()
        try:
            with open(self._current_chat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["messages"].append({
                "role": role,
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": text
            })
            with open(self._current_chat_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.root.after(0, self.refresh_chats_sidebar)
        except Exception as e:
            print(f"[Сохранение чата] Ошибка: {e}")

    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================

    def refresh_models(self):
        installed = set()
        try:
            resp = ollama.list()
            for m in resp.get("models", []):
                name = m.get("name") or m.get("model")
                if name:
                    installed.add(name)
        except Exception as e:
            print(f"[refresh_models] Ошибка: {e}")

        self.model_map = dict(self.base_models)

        for name in installed:
            if name in self.model_map.values():
                continue
            display = None
            for m in MODEL_CATALOG:
                if m["id"] == name:
                    display = m["name"]
                    break
            if display is None:
                display = name
            base_display = display
            counter = 1
            while display in self.model_map:
                display = f"{base_display} ({counter})"
                counter += 1
            self.model_map[display] = name

        self.available_models = list(self.model_map.keys())
        try:
            self.model_combo["values"] = self.available_models
        except Exception:
            pass

        if self.current_model.get() not in self.model_map:
            self.current_model.set(self.available_models[0])

    def on_model_change(self, event=None):
        self.add_message("Система", f"🔄 Модель изменена на: {self.current_model.get()}")

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        theme = "dark" if self.is_dark else "light"
        c = self.colors[theme]
        self.root.configure(bg=c["bg"])
        self.top_frame.configure(bg=c["panel"])
        for w in self.top_frame.winfo_children():
            try:
                w.configure(bg=c["panel"])
            except Exception:
                pass
        self.think_check.configure(bg=c["panel"], fg=c["fg"], selectcolor=c["panel"],
                                   activebackground=c["panel"], activeforeground=c["fg"])
        self.think_status.configure(bg=c["panel"], fg=c["meta"])
        self.token_counter.configure(bg=c["panel"], fg="#00BCD4")
        self.status_label.configure(bg=c["panel"])
        self.shop_btn.configure(bg=c["btn_shop"], fg="white")
        self.clear_ram_btn.configure(bg=c["btn_neutral"], fg="white")
        self.theme_btn.configure(bg=c["btn_neutral"], fg="white",
                                 text="☀️ Светлая" if self.is_dark else "🌙 Тёмная")
        self.settings_btn.configure(bg=c["btn_neutral"], fg="white")
        self.clear_btn.configure(bg=c["btn_clear"], fg="white")
        self.toggle_sidebar_btn.configure(bg=c["btn_neutral"], fg="white")
        self.refresh_btn.configure(bg=c["btn_neutral"], fg="white")
        self.chat_area.configure(bg=c["bg"], fg=c["fg"])
        self.main_frame.configure(bg=c["bg"])
        self.chat_frame.configure(bg=c["bg"])
        self.input_frame.configure(bg=c["bg"])
        self.copy_btn.configure(bg=c["btn_neutral"], fg="white")
        self.input_entry.configure(bg=c["input"], fg=c["fg"], insertbackground=c["fg"])
        self.send_btn.configure(bg=c["btn_send"])
        self.stop_btn.configure(bg=c["btn_stop"])
        self.image_btn.configure(bg=c["btn_image"])
        self.chat_area.tag_config("meta", foreground=c["meta"])
        self.chat_area.tag_config("thinking", foreground=c["thinking"], font=("Consolas", 10, "italic"))

    def paste_text(self, event=None):
        try:
            self.input_entry.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass
        return "break"

    def copy_text(self, event=None):
        try:
            selected = self.input_entry.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def cut_text(self, event=None):
        try:
            selected = self.input_entry.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.input_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return "break"

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        return "break"

    def on_think_toggle(self):
        self.think_status.config(text="Вкл" if self.think_var.get() else "Выкл")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Настройки модели")
        win.geometry("420x450")
        win.configure(bg="#2d2d2d")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Температура:", bg="#2d2d2d", fg="white").pack(anchor="w", padx=15, pady=(15, 2))
        tk.Scale(win, from_=0.1, to=1.5, resolution=0.05, orient="horizontal",
                 variable=self.temperature_var, bg="#2d2d2d", fg="white",
                 highlightbackground="#2d2d2d", length=380).pack(padx=15, pady=2)

        tk.Label(win, text="Контекст (num_ctx):", bg="#2d2d2d", fg="white").pack(anchor="w", padx=15, pady=(10, 2))
        tk.Scale(win, from_=2048, to=32768, resolution=2048, orient="horizontal",
                 variable=self.num_ctx_var, bg="#2d2d2d", fg="white",
                 highlightbackground="#2d2d2d", length=380,
                 command=self.on_ctx_change).pack(padx=15, pady=2)

        tk.Label(win, text="Top-K:", bg="#2d2d2d", fg="white").pack(anchor="w", padx=15, pady=(10, 2))
        tk.Scale(win, from_=1, to=100, orient="horizontal",
                 variable=self.top_k_var, bg="#2d2d2d", fg="white",
                 highlightbackground="#2d2d2d", length=380).pack(padx=15, pady=2)

        tk.Label(win, text="Top-P:", bg="#2d2d2d", fg="white").pack(anchor="w", padx=15, pady=(10, 2))
        tk.Scale(win, from_=0.1, to=1.0, resolution=0.05, orient="horizontal",
                 variable=self.top_p_var, bg="#2d2d2d", fg="white",
                 highlightbackground="#2d2d2d", length=380).pack(padx=15, pady=2)

        btn_frame = tk.Frame(win, bg="#2d2d2d")
        btn_frame.pack(pady=15)

        def apply_settings():
            self.add_message("Система",
                             f"⚙️ Настройки: темп={self.temperature_var.get():.2f}, "
                             f"контекст={self.num_ctx_var.get()}")
            self.update_token_counter()
            win.destroy()

        def open_help():
            self.show_help_window()

        tk.Button(btn_frame, text="Применить", command=apply_settings,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❓ Справка", command=open_help,
                  bg="#2196F3", fg="white", font=("Arial", 11, "bold"), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy,
                  bg="#555555", fg="white", font=("Arial", 11), padx=15).pack(side=tk.LEFT, padx=5)

    def show_help_window(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("❓ Справка по настройкам")
        help_win.geometry("650x600")
        help_win.configure(bg="#1e1e1e")
        help_win.grab_set()

        tk.Label(help_win, text="❓ Справка по настройкам",
                 font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=(15, 5))

        text = scrolledtext.ScrolledText(help_win, wrap=tk.WORD, bg="#1e1e1e", fg="#dddddd",
                                         font=("Consolas", 10), padx=15, pady=15,
                                         insertbackground="white")
        text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        help_text = """
🌡️ ТЕМПЕРАТУРА (temperature)
─────────────────────────────
• 0.1–0.3  → Точно, но скучно. Для кода и фактов.
• 0.7–0.9  → Баланс. Для диалогов. (рекомендуется)
• 1.0–1.2  → Творчески. Для идей и историй.
• 1.5+     → Хаос, возможен бред.

📏 КОНТЕКСТ (num_ctx)
─────────────────────────────
• 2048    → Короткие диалоги.
• 4096    → Стандарт. (рекомендуется)
• 8192    → Длинные диалоги.
• 16384+  → Требует много ОЗУ и VRAM.

🎯 TOP-K
─────────────────────────────
• 1 — скучно, 40 — стандарт, 100 — разнообразно.

🎲 TOP-P
─────────────────────────────
• 0.1 — скучно, 0.9 — стандарт, 1.0 — разнообразно.

🎨 ГЕНЕРАЦИЯ КАРТИНОК (Z-Image)
─────────────────────────────
1. Нажми кнопку «🎨 Картинка» — откроется 3-е окно.
2. Если Z-Image не запущен — в окне будут команды.
3. Запусти Z-Image вручную (скопируй команды).
4. Введи промт по-русски.
5. Программа переведёт на английский и скопирует в буфер.
6. Вставь в браузере Z-Image и нажми Generate.
7. Нажми «Я нажал Generate» — программа следит за папкой outputs.
8. Когда картинка появится — она откроется в окне.

⚠️ Генерация: 1-3 минуты на GTX 1060 3GB.
⚠️ Картинки сохраняются в D:\\Z-Image-Turbo-Windows-main\\outputs\\

💡 СОВЕТЫ
─────────────────────────────
• Код: temperature=0.3
• Чат: temperature=0.8 (по умолчанию)
• Творчество: temperature=1.0–1.2
"""
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)

        tk.Button(help_win, text="Понятно", command=help_win.destroy,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                  padx=20, pady=5).pack(pady=(0, 15))

    def on_ctx_change(self, value):
        if self._ctx_after_id is not None:
            self.root.after_cancel(self._ctx_after_id)
        self._ctx_after_id = self.root.after(50, self.update_token_counter)

    def copy_last_response(self):
        if not self.last_response:
            messagebox.showinfo("Копировать", "Нет ответа.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_response)
        self.add_message("Система", "📋 Скопировано.")

    def clear_ram(self):
        self.add_message("Система", "🧹 Очистка ОЗУ, подождите несколько секунд...")
        def task():
            try:
                r = requests.get("http://localhost:11434/api/ps", timeout=5)
                models = r.json().get("models", [])
                if not models:
                    self.root.after(0, lambda: self.add_message("Система", "🧹 В ОЗУ нет загруженных моделей."))
                    return
                count = 0
                for m in models:
                    name = m.get("name") or m.get("model")
                    if name:
                        requests.post("http://localhost:11434/api/generate",
                                      json={"model": name, "keep_alive": 0}, timeout=10)
                        count += 1
                self.root.after(0, lambda: self.add_message("Система", f"🧹 Выгружено моделей: {count}."))
            except Exception as e:
                self.root.after(0, lambda: self.add_message("Ошибка", f"Не удалось очистить ОЗУ: {e}"))
        threading.Thread(target=task, daemon=True).start()

    def add_message(self, sender, text, extra_info="", tag=None):
        self.chat_area.config(state='normal')
        if tag:
            self.chat_area.insert(tk.END, f"{sender}: {text}\n", (tag,))
        else:
            self.chat_area.insert(tk.END, f"{sender}: {text}")
        if extra_info:
            self.chat_area.insert(tk.END, f"  {extra_info}", ("meta",))
        if not tag:
            self.chat_area.insert(tk.END, "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def append_thinking_to_chat(self, text):
        self.chat_area.config(state='normal')
        if not self._thinking_started:
            self.chat_area.insert(tk.END, "\n🤖 Мышления: ", ("thinking",))
            self._thinking_started = True
        self.chat_area.insert(tk.END, text, ("thinking",))
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def append_answer_to_chat(self, text):
        self.chat_area.config(state='normal')
        if not self._answer_started:
            self.chat_area.insert(tk.END, "\n\n✅ Ответ: ", ("meta",))
            self._answer_started = True
        self.chat_area.insert(tk.END, text)
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def count_tokens(self):
        return sum(len(m.get('content', '')) for m in self.messages) // 4

    def update_token_counter(self):
        self._ctx_after_id = None
        used = self.count_tokens()
        limit = self.num_ctx_var.get() or 4096
        percent = (used / limit * 100) if limit > 0 else 0
        color = "#F44336" if percent > 90 else "#FF9800" if percent > 70 else "#00BCD4"
        self.token_counter.config(text=f"📊 {used} / {limit} ({percent:.0f}%)", fg=color)

    def clear_chat(self):
        self.chat_area.config(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state='disabled')
        self.messages = []
        self.last_response = ""
        self._current_chat_file = None
        self.update_token_counter()
        self.add_message("Система", "История очищена.")
        self.refresh_chats_sidebar()

    def stop_generation(self):
        self.stop_flag = True
        self.status_label.config(text="Остановка...", fg="#FFA500")
        self.add_message("Система", "🛑 Остановка...")

    def send_message(self, event=None):
        if self.is_generating:
            return
        user_text = self.input_entry.get().strip()
        if not user_text:
            return
        self.input_entry.delete(0, tk.END)
        self.add_message("Ты", user_text)
        self.messages.append({'role': 'user', 'content': user_text})
        self._save_message_to_file("user", user_text)
        self.update_token_counter()
        self.stop_flag = False
        self.is_generating = True
        self._thinking_started = False
        self._answer_started = False
        self.send_btn.pack_forget()
        self.stop_btn.pack(side=tk.RIGHT)
        self.status_label.config(text="Отправка...", fg="#FFA500")
        threading.Thread(target=self.get_response, daemon=True).start()

    def get_response(self):
        try:
            think_enabled = self.think_var.get()
            self.root.after(0, lambda: self.status_label.config(text="Загрузка в ОЗУ...", fg="#FFA500"))
            start_time = time.time()
            options = {"temperature": self.temperature_var.get(), "num_ctx": self.num_ctx_var.get(),
                       "top_k": self.top_k_var.get(), "top_p": self.top_p_var.get()}
            display_name = self.current_model.get()
            real_model_id = self.model_map.get(display_name, display_name)
            sys_msg = {'role': 'system',
                       'content': 'Ты — полезный русскоязычный ассистент. Отвечай только на русском языке.'}
            messages_for_model = [sys_msg] + self.messages

            response = ollama.chat(model=real_model_id, messages=messages_for_model,
                                   think=think_enabled, stream=True, options=options)
            first_chunk = True
            full_response = ""
            thinking_text = ""
            eval_count = 0

            for chunk in response:
                if self.stop_flag:
                    self.root.after(0, self.add_message, "Система", "🛑 Остановлено.")
                    break
                if first_chunk:
                    self.root.after(0, lambda: self.status_label.config(text="Генерация...", fg="#4CAF50"))
                    first_chunk = False
                if hasattr(chunk, 'eval_count') and chunk.eval_count:
                    eval_count = chunk.eval_count
                if hasattr(chunk.message, 'thinking') and chunk.message.thinking:
                    thinking_text += chunk.message.thinking
                    self.root.after(0, self.append_thinking_to_chat, chunk.message.thinking)
                if hasattr(chunk.message, 'content') and chunk.message.content:
                    full_response += chunk.message.content
                    self.root.after(0, self.append_answer_to_chat, chunk.message.content)

            full_response_clean = full_response.replace('<think>', '').replace('</think>', '').strip()
            if full_response_clean:
                self.messages.append({'role': 'assistant', 'content': full_response_clean})
                if thinking_text:
                    self.messages[-1]['thinking'] = thinking_text
                self.last_response = full_response_clean
                self.root.after(0, self.update_token_counter)
                self.root.after(0, self._save_message_to_file, "assistant", full_response_clean)

            elapsed = time.time() - start_time
            tokens_per_sec = eval_count / elapsed if elapsed > 0 and eval_count > 0 else 0
            stats = f"⏱️ {elapsed:.1f}с | {tokens_per_sec:.1f} ток/сек"
            if self.stop_flag:
                stats = "🛑 Остановлено (частичный ответ сохранён)"
            self.root.after(0, self.finish_response, stats)
        except Exception as e:
            self.root.after(0, self.add_message, "Ошибка", str(e))
            self.root.after(0, self.finish_response, "")

    def finish_response(self, stats):
        self.chat_area.config(state='normal')
        if stats:
            self.chat_area.insert(tk.END, f"\n  {stats}", ("meta",))
        self.chat_area.insert(tk.END, "\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')
        self.stop_btn.pack_forget()
        self.send_btn.pack(side=tk.RIGHT)
        self.is_generating = False
        self.stop_flag = False
        self.status_label.config(text="Готова", fg="#4CAF50")

    # ==================== МАГАЗИН МОДЕЛЕЙ ====================

    def open_shop(self):
        shop = tk.Toplevel(self.root)
        shop.title("🏪 Магазин моделей")
        shop.geometry("1000x720")
        shop.minsize(750, 500)
        shop.configure(bg="#1e1e1e")
        shop.transient(self.root)

        header = tk.Frame(shop, bg="#1e1e1e")
        header.pack(fill=tk.X, padx=15, pady=(15, 5))
        tk.Label(header, text="🏪 Магазин моделей", font=("Arial", 18, "bold"),
                 bg="#1e1e1e", fg="white").pack(anchor="w")
        tk.Label(header,
                 text=f"💻 Ваш ПК: {self.sys_info['ram_gb']} ГБ ОЗУ | "
                      f"{self.sys_info['vram_gb']} ГБ VRAM | {self.sys_info['cpu_cores']} ядер CPU",
                 font=("Arial", 10), bg="#1e1e1e", fg="#00BCD4").pack(anchor="w", pady=(5, 0))

        legend = tk.Frame(shop, bg="#1e1e1e")
        legend.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(legend, text="🟢 Хорошо", font=("Arial", 10), bg="#1e1e1e", fg="#4CAF50").pack(side=tk.LEFT, padx=10)
        tk.Label(legend, text="🟡 Средне", font=("Arial", 10), bg="#1e1e1e", fg="#FF9800").pack(side=tk.LEFT, padx=10)
        tk.Label(legend, text="🔴 Плохо", font=("Arial", 10), bg="#1e1e1e", fg="#F44336").pack(side=tk.LEFT, padx=10)

        def toggle_fullscreen():
            state = shop.attributes("-fullscreen")
            shop.attributes("-fullscreen", not state)

        tk.Button(legend, text="⛶ На весь экран", command=toggle_fullscreen,
                  bg="#555555", fg="white", font=("Arial", 10), relief=tk.FLAT, padx=10).pack(side=tk.RIGHT, padx=10)

        container = tk.Frame(shop, bg="#1e1e1e")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#1e1e1e")

        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_inner_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_inner_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        inner.bind("<MouseWheel>", on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        installed_models = set()
        try:
            resp = ollama.list()
            for m in resp.get("models", []):
                name = m.get("name") or m.get("model")
                if name:
                    installed_models.add(name)
        except Exception:
            pass

        for model in MODEL_CATALOG:
            compat_text, compat_color = check_compatibility(model, self.sys_info)
            is_installed = model["id"] in installed_models

            row = tk.Frame(inner, bg="#2d2d2d", pady=6)
            row.pack(fill=tk.X, pady=3, padx=5)
            row.bind("<MouseWheel>", on_mousewheel)

            info_frame = tk.Frame(row, bg="#2d2d2d")
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            info_frame.bind("<MouseWheel>", on_mousewheel)

            tk.Label(info_frame, text=model["name"], font=("Arial", 11, "bold"),
                     bg="#2d2d2d", fg="white").pack(anchor="w")
            tk.Label(info_frame, text=model["description"], font=("Arial", 9),
                     bg="#2d2d2d", fg="#aaaaaa").pack(anchor="w")
            tk.Label(info_frame,
                     text=f"Размер: {model['size']}  |  RAM: {model['min_ram']} ГБ  |  VRAM: {model['min_vram']} ГБ",
                     font=("Arial", 8), bg="#2d2d2d", fg="#666666").pack(anchor="w")

            right_frame = tk.Frame(row, bg="#2d2d2d")
            right_frame.pack(side=tk.RIGHT, padx=10)
            right_frame.bind("<MouseWheel>", on_mousewheel)

            tk.Label(right_frame, text=compat_text, font=("Arial", 10, "bold"),
                     bg="#2d2d2d", fg=compat_color).pack(anchor="e")

            if is_installed:
                install_btn = tk.Button(right_frame, text="✅ Установлена",
                                        state=tk.DISABLED, font=("Arial", 10),
                                        bg="#555555", fg="white", relief=tk.FLAT, padx=15, pady=5, width=15)
                install_btn.pack(side=tk.LEFT)
                del_btn = tk.Button(right_frame, text="🗑 Удалить", font=("Arial", 10),
                                    bg="#D32F2F", fg="white", relief=tk.FLAT, padx=10, pady=5)
                del_btn.config(command=lambda m=model, ib=install_btn, db=del_btn: self.delete_model(m, ib, db))
                del_btn.pack(side=tk.LEFT, padx=(5, 0))
            else:
                install_btn = tk.Button(right_frame, text="📥 Установить",
                                        font=("Arial", 10),
                                        bg="#4CAF50", fg="white", relief=tk.FLAT, padx=15, pady=5, width=15)
                install_btn.config(command=lambda m=model, b=install_btn: self.install_model(m, b))
                install_btn.pack(side=tk.LEFT)

        tk.Button(shop, text="Закрыть", command=shop.destroy,
                  bg="#555555", fg="white", font=("Arial", 10),
                  relief=tk.FLAT, padx=20, pady=5).pack(pady=(0, 15))

    def install_model(self, model, btn):
        btn.config(text="⏳ Загрузка...", state=tk.DISABLED, bg="#FF9800")

        progress_win = tk.Toplevel(self.root)
        progress_win.title(f"Загрузка: {model['name']}")
        progress_win.geometry("450x150")
        progress_win.configure(bg="#1e1e1e")
        progress_win.transient(self.root)
        progress_win.grab_set()

        tk.Label(progress_win, text=f"Скачивание {model['name']}...",
                 font=("Arial", 11), bg="#1e1e1e", fg="white").pack(pady=10)

        progress_var = tk.DoubleVar(value=0)
        bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=400)
        bar.pack(pady=5, padx=25)

        status_lbl = tk.Label(progress_win, text="0%",
                              font=("Arial", 10), bg="#1e1e1e", fg="#aaaaaa")
        status_lbl.pack()

        self._pull_progress = {
            "win": progress_win,
            "var": progress_var,
            "label": status_lbl,
        }

        def task():
            try:
                for progress in ollama.pull(model["id"], stream=True):
                    if isinstance(progress, dict):
                        status = progress.get("status", "")
                        total = progress.get("total", 0) or 0
                        completed = progress.get("completed", 0) or 0
                    else:
                        status = getattr(progress, "status", "") or ""
                        total = getattr(progress, "total", 0) or 0
                        completed = getattr(progress, "completed", 0) or 0

                    if total > 0 and completed > 0:
                        percent = (completed / total) * 100
                        self.root.after(0, self._update_progress_ui, percent, f"{percent:.1f}%")
                    elif status == "verifying sha256 digest":
                        self.root.after(0, self._update_progress_ui, 100, "Проверка...")
                    elif status == "writing manifest":
                        self.root.after(0, self._update_progress_ui, 100, "Запись...")
                    elif status == "success":
                        break

                self.root.after(0, self._update_progress_ui, 100, "Готово!")
                self.root.after(500, self._finish_install, model, btn, True)
            except Exception as e:
                print(f"[PULL] Ошибка: {e}")
                self.root.after(0, self._finish_install, model, btn, False, str(e))

        threading.Thread(target=task, daemon=True).start()

    def _update_progress_ui(self, percent, text):
        info = getattr(self, "_pull_progress", None)
        if not info:
            return
        try:
            info["var"].set(percent)
            info["label"].config(text=text)
        except Exception:
            pass

    def _finish_install(self, model, btn, success, error_msg=""):
        info = getattr(self, "_pull_progress", None)
        if info:
            try:
                info["win"].destroy()
            except Exception:
                pass
            self._pull_progress = None

        if success:
            btn.config(text="✅ Установлена", state=tk.DISABLED, bg="#555555")
            self.refresh_models()
            self.add_message("Система", f"✅ Модель «{model['name']}» установлена!")
        else:
            btn.config(text="📥 Установить", state=tk.NORMAL, bg="#4CAF50")
            self.add_message("Ошибка", f"Не удалось установить модель: {error_msg}")

    def delete_model(self, model, install_btn, del_btn):
        if not messagebox.askyesno("Удаление", f"Удалить модель «{model['name']}»?\nЭто освободит место на диске."):
            return
        try:
            ollama.delete(model["id"])
            self.add_message("Система", f"🗑 Модель «{model['name']}» удалена.")
            install_btn.config(text="📥 Установить", state=tk.NORMAL, bg="#4CAF50",
                               command=lambda m=model, b=install_btn: self.install_model(m, b))
            del_btn.destroy()
            self.refresh_models()
        except Exception as e:
            self.add_message("Ошибка", f"Не удалось удалить модель: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", "Consolas 11")
    app = LocalChatApp(root)
    app.chat_area.tag_config("meta", foreground="#888888", font=("Consolas", 9))
    app.chat_area.tag_config("thinking", foreground="#888888", font=("Consolas", 10, "italic"))
    app.chat_area.tag_config("image", foreground="#9C27B0", font=("Consolas", 10, "bold"))
    root.mainloop()