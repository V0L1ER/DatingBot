from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo
from datetime import datetime

import json

import keyboards.inline_kb as in_kb
import keyboards.reply_kb as re_kb
import handlers.handlers_func as hf

from database.db import get_db_connection

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    time_added = datetime.now()

    time_added_str = time_added.strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            # Проверяем, есть ли пользователь в таблице 'users'
            await cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            user_exists = await cursor.fetchone()
            if user_exists is None:
                # Если пользователя нет, добавляем его
                await cursor.execute("""
                    INSERT INTO users (user_id, username, time_added) VALUES (?, ?, ?)
                """, (user_id, username, time_added_str))
                await conn.commit()
                await message.answer(
                    "Привет! Я бот для знакомств. Я помогу тебе найти себе собеседника или что-то больше:)",
                    reply_markup=re_kb.start
                )
            else:
                # Пользователь существует, получаем его пол
                await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
                sex_result = await cursor.fetchone()
                sex = sex_result[0] if sex_result else None
                await message.answer("Ваша анкета:")
                if sex == "Я Парень":
                    # Получаем анкету пользователя из таблицы 'boy_form'
                    await cursor.execute("SELECT name, user_photo, age, city, description FROM boy_form WHERE user_id = ?", (user_id,))
                    user_info = await cursor.fetchone()
                    if user_info:
                        name, user_photo_str, age, city, description = user_info

                        # Обрабатываем и отправляем медиафайлы
                        if user_photo_str:
                            media_files = [file_id.strip() for file_id in user_photo_str.split(',') if file_id.strip()]
                        else:
                            media_files = []

                        # Создаем подпись с информацией об анкете
                        caption = f"Имя: {name}\nВозраст: {age}\nГород: {city}\nОписание: {description}"
                        menu_command = await re_kb.get_menu_keyboard(user_id)
                        await hf.send_media_files(message, media_files, caption)
                        await message.answer("Выберите что вам нужно:", reply_markup=menu_command)

                    else:
                        await message.answer(
                            "У вас еще нет анкеты. Пожалуйста, заполните анкету.",
                            reply_markup=re_kb.start
                        )
                elif sex == "Я Девушка":
                    # Получаем анкету пользователя из таблицы 'girl_form'
                    await cursor.execute("SELECT name, user_photo, age, city, description FROM girl_form WHERE user_id = ?", (user_id,))
                    user_info = await cursor.fetchone()
                    await message.answer("Ваша анкета:")
                    if user_info:
                        name, user_photo_str, age, city, description = user_info

                        # Обрабатываем и отправляем медиафайлы
                        if user_photo_str:
                            media_files = [file_id.strip() for file_id in user_photo_str.split(',') if file_id.strip()]
                        else:
                            media_files = []

                        # Создаем подпись с информацией об анкете
                        caption = f"Имя: {name}\nВозраст: {age}\nГород: {city}\nОписание: {description}"
                        menu_command = await re_kb.get_menu_keyboard(user_id)
                        await hf.send_media_files(message, media_files, caption)
                        await message.answer("Выберите что вам нужно:", reply_markup=menu_command)

                    else:
                        await message.answer(
                            "У вас еще нет анкеты. Пожалуйста, заполните анкету.",
                            reply_markup=re_kb.start
                        )
                else:
                    # Пол не указан или некорректен
                    await message.answer(
                        "У вас еще нет анкеты. Пожалуйста, заполните анкету.",
                        reply_markup=re_kb.start
                    )
        await conn.close()
        
    except Exception as ex:
        print(ex)
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message(Command('myprofile'))
async def cmd_myprofile(message: Message):
    pass
