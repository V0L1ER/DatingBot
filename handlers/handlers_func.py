import os

from aiogram import Bot
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import InputMediaPhoto, InputMediaVideo
from dotenv import load_dotenv

import keyboards.inline_kb as in_kb
import keyboards.reply_kb as re_kb

from database.db import get_db_connection

load_dotenv('.env')
token = os.getenv('BOT_TOKEN')
bot = Bot(token)

async def menu_command(message, user_id):
    menu_command = await re_kb.get_menu_keyboard(user_id)
    await message.answer("Выберите что вас интересует", reply_markup=menu_command)
    
    
async def save_user_data(state, media_files, message):
    user_data = await state.get_data()
    
    user_photo = ','.join(media_files)
    user_id = user_data["user_id"]
    username = user_data["username"]
    user_first_name = user_data["user_first_name"]
    user_last_name = user_data["user_last_name"]
    name = user_data["name"]
    age = user_data["age"]
    city = user_data["city"]
    description = user_data["description"]
    sex = user_data["sex"]
    sex_interest = user_data["interest"]

    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        if sex == "Я Парень":
            await cursor.execute("""
                INSERT INTO boy_form (user_id, username, user_first_name, user_last_name, name, user_photo, age, city, description, sex, sex_interest) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, user_first_name, user_last_name, name, user_photo, age, city, description, sex, sex_interest))
        elif sex == "Я Девушка":
            await cursor.execute("""
                INSERT INTO girl_form (user_id, username, user_first_name, user_last_name, name, user_photo, age, city, description, sex, sex_interest) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, user_first_name, user_last_name, name, user_photo, age, city, description, sex, sex_interest))

        await conn.commit()
        await message.answer("Анкета успешно сохранена!", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"Ошибка при сохранении анкеты: {e}")
    finally:
        await cursor.close()
        await conn.close()
        
async def send_media_files(message, media_files, caption):
    if not media_files:
        await message.answer("У вас нет загруженных медиафайлов.")
        return

    # Функция для определения типа медиафайла
    async def determine_media_type(file_id):
        try:
            # Пробуем получить информацию о файле
            file = await message.bot.get_file(file_id)
            if file.file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                return 'photo'
            elif file.file_path.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                return 'video'
            else:
                # Пробуем отправить как фото
                try:
                    await message.bot.send_photo(chat_id=message.chat.id, photo=file_id)
                    return 'photo'
                except:
                    # Пробуем отправить как видео
                    try:
                        await message.bot.send_video(chat_id=message.chat.id, video=file_id)
                        return 'video'
                    except:
                        return None
        except:
            return None

    if len(media_files) == 1:
        file_id = media_files[0]
        media_type = await determine_media_type(file_id)
        if media_type == 'photo':
            await message.answer_photo(photo=file_id, caption=caption, parse_mode='HTML')
        elif media_type == 'video':
            await message.answer_video(video=file_id, caption=caption, parse_mode='HTML')
        else:
            await message.answer("Не удалось отправить медиафайл.")
    else:
        media_group = []
        for index, file_id in enumerate(media_files):
            media_type = await determine_media_type(file_id)
            if media_type == 'photo':
                if index == 0:
                    media_group.append(InputMediaPhoto(media=file_id, caption=caption, parse_mode='HTML'))
                else:
                    media_group.append(InputMediaPhoto(media=file_id))
            elif media_type == 'video':
                if index == 0:
                    media_group.append(InputMediaVideo(media=file_id, caption=caption, parse_mode='HTML'))
                else:
                    media_group.append(InputMediaVideo(media=file_id))
            else:
                await message.answer("Не удалось определить тип одного из медиафайлов.")
                return
        try:
            await message.answer_media_group(media_group)
        except Exception as e:
            await message.answer(f"Не удалось отправить медиагруппу. Ошибка: {e}")
                

async def send_message_to_user(message_text, target_user_id, sender_user_id, bot):
    # Добавляем кнопку для просмотра профиля отправителя
    keyboard = await in_kb.look_profile(sender_user_id)
    await bot.send_message(target_user_id, message_text, reply_markup=keyboard)
    
async def update_user_media(state, message):
    user_data = await state.get_data()
    user_id = message.from_user.id
    media_files = user_data.get('media_files', [])
    
    # Преобразуем список медиафайлов в строку, разделенную запятыми
    user_photo_str = ','.join(media_files)
    
    # Определяем таблицу на основе пола пользователя
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Получаем пол пользователя из базы данных
        await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
        sex_row = await cursor.fetchone()
        if sex_row:
            sex = sex_row[0]
        else:
            await message.answer("Не удалось определить ваш пол. Пожалуйста, заполните анкету заново.")
            return
        
        table_name = 'boy_form' if sex == 'Я Парень' else 'girl_form'
        
        # Обновляем медиафайлы в базе данных
        await cursor.execute(f"UPDATE {table_name} SET user_photo = ? WHERE user_id = ?", (user_photo_str, user_id))
        await conn.commit()
    
    await conn.close()

async def update_user_field(user_id, field_name, new_value):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Получаем пол пользователя
        await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
        sex_row = await cursor.fetchone()
        if sex_row:
            sex = sex_row[0]
        else:
            # Пользователь не найден
            return

        table_name = 'boy_form' if sex == 'Я Парень' else 'girl_form'

        # Обновляем указанное поле
        await cursor.execute(f"UPDATE {table_name} SET {field_name} = ? WHERE user_id = ?", (new_value, user_id))
        await conn.commit()
    await conn.close()
    
async def next_profile(message, state, user_id):
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    current_index += 1
    await state.update_data(current_index=current_index)
    await show_profile(message, state, user_id)
    
async def show_profile(message, state, user_id):
    data = await state.get_data()
    users_info = data.get('users_info', [])
    current_index = data.get('current_index', 0)

    if current_index >= len(users_info):
        menu_command = await re_kb.get_menu_keyboard(user_id)
        await message.answer("Больше нет анкет для просмотра.", reply_markup=menu_command)
        await state.clear()
        return

    user = users_info[current_index]
    target_user_id, name, user_photo_str, age, city, description = user

    media_files = [file_id.strip() for file_id in user_photo_str.split(',') if file_id.strip()] if user_photo_str else []
    caption = f"Имя: {name}\nВозраст: {age}\nГород: {city}\nОписание: {description}"

    await state.update_data(target_user_id=target_user_id)
    await send_media_files(message, media_files, caption)
    await message.answer("Выберите действие:", reply_markup=re_kb.view_profile)
    
async def show_user_profile(message):
    user_id = message.from_user.id
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Получаем пол пользователя из таблицы 'users'
        await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
        sex_row = await cursor.fetchone()
        if sex_row:
            sex = sex_row[0]
        else:
            await message.answer("Не удалось определить ваш пол. Пожалуйста, заполните анкету.", reply_markup=re_kb.start)
            await conn.close()
            return

        # Определяем таблицу на основе пола пользователя
        table = 'boy_form' if sex == "Я Парень" else 'girl_form'

        # Получаем информацию об анкете пользователя
        await cursor.execute(f"SELECT name, user_photo, age, city, description FROM {table} WHERE user_id = ?", (user_id,))
        user_info = await cursor.fetchone()

        if user_info:
            name, user_photo_str, age, city, description = user_info
            media_files = [file_id.strip() for file_id in user_photo_str.split(',') if file_id.strip()] if user_photo_str else []
            caption = f"Имя: {name}\nВозраст: {age}\nГород: {city}\nОписание: {description}"
            await send_media_files(message, media_files, caption)
        else:
            await message.answer("У вас еще нет анкеты. Пожалуйста, заполните анкету.", reply_markup=re_kb.start)
    await conn.close()