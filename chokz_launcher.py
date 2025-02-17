import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import subprocess
import json
import requests
from PIL import Image, ImageTk

class GameCard(ttk.Frame):
    def __init__(self, parent, game_name, game_info, launcher, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.launcher = launcher
        self.game_name = game_name
        self.game_info = game_info
        
        # Создаем стиль для карточки
        self.configure(style='GameCard.TFrame')
        self.setup_card()

    def setup_card(self):
        # Загрузка изображения
        try:
            logo_path = os.path.join(self.game_info['path'], 'game_logo.png')
            if not os.path.exists(logo_path):
                # Копируем стандартное лого
                default_logo = os.path.join(os.path.dirname(__file__), 'assets', 'default_logo.png')
                shutil.copy(default_logo, logo_path)
            
            image = Image.open(logo_path)
            image = image.resize((200, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
        except Exception:
            # Если произошла ошибка, используем заглушку
            photo = self.launcher.default_logo

        # Создаем и размещаем элементы карточки
        self.logo_label = ttk.Label(self, image=photo)
        self.logo_label.image = photo
        self.logo_label.pack(pady=5)

        self.name_label = ttk.Label(self, text=self.game_name, style='GameTitle.TLabel')
        self.name_label.pack(pady=5)

        self.play_button = ttk.Button(
            self, 
            text="ИГРАТЬ",
            style='GamePlay.TButton',
            command=lambda: self.launcher.launch_game(self.game_info)
        )
        self.play_button.pack(pady=5)

        # Привязываем событие клика к показу информации
        self.logo_label.bind('<Button-1>', self.show_game_info)
        self.name_label.bind('<Button-1>', self.show_game_info)

    def show_game_info(self, event=None):
        self.launcher.show_game_details(self.game_name, self.game_info)

class ChokzLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chokz Game Launcher")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1b2838')
        
        # Загружаем стандартное лого
        self.load_default_logo()
        
        # Создаем стили
        self.create_styles()
        
        # Загрузка списка установленных игр
        self.installed_games = self.load_installed_games()
        
        # Создание основного интерфейса
        self.create_gui()
        
        # URL для загрузки списка доступных игр
        self.games_api_url = "https://api.chokz-games.com/games"  # Замените на реальный API
        
    def create_styles(self):
        style = ttk.Style()
        style.configure('GameCard.TFrame', background='#2a475e', padding=10)
        style.configure('GameTitle.TLabel', 
                       font=('Arial', 12, 'bold'),
                       background='#2a475e',
                       foreground='white')
        style.configure('GamePlay.TButton',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        style.configure('Header.TFrame', background='#171a21')
        style.configure('Header.TLabel',
                       font=('Arial', 24, 'bold'),
                       foreground='white',
                       background='#171a21')

    def load_default_logo(self):
        try:
            image = Image.open(os.path.join('assets', 'default_logo.png'))
            image = image.resize((200, 300), Image.Resampling.LANCZOS)
            self.default_logo = ImageTk.PhotoImage(image)
        except Exception:
            # Создаем пустое изображение если не удалось загрузить лого
            self.default_logo = None
            
    def create_gui(self):
        # Верхняя панель
        self.header = ttk.Frame(self.root, style='Header.TFrame')
        self.header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            self.header,
            text="CHOKZ LAUNCHER",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            self.header,
            text="Добавить игру",
            command=self.add_game
        ).pack(side=tk.RIGHT)
        
        # Основная область с играми (с поддержкой скролла)
        self.canvas = tk.Canvas(self.root, bg='#1b2838')
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.games_frame = ttk.Frame(self.canvas, style='GameCard.TFrame')
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.games_frame, anchor="nw")
        
        self.games_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Отображение игр
        self.refresh_games_list()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def show_game_details(self, game_name, game_info):
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Информация об игре: {game_name}")
        details_window.geometry("600x400")
        details_window.configure(bg='#1b2838')

        # Загружаем информацию об игре
        game_details = game_info.get('details', {
            'description': 'Описание игры отсутствует',
            'developer': 'Неизвестный разработчик',
            'version': '1.0'
        })

        # Создаем и размещаем элементы
        ttk.Label(details_window, text=game_name, style='GameTitle.TLabel').pack(pady=10)
        
        description_text = tk.Text(details_window, height=5, width=50)
        description_text.insert('1.0', game_details.get('description', ''))
        description_text.pack(pady=10)
        
        ttk.Label(details_window, text=f"Разработчик: {game_details.get('developer', '')}", 
                 style='GameTitle.TLabel').pack()
        ttk.Label(details_window, text=f"Версия: {game_details.get('version', '')}", 
                 style='GameTitle.TLabel').pack()

        def save_details():
            game_info['details'] = {
                'description': description_text.get('1.0', tk.END).strip(),
                'developer': game_details.get('developer', ''),
                'version': game_details.get('version', '')
            }
            self.save_installed_games()
            details_window.destroy()

        ttk.Button(details_window, text="Сохранить", command=save_details).pack(pady=10)
        ttk.Button(details_window, text="Закрыть", command=details_window.destroy).pack()

    def load_installed_games(self):
        try:
            with open("installed_games.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_installed_games(self):
        with open("installed_games.json", "w") as f:
            json.dump(self.installed_games, f)
            
    def add_game(self):
        game_dir = filedialog.askdirectory(
            title="Выберите папку с игрой"
        )
        
        if game_dir:
            # Создаем окно для выбора файла
            file_window = tk.Toplevel(self.root)
            file_window.title("Выберите файл для запуска")
            file_window.geometry("400x300")
            
            # Создаем список всех Python файлов в директории
            python_files = [f for f in os.listdir(game_dir) if f.endswith('.py')]
            
            if not python_files:
                messagebox.showerror("Ошибка", "В выбранной папке не найдены Python файлы")
                file_window.destroy()
                return
                
            # Создаем фрейм со скроллбаром
            frame = ttk.Frame(file_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Создаем список файлов
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=listbox.yview)
            
            # Добавляем файлы в список
            for file in python_files:
                listbox.insert(tk.END, file)
            
            def select_file():
                if listbox.curselection():
                    selected_file = listbox.get(listbox.curselection())
                    game_name = os.path.basename(game_dir)
                    game_info = {
                        'path': game_dir,
                        'main_file': selected_file
                    }
                    self.installed_games[game_name] = game_info
                    self.save_installed_games()
                    self.refresh_games_list()
                    file_window.destroy()
                else:
                    messagebox.showwarning("Предупреждение", "Пожалуйста, выберите файл")
            
            # Кнопки
            button_frame = ttk.Frame(file_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(button_frame, text="Выбрать", command=select_file).pack(side=tk.RIGHT)
            ttk.Button(button_frame, text="Отмена", command=file_window.destroy).pack(side=tk.RIGHT, padx=5)
            
    def launch_game(self, game_info):
        try:
            game_path = os.path.join(game_info['path'], game_info['main_file'])
            subprocess.Popen(["python", game_path], cwd=game_info['path'])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить игру: {str(e)}")
            
    def download_game(self, game_name):
        # Здесь должна быть логика загрузки игры с сервера
        try:
            # Имитация загрузки
            messagebox.showinfo("Загрузка", f"Загрузка игры {game_name}...")
            # После загрузки добавляем в установленные
            self.installed_games[game_name] = f"games/{game_name}"
            self.save_installed_games()
            self.refresh_games_list()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить игру: {str(e)}")
            
    def refresh_games_list(self):
        # Очистка текущего списка
        for widget in self.games_frame.winfo_children():
            widget.destroy()
            
        # Создаем сетку для карточек игр
        row = 0
        col = 0
        max_cols = 4  # Количество карточек в ряду
        
        for game_name, game_info in self.installed_games.items():
            card = GameCard(self.games_frame, game_name, game_info, self)
            card.grid(row=row, column=col, padx=10, pady=10)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    launcher = ChokzLauncher()
    launcher.run()
