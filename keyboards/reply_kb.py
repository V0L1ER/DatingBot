from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.db import get_db_connection

start = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Заполнить анкету")]
], resize_keyboard=True, input_field_placeholder="Выберите что вас интересует...")

async def get_menu_keyboard(user_id):
    # Получаем статус пользователя из базы данных
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
        status_row = await cursor.fetchone()
        if status_row:
            status = status_row[0]
        else:
            # Если статус не найден, по умолчанию считаем, что анкета включена
            status = 'Включено'
    await conn.close()
    
    # Формируем кнопки меню
    buttons = [
        [KeyboardButton(text="Смотреть анкеты"), KeyboardButton(text="Заполнить анкету заново")],
        [KeyboardButton(text="Изменить фото/видео анкеты"), KeyboardButton(text="Изменить текст анкеты")],
        [KeyboardButton(text="Привязать инстаграм")]
    ]
    
    # Добавляем кнопку в зависимости от статуса
    if status == 'Включено':
        buttons.append([KeyboardButton(text="Отключить анкету")])
    else:
        buttons.append([KeyboardButton(text="Включить анкету")])
    
    menu_command = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите что вас интересует..."
    )
    
    return menu_command

sex = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Я Парень"), KeyboardButton(text="Я Девушка")]
], resize_keyboard=True, input_field_placeholder="Выберите что вас интересует...")

sex_interest = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Парни"), KeyboardButton(text="Девушки"), KeyboardButton(text="Все равно")]
], resize_keyboard=True, input_field_placeholder="Выберите что вас интересует...")

dann = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Готово")]
], resize_keyboard=True, input_field_placeholder="Выберите что вас интересует...")

view_profile = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="👍"), KeyboardButton(text="✉️/📹"), KeyboardButton(text="👎"), KeyboardButton(text="💤")]
], resize_keyboard=True, input_field_placeholder="Выберите что вас интересует...")

edit_text_options = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Изменить имя")],
        [KeyboardButton(text="Изменить возраст")],
        [KeyboardButton(text="Изменить город")],
        [KeyboardButton(text="Изменить описание")],
        [KeyboardButton(text="Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)