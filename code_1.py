import tkinter as tk
from tkinter import PhotoImage, messagebox
import json
import os
import hashlib
import time
import threading
import sys
from datetime import datetime, date, timedelta

BG_COLOR, FG_COLOR = '#6899D3', '#FFFFFF'
PRIMARY_COLOR, SECONDARY_COLOR = '#FFFFFF', '#87CEEB'
FONT_FAMILY, FONT_SIZE = 'Helvetica Neue', 14
FONT = (FONT_FAMILY, FONT_SIZE)
BOLD_FONT = (FONT_FAMILY, FONT_SIZE, 'bold')
DEFAULT_DAILY_GOAL, USERS_FILE, USER_DATA_PREFIX = 2000, 'users.json', 'user_data_'
REMINDER_INTERVAL = 3600

root = None
logged_in_username = None
daily_goal = DEFAULT_DAILY_GOAL  # Сколько надо выпить
water_drunk = 0  # Сколько уже выпили
progress_bar = None  # Прогресс
progress_label = None
last_reminder_time = 0
weight_entry = None
height_entry = None
canvas = None  # Холст для прогресс-бара, нужно сделать глобальным

def hash_password(password): # Создает нового и записывает его в файл с пользователями
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    hashed_password = hash_password(password)
    users = {}
    if os.path.exists(USERS_FILE):  # Если файл уже есть
        try:
            with open(USERS_FILE, 'r') as f:  # Открывает файл на чтение
                users = json.load(f)  # Загружает пользователей из файла
        except (json.JSONDecodeError, FileNotFoundError):
            users = {}
    users[username] = hashed_password  # Добавляет пользователя
    with open(USERS_FILE, 'w') as f:  # Открывает файл на запись
        json.dump(users, f)  # Записывает всех пользователей в файл
    messagebox.showinfo('Победа', 'Пользователь создан!')

def authenticate_user(username, password): # Проверяет на правильность
    if not os.path.exists(USERS_FILE):
        return False
    try:
        with open(USERS_FILE, 'r') as f:  # Открывает файл на чтение
            users = json.load(f)  # Загружает пользователей из файла
    except (json.JSONDecodeError, FileNotFoundError):
        return False  # Значит, пользователя нет
    return username in users and users[username] == hash_password(password)  # Проверяет логин и пароль

def show_login_register(): # Экран входа и регистрации
    global root, bot_image, main_frame, username_entry, password_entry, reg_username_entry, reg_password_entry, reg_password_confirm_entry, weight_entry, height_entry, progress_bar, progress_label, water_drunk_label, canvas

    for widget in main_frame.winfo_children():
        widget.destroy()

    try:
        bot_image = PhotoImage(file='bot.png')
        bot_image = bot_image.subsample(3, 3)  # Уменьшает картинку
    except tk.TclError:
        messagebox.showerror('Ошибка', 'Не удалось загрузить изображение')
        return

    image_label = tk.Label(main_frame, image=bot_image, background=BG_COLOR)
    image_label.pack(pady=(30, 15))

    title_label = tk.Label(main_frame, text='Водный баланс', font=('Helvetica Neue', 30, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
    title_label.pack(pady=(0, 40))

    def show_auth():
        for widget in main_frame.winfo_children():
            widget.destroy()

        username_label = tk.Label(main_frame, text='Имя:', font=('Helvetica Neue', 18, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
        username_label.pack(pady=(15, 5))
        username_entry = tk.Entry(main_frame, font=('Helvetica Neue', 18, 'bold'), bg='white', width=15, borderwidth=0)
        username_entry.pack(pady=(0, 20), padx=50, fill='x')

        password_label = tk.Label(main_frame, text='Пароль:', font=('Helvetica Neue', 18, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
        password_label.pack(pady=(5, 5))
        password_entry = tk.Entry(main_frame, show='*', font=('Helvetica Neue', 18, 'bold'), bg='white', width=15, borderwidth=0)
        password_entry.pack(pady=(0, 20), padx=50, fill='x')

        def login():
            global logged_in_username
            username = username_entry.get()
            password = password_entry.get()
            if authenticate_user(username, password):
                messagebox.showinfo('Победа', 'Вход выполнен!')
                logged_in_username = username  # Запоминает имя
                show_water_intake_window()
            else:
                messagebox.showerror('Ошибка', 'Неверный логин/пароль')

        def show_register():
            for widget in main_frame.winfo_children():
                widget.destroy()

            reg_username_label = tk.Label(main_frame, text='Имя:', font=('Helvetica Neue', 18, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
            reg_username_label.pack(pady=(15, 5))
            reg_username_entry = tk.Entry(main_frame, font=('Helvetica Neue', 18, 'bold'), bg='white', width=15, borderwidth=0)
            reg_username_entry.pack(pady=(0, 20), padx=50, fill='x')

            reg_password_label = tk.Label(main_frame, text='Пароль:', font=('Helvetica Neue', 18, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
            reg_password_label.pack(pady=(5, 5))
            reg_password_entry = tk.Entry(main_frame, show='*', font=('Helvetica Neue', 18, 'bold'), bg='white', width=15, borderwidth=0)
            reg_password_entry.pack(pady=(0, 20), padx=50, fill='x')

            reg_password_confirm_label = tk.Label(main_frame, text='Подтвердите:', font=('Helvetica Neue', 18, 'bold'), bg=BG_COLOR, fg=FG_COLOR)
            reg_password_confirm_label.pack(pady=(5, 5))
            reg_password_confirm_entry = tk.Entry(main_frame, show='*', font=('Helvetica Neue', 18, 'bold'), bg='white', width=15, borderwidth=0)
            reg_password_confirm_entry.pack(pady=(0, 20), padx=50, fill='x')

            def register():
                username = reg_username_entry.get()
                password = reg_password_entry.get()
                if password != reg_password_confirm_entry.get():
                    messagebox.showerror('Ошибка', 'Пароли не совпадают')
                    return  # Выходим
                if user_exists(username):
                    messagebox.showerror('Ошибка', 'Данное имя уже занято')
                    return

                create_user(username, password)
                show_auth()

            register_button = tk.Button(main_frame, text='Зарегистрироваться', command=register, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
            register_button.pack(pady=10)

            login_auth_button = tk.Button(main_frame, text='Назад к входу', command=show_auth, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
            login_auth_button.pack(pady=10)

        login_button = tk.Button(main_frame, text='Войти', command=login, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
        login_button.pack(pady=10)

        register_button = tk.Button(main_frame, text='Регистрация', command=show_register, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
        register_button.pack(pady=10)

    show_auth_button = tk.Button(main_frame, text='Старт', command=show_auth, bg=PRIMARY_COLOR, fg=BG_COLOR, font=('Helvetica Neue', 12, 'bold'), borderwidth=0, padx=20, pady=8)
    show_auth_button.pack(pady=30)

def save_user_data(username, weight, height, goal=None, water_drunk=None):
    filename = f'{USER_DATA_PREFIX}{username}.json'
    try:
        with open(filename, 'r') as f:
            try:
                user_data = json.load(f)
            except json.JSONDecodeError:
                user_data = {}
    except FileNotFoundError:
        user_data = {}

    user_data['weight'] = weight
    user_data['height'] = height
    user_data['daily_goal'] = goal or daily_goal
    if water_drunk is not None:
        user_data['water_drunk'] = water_drunk

    today = date.today().strftime("%Y-%m-%d")  # Сохраняет ежедневные записи
    if 'daily_records' not in user_data:
        user_data['daily_records'] = {}
    user_data['daily_records'][today] = user_data.get('water_drunk', 0)

    with open(filename, 'w') as f:
        json.dump(user_data, f)

def load_user_data(username):
    global weight_entry, height_entry, daily_goal, water_drunk, canvas

    filename = f'{USER_DATA_PREFIX}{username}.json'
    if not os.path.exists(filename):
        return

    try:
        with open(filename, 'r') as f:
            user_data = json.load(f)

            global daily_goal, water_drunk # Обновляет глобальные переменные
            daily_goal = user_data.get('daily_goal', DEFAULT_DAILY_GOAL)
            water_drunk = user_data.get('water_drunk', 0)

            return user_data # Возвращает данные для использования
    except (json.JSONDecodeError, FileNotFoundError):
        messagebox.showerror('Ошибка', 'Ошибка чтения данных пользователя')
        return None

def calculate_water_intake(weight):
    return weight * 30 if weight > 0 else None

def record_bottles():
    global water_drunk, logged_in_username, bottles_entry, daily_goal

    def save_bottles():
        global water_drunk
        num_bottles_str = bottles_entry.get()  # Получает количество бутылок
        if not num_bottles_str.isdigit():
            messagebox.showerror('Ошибка', 'Введите число бутылок')
            return

        num_bottles = int(num_bottles_str)
        added_water = num_bottles * 500
        water_drunk += added_water
        weight = weight_entry.get() # Получаем вес и рост из полей ввода
        height = height_entry.get() 

        if not weight or not weight.replace('.', '', 1).isdigit() or not height or not height.replace('.', '', 1).isdigit():  # Проверяет, что вес и рост введены верно
            messagebox.showerror('Ошибка', 'Введите корректные значения для веса и роста')
            return
            
        save_user_data(logged_in_username, weight, height, daily_goal, water_drunk) # Сохраняет новые данные
        update_progress()  # Обновляем прогресс
        messagebox.showinfo('Успех', f'Записано {num_bottles} бутылок(-ки)!')
        show_water_intake_window()

    bottles_label = tk.Label(main_frame, text='Выпито бутылок (0.5 л):', font=FONT, bg=BG_COLOR, fg=FG_COLOR)
    bottles_label.pack(pady=5)
    bottles_entry = tk.Entry(main_frame, font=FONT, bg='white', width=15, borderwidth=0)
    bottles_entry.pack(pady=5, padx=30, fill='x')

    save_button = tk.Button(main_frame, text='Записать', command=save_bottles, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT)
    save_button.pack(pady=10)

def calculate_and_show():
    global weight_entry, height_entry
    weight_str = weight_entry.get()
    height_str = height_entry.get()

    if not weight_str or not weight_str.replace('.', '', 1).isdigit() or not height_str or not height_str.replace('.', '', 1).isdigit():
        messagebox.showerror('Ошибка', 'Введите корректные данные')
        return

    weight = float(weight_str)
    height = float(height_str)

    if weight <= 0:
        messagebox.showerror('Ошибка', 'Введите корректный вес')
        return

    recommended_intake = calculate_water_intake(weight)

    if recommended_intake is not None:
        messagebox.showinfo('Результат', f'Рекомендуемая норма: {recommended_intake:.0f} мл')
    else:
        messagebox.showerror('Ошибка', 'Невозможно рассчитать')

def set_daily_goal():
    global daily_goal, logged_in_username, goal_entry

    def save_goal():
        global daily_goal
        new_goal_str = goal_entry.get()
        if new_goal_str.isdigit():
            new_goal = int(new_goal_str)
            if new_goal > 0:
                daily_goal = new_goal
                weight = weight_entry.get()  # Получает вес и рост
                height = height_entry.get()
                save_user_data(logged_in_username, weight, height, new_goal)
                update_progress()
                show_water_intake_window()
            else:
                messagebox.showerror('Ошибка', 'Цель должна быть положительным числом')
        else:
            messagebox.showerror('Ошибка', 'Введите числовое значение')

    goal_label = tk.Label(main_frame, text='Дневная цель (мл):', font=FONT, bg=BG_COLOR, fg=FG_COLOR)
    goal_label.pack(pady=5)
    goal_entry = tk.Entry(main_frame, font=FONT, bg='white', width=15, borderwidth=0)
    goal_entry.pack(pady=5, padx=30, fill='x')

    save_button = tk.Button(main_frame, text='Сохранить', command=save_goal, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
    save_button.pack(pady=10)

def update_progress():
    global water_drunk, daily_goal, progress_bar, progress_label, canvas

    if daily_goal == 0:
        progress = 0
    else:
        progress = min(100, (water_drunk / daily_goal) * 100)

    if progress_bar:
        update_circular_progress(progress)
    if progress_label:
        progress_label.config(text=f'Прогресс: {progress:.1f}%')

def show_water_intake_window():
    global root, main_frame, weight_entry, height_entry, progress_bar, progress_label, water_drunk_label, canvas, bottle_image, logged_in_username, daily_goal, water_drunk

    for widget in main_frame.winfo_children():
        widget.destroy()

    input_frame = tk.Frame(main_frame, bg=BG_COLOR)
    input_frame.pack(pady=20)

    weight_label = tk.Label(input_frame, text='Вес (кг):', font=FONT, bg=BG_COLOR, fg=FG_COLOR)
    weight_label.grid(row=0, column=0, sticky='e', padx=(20, 10), pady=10)
    weight_entry = tk.Entry(input_frame, font=FONT, bg='white', width=8, borderwidth=0)
    weight_entry.grid(row=0, column=1, sticky='w', padx=(10, 20), pady=10)

    height_label = tk.Label(input_frame, text='Рост (см):', font=FONT, bg=BG_COLOR, fg=FG_COLOR)
    height_label.grid(row=1, column=0, sticky='e', padx=(20, 10), pady=10)
    height_entry = tk.Entry(input_frame, font=FONT, bg='white', width=8, borderwidth=0)
    height_entry.grid(row=1, column=1, sticky='w', padx=(10, 20), pady=10)

    try:
        bottle_image = PhotoImage(file='bottless.png')
        bottle_image = bottle_image.subsample(3, 3)
    except tk.TclError:
        messagebox.showerror('Ошибка')
        return

    def show_bottle_menu(event=None):
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label='Вернуться ко входу и удалить данные', command=reset_and_show_login, background=BG_COLOR, foreground=FG_COLOR)
        menu.add_command(label='Посмотреть статистику', command=show_stats, background=BG_COLOR, foreground=FG_COLOR)
        try: 
            menu.tk_popup(event.x_root, event.y_root)  # Показ меню где кликнули
        except AttributeError:
            menu.tk_popup(main_frame.winfo_rootx() + 50, main_frame.winfo_rooty() + 50)

    bottle_label = tk.Label(main_frame, image=bottle_image, bg=BG_COLOR) # Картинка бутылки
    bottle_label.place(x=0, y=0)
    bottle_label.bind('<Button-1>', show_bottle_menu)

    button_frame = tk.Frame(main_frame, bg=BG_COLOR)
    button_frame.pack(pady=10)

    calculate_button = tk.Button(button_frame, text='Рассчитать', command=calculate_and_show, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
    calculate_button.pack(side=tk.LEFT, padx=5)

    record_button = tk.Button(button_frame, text='Записать выпитое', command=record_bottles, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
    record_button.pack(side=tk.LEFT, padx=5)

    set_goal_button = tk.Button(button_frame, text='Установить цель', command=set_daily_goal, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT, borderwidth=0, padx=20, pady=8)
    set_goal_button.pack(side=tk.LEFT, padx=5)

    canvas_width = 200
    canvas_height = 200  # Холст для прогресс-бара
    global canvas
    canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(pady=20)
    global progress_bar
    progress_bar = canvas
    create_circular_progress(canvas, 100, 100, 80, 10, PRIMARY_COLOR)  # Инициализирует прогресс-бар

    progress_label = tk.Label(main_frame, text='Прогресс: 0%', font=BOLD_FONT, bg=BG_COLOR, fg=FG_COLOR)
    progress_label.pack(pady=5)

    water_drunk_label = tk.Label(main_frame, text=f'Выпито: {water_drunk} мл', font=FONT, bg=BG_COLOR, fg=FG_COLOR)
    water_drunk_label.pack(pady=5)

    user_data = load_user_data(logged_in_username)  # Загружает данные и инициализирует значения
    if user_data:
        weight_entry.insert(0, str(user_data.get('weight', '')))
        height_entry.insert(0, str(user_data.get('height', '')))
        daily_goal = user_data.get('daily_goal', DEFAULT_DAILY_GOAL)
        water_drunk = user_data.get('water_drunk', 0)
        update_progress()  # Обновляет прогресс-бар с данными

def user_exists(username):
    if not os.path.exists(USERS_FILE):
        return False
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return False
    return username in users

def reminder_thread():
    global last_reminder_time, logged_in_username
    while True:
        now = time.time()
        if logged_in_username and now - last_reminder_time >= REMINDER_INTERVAL:
            root.after(0, show_reminder)
            last_reminder_time = now
        time.sleep(60)

def show_reminder():
    messagebox.showinfo('Напоминание', 'Пора выпить воды!')
    global last_reminder_time
    last_reminder_time = time.time()

def create_circular_progress(canvas, x, y, radius, width, color):
    start_angle = 90
    extent = 0
    canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=start_angle, extent=extent, width=width, style=tk.ARC, outline=color, tags='progress_arc')

def update_circular_progress(progress):
    global progress_bar, canvas
    if not canvas:
        return  # Если холст не создан, выходит

    x = 100
    y = 100
    radius = 80
    width = 10

    extent = -359.999 * (progress / 100)
    canvas.delete('progress_arc')  # Удаляет только дугу с прогрессом
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=SECONDARY_COLOR, width=3, tags='progress_arc')
    canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=90, extent=extent, width=width, style=tk.ARC, outline=PRIMARY_COLOR, tags='progress_arc')

def reset_and_show_login():
    global logged_in_username, water_drunk, daily_goal

    water_drunk = 0
    daily_goal = DEFAULT_DAILY_GOAL

    if logged_in_username:
        save_user_data(logged_in_username, '', '', daily_goal, water_drunk)

    logged_in_username = None
    show_login_register()
    logged_in_username = None
    show_login_register()

def show_stats():
    global logged_in_username, main_frame

    root.iconbitmap('in.ico')
    user_data = load_user_data(logged_in_username)
    if not user_data or 'daily_records' not in user_data:
        messagebox.showinfo('Статистика', 'Нет данных для отображения')
        return

    daily_records = user_data['daily_records']

    today = date.today()
    weekly_total = 0
    weekly_data = []
    for i in range(7):
        current_date = today - timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str in daily_records:
            weekly_total += daily_records[date_str]
            weekly_data.append(f'{date_str}: {daily_records[date_str]} мл')
        else:
            weekly_data.append(f'{date_str}: 0 мл')

    monthly_total = 0
    monthly_data = []
    first_day_month = date(today.year, today.month, 1)  # Первый день текущего месяца
    for i in range((today - first_day_month).days + 1):
        current_date = first_day_month + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str in daily_records:
            monthly_total += daily_records[date_str]
            monthly_data.append(f'{date_str}: {daily_records[date_str]} мл')
        else:
            monthly_data.append(f'{date_str}: 0 мл')

    stats_window = tk.Toplevel(root)
    stats_window.title('Статистика')
    stats_window.configure(bg=BG_COLOR)
    stats_window.geometry('520x520')
    stats_window.iconbitmap('in.ico')

    weekly_label = tk.Label(stats_window, text='Статистика за неделю:', font=BOLD_FONT, bg=BG_COLOR, fg=FG_COLOR)
    weekly_label.pack(pady=5)

    weekly_text = tk.Text(stats_window, height=7, width=30, bg='white', fg='black')
    weekly_text.pack(pady=5)
    weekly_text.insert(tk.END, '\n'.join(reversed(weekly_data)))
    weekly_text.insert(tk.END, f'\nИтого за неделю: {weekly_total} мл')
    weekly_text.config(state=tk.DISABLED)

    monthly_label = tk.Label(stats_window, text='Статистика за месяц:', font=BOLD_FONT, bg=BG_COLOR, fg=FG_COLOR)
    monthly_label.pack(pady=5)

    monthly_text = tk.Text(stats_window, height=7, width=30, bg='white', fg='black')
    monthly_text.pack(pady=5)
    monthly_text.insert(tk.END, '\n'.join(reversed(monthly_data)))
    monthly_text.insert(tk.END, f'\nИтого за месяц: {monthly_total} мл')
    monthly_text.config(state=tk.DISABLED)

    close_button = tk.Button(stats_window, text='Закрыть', command=stats_window.destroy, bg=PRIMARY_COLOR, fg=BG_COLOR, font=FONT)
    close_button.pack(pady=10)

root = tk.Tk()
root.title('Водный баланс')
root.geometry('620x740')
root.configure(bg=BG_COLOR)
root.resizable(False, False)

main_frame = tk.Frame(root, bg=BG_COLOR, padx=30, pady=30)
main_frame.pack(fill='both', expand=True)

show_login_register()

reminder_thread_obj = threading.Thread(target=reminder_thread, daemon=True)
reminder_thread_obj.start()

root.iconbitmap('in.ico')

def close():
    global logged_in_username, weight_entry, height_entry, daily_goal, water_drunk

    if logged_in_username:
        try:
            weight = weight_entry.get()
            height = height_entry.get()
            save_user_data(logged_in_username, weight, height, daily_goal, water_drunk) # Сохраняет данные
        except NameError:
            pass
    root.destroy()

root.protocol('WM_DELETE_WINDOW', close)

root.mainloop()
