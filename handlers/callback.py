import random

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

import keyboards.inline_kb as in_kb
import keyboards.reply_kb as re_kb
import handlers.handlers_func as hf
from database.db import get_db_connection

call_router = Router()

class SetInfo(StatesGroup):
    waiting_age = State()
    waiting_sex = State()
    waiting_interest = State()
    waiting_from = State()
    waiting_name = State()
    waiting_description = State()
    waiting_profile_media = State()
    updating_profile_media = State()
    updating_text_choice = State() 
    updating_name = State()
    updating_age = State()
    updating_city = State()
    updating_description = State()


@call_router.message(F.text == "Заполнить анкету")
async def full_form(message: Message, state: FSMContext):
    await state.set_state(SetInfo.waiting_age)
    await message.answer("Сколько тебе лет?", reply_markup=ReplyKeyboardRemove())

@call_router.message(SetInfo.waiting_age)
async def age(message: Message, state: FSMContext):
    age = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name or "Отсутствует"
    
    if not age.isdigit():
        await message.answer("Вы ввели не число!")
        return
    
    age = int(age)
    
    if age < 16:
        await message.answer("Бот разрешен только людям старше 16 лет:) Возвращайся когда тебе будет 16!")
        
    await state.update_data(age = age)
    await state.update_data(user_id = user_id)
    await state.update_data(username = username)
    await state.update_data(user_first_name = user_first_name)
    await state.update_data(user_last_name = user_last_name)
    await state.set_state(SetInfo.waiting_sex)
    
    await message.answer("Теперь выберем пол:", reply_markup=re_kb.sex)

@call_router.message(SetInfo.waiting_sex)
async def sex(message: Message, state: FSMContext):
    sex = message.text.strip()
    
    if sex not in ["Я Парень", "Я Девушка"]:
        await message.answer("Не нужно писать ничего в чат, просто нажмите на кнопочку:)", reply_markup=re_kb.sex)
        return
    
    await state.update_data(sex=sex)
    
    # Обновляем поле 'sex' в таблице 'users'
    user_id = message.from_user.id
    conn = await get_db_connection()
    cursor = await conn.cursor()
    await cursor.execute("UPDATE users SET sex = ? WHERE user_id = ?", (sex, user_id))
    await conn.commit()
    await cursor.close()
    await conn.close()
    
    await state.set_state(SetInfo.waiting_interest)
    await message.answer("Кто тебя интересует?", reply_markup=re_kb.sex_interest)

@call_router.message(SetInfo.waiting_interest)
async def interest(message: Message, state: FSMContext):
    interest = message.text.strip()
    
    if interest not in ["Парни", "Девушки", "Все равно"]:
        await message.answer("Не нужно писать ничего в чат, просто нажмите на кнопочку:)", reply_markup=re_kb.sex_interest)
        return
    
    await state.update_data(interest = interest)
    await state.set_state(SetInfo.waiting_from)
    
    await message.answer("С какого ты города?", reply_markup=ReplyKeyboardRemove())
    
@call_router.message(SetInfo.waiting_from)
async def city(message: Message, state: FSMContext):
    city = message.text.strip()
    
    await state.update_data(city = city)
    await state.set_state(SetInfo.waiting_name)
    
    await message.answer("Как к тебе обращаться?")
    
@call_router.message(SetInfo.waiting_name)
async def name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    await state.update_data(name = name)
    await state.set_state(SetInfo.waiting_description)
    
    await message.answer("Расскажи о себе, кого хочеш найти, чем планируешь заняться. Это поможет тебе найти компанию.")
   
@call_router.message(SetInfo.waiting_description)
async def description(message: Message, state: FSMContext):
    description = message.text.strip()
    
    await state.update_data(description = description)
    await state.set_state(SetInfo.waiting_profile_media)
    
    await message.answer("Теперь отправь фото или запиши видео (до 15 сек.). Можно отправить до 3 медиафайлов. Когда закончишь, напиши или нажми 'Готово'.", reply_markup=re_kb.dann)

    
@call_router.message(SetInfo.waiting_profile_media)
async def media(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Получаем текущий список медиафайлов или инициализируем его
    media_files = user_data.get('media_files', [])
    
    # Проверяем, написал ли пользователь 'Готово'
    if message.text and message.text.strip().lower() == 'готово':
        if not media_files:
            await message.answer("Вы не отправили ни одного медиафайла. Пожалуйста, отправьте фото или видео.")
            return
        
        # Сохранение данных в базу данных
        await hf.save_user_data(state, media_files, message)
        await state.clear()
        return
    
    # Обработка входящих медиафайлов
    if message.photo:
        if len(media_files) >= 3:
            await message.answer("Вы уже отправили максимальное количество медиафайлов.")
            return
        photo_id = message.photo[-1].file_id
        media_files.append(photo_id)
    elif message.video:
        if len(media_files) >= 3:
            await message.answer("Вы уже отправили максимальное количество медиафайлов.")
            return
        if message.video.duration > 15:
            await message.answer("Видео слишком длинное. Пожалуйста, отправьте видео не длиннее 15 секунд.")
            return
        video_id = message.video.file_id
        media_files.append(video_id)
    else:
        await message.answer("Пожалуйста, отправьте фото или видео.")
        return
    
    # Обновляем список медиафайлов в состоянии
    await state.update_data(media_files=media_files)
    
    if len(media_files) >= 3:
        # Сохранение данных в базу данных
        await hf.save_user_data(state, media_files, message)
        await state.clear()
    else:
        remaining = 3 - len(media_files)
        await message.answer(f"Медиафайл сохранен. Вы можете отправить еще {remaining} файл(а). Когда закончите, напиши или нажми 'Готово'.", reply_markup=re_kb.dann)

@call_router.message(F.text == 'Заполнить анкету заново')
async def edit_form(message: Message, state: FSMContext):
    await state.set_state(SetInfo.waiting_age)
    await message.answer("Сколько тебе лет?", reply_markup=ReplyKeyboardRemove())
    
@call_router.message(F.text == 'Смотреть анкеты')
async def view_profiles(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            # Получаем пол пользователя
            await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
            sex_row = await cursor.fetchone()
            if sex_row:
                sex = sex_row[0]
            else:
                await message.answer("Не удалось определить ваш пол. Пожалуйста, заполните анкету.", reply_markup=re_kb.start)
                return

            # Определяем таблицу с противоположным полом
            if sex == "Я Парень":
                opposite_table = 'girl_form'
            elif sex == "Я Девушка":
                opposite_table = 'boy_form'
            else:
                await message.answer("Ваш пол указан некорректно. Пожалуйста, заполните анкету заново.", reply_markup=re_kb.start)
                return

            # Получаем анкеты противоположного пола, у которых статус 'Включено'
            await cursor.execute(f"""
                SELECT u.user_id, f.name, f.user_photo, f.age, f.city, f.description
                FROM {opposite_table} f
                JOIN users u ON f.user_id = u.user_id
                WHERE u.status = 'Включено' AND u.user_id != ?
            """, (user_id,))
            users_info = await cursor.fetchall()

            if not users_info:
                await message.answer("К сожалению, нет доступных анкет для просмотра.")
                return

            # Перемешиваем список анкет
            users_info = list(users_info)
            random.shuffle(users_info)

            # Сохраняем список анкет и текущий индекс в состоянии
            await state.update_data(users_info=users_info, current_index=0)

            # Показываем первую анкету
            await hf.show_profile(message, state, user_id)
    except Exception as ex:
        print(ex)
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        await conn.close()
        
@call_router.message(F.text == "👍")
async def like(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        await message.answer("Ошибка: не удалось определить пользователя для лайка.")
        return

    # Отправляем уведомление целевому пользователю
    message_text = "Вам поставили лайк! 💖"
    await hf.send_message_to_user(message_text, target_user_id, user_id, message.bot)

    await message.answer("Вы поставили лайк!")

    # Переходим к следующей анкете
    await hf.next_profile(message, state, user_id)


@call_router.message(F.text == "✉️/📹")
async def contact_request(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        await message.answer("Ошибка: не удалось определить пользователя для связи.")
        return

    # Получаем информацию о текущем пользователе
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Получаем имя пользователя из его анкеты
        await cursor.execute("SELECT name FROM boy_form WHERE user_id = ?", (user_id,))
        user_info = await cursor.fetchone()
        if not user_info:
            await cursor.execute("SELECT name FROM girl_form WHERE user_id = ?", (user_id,))
            user_info = await cursor.fetchone()

        if user_info:
            user_name = user_info[0]
        else:
            user_name = "Пользователь"

    await conn.close()

    # Отправляем сообщение целевому пользователю
    message_text = f"Пользователь {user_name} хочет связаться с вами! ✉️"
    await hf.send_message_to_user(message_text, target_user_id, user_id, message.bot)

    await message.answer("Ваш запрос на связь отправлен!")

    # Переходим к следующей анкете
    await hf.next_profile(message, state, user_id)

    
@call_router.message(F.text == "👎")
async def dislike(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer("Анкета пропущена.")

    # Переходим к следующей анкете
    await hf.next_profile(message, state, user_id)

    
@call_router.message(F.text == "💤")
async def stop_viewing(message: Message, state: FSMContext):
    user_id = message.from_user.id
    menu_command = await re_kb.get_menu_keyboard(user_id)
    await state.clear()
    await message.answer("Просмотр анкет завершен. Вот ваша анкета:", reply_markup=menu_command)
    await hf.show_user_profile(message)

    
@call_router.callback_query(F.data.startswith("look/"))
async def look_profile_call(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('/')
    user_id = data[1]

    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Получаем пол пользователя из таблицы 'users'
        await cursor.execute("SELECT sex FROM users WHERE user_id = ?", (user_id,))
        sex_row = await cursor.fetchone()
        if sex_row:
            sex = sex_row[0]
        else:
            await callback.message.answer("Не удалось определить пол пользователя.")
            await conn.close()
            await callback.answer()
            return

        # Определяем таблицу на основе пола пользователя
        table = 'boy_form' if sex == "Я Парень" else 'girl_form'

        # Получаем информацию об анкете пользователя
        await cursor.execute(f"SELECT name, user_photo, age, city, description FROM {table} WHERE user_id = ?", (user_id,))
        user_info = await cursor.fetchone()

        if user_info:
            profile_link = f"tg://user?id={user_id}"
            name, user_photo_str, age, city, description = user_info
            media_files = [file_id.strip() for file_id in user_photo_str.split(',') if file_id.strip()] if user_photo_str else []
            caption = f"Имя: {name}\nВозраст: {age}\nГород: {city}\nОписание: {description}"
            await hf.send_media_files(callback.message, media_files, caption)
        else:
            await callback.message.answer("Не удалось получить информацию о пользователе.")
    await conn.close()
    await callback.answer()
    
@call_router.message(F.text == 'Изменить фото/видео анкеты')
async def edit_photo_video_form(message: Message, state: FSMContext):
    # Устанавливаем новое состояние
    await state.set_state(SetInfo.updating_profile_media)
    # Очищаем предыдущие медиафайлы из состояния
    await state.update_data(media_files=[])
    # Отправляем инструкцию пользователю
    await message.answer(
        "Отправьте новые фото или видео для вашей анкеты (до 3 медиафайлов). Когда закончите, напишите или нажмите 'Готово'.",
        reply_markup=re_kb.dann
    )

@call_router.message(SetInfo.updating_profile_media)
async def update_media(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id
    
    # Получаем текущий список медиафайлов или инициализируем его
    media_files = user_data.get('media_files', [])
    
    # Проверяем, написал ли пользователь 'Готово'
    if message.text and message.text.strip().lower() == 'готово':
        if not media_files:
            await message.answer("Вы не отправили ни одного медиафайла. Пожалуйста, отправьте фото или видео.")
            return
        
        menu_command = await re_kb.get_menu_keyboard(user_id)
        await hf.update_user_media(state, message)
        await state.clear()
        await message.answer("Ваши фото/видео успешно обновлены!", reply_markup=menu_command)
        return
    
    # Обработка входящих медиафайлов
    if message.photo:
        if len(media_files) >= 3:
            await message.answer("Вы уже отправили максимальное количество медиафайлов.")
            return
        photo_id = message.photo[-1].file_id
        media_files.append(photo_id)
    elif message.video:
        if len(media_files) >= 3:
            await message.answer("Вы уже отправили максимальное количество медиафайлов.")
            return
        if message.video.duration > 15:
            await message.answer("Видео слишком длинное. Пожалуйста, отправьте видео не длиннее 15 секунд.")
            return
        video_id = message.video.file_id
        media_files.append(video_id)
    else:
        await message.answer("Пожалуйста, отправьте фото или видео.")
        return
    
    # Обновляем список медиафайлов в состоянии
    await state.update_data(media_files=media_files)
    
    if len(media_files) >= 3:
        menu_command = await re_kb.get_menu_keyboard(user_id)
        await hf.update_user_media(state, message)
        await state.clear()
        await message.answer("Ваши фото/видео успешно обновлены!", reply_markup=menu_command)
    else:
        remaining = 3 - len(media_files)
        await message.answer(f"Медиафайл сохранен. Вы можете отправить еще {remaining} файл(а). Когда закончите, напишите или нажмите 'Готово'.", reply_markup=re_kb.dann)
        
@call_router.message(F.text == 'Изменить текст анкеты')
async def edit_text_form(message: Message, state: FSMContext):
    # Спрашиваем, что пользователь хочет изменить
    await message.answer(
        "Что вы хотите изменить?",
        reply_markup=re_kb.edit_text_options  # Клавиатура с вариантами
    )
    # Устанавливаем состояние ожидания выбора поля для обновления
    await state.set_state(SetInfo.updating_text_choice)
    
@call_router.message(SetInfo.updating_text_choice)
async def process_text_update_choice(message: Message, state: FSMContext):
    choice = message.text.strip()
    user_id = message.from_user.id
    if choice == "Изменить имя":
        await state.set_state(SetInfo.updating_name)
        await message.answer("Пожалуйста, введите новое имя:", reply_markup=ReplyKeyboardRemove())
    elif choice == "Изменить возраст":
        await state.set_state(SetInfo.updating_age)
        await message.answer("Пожалуйста, введите новый возраст:", reply_markup=ReplyKeyboardRemove())
    elif choice == "Изменить город":
        await state.set_state(SetInfo.updating_city)
        await message.answer("Пожалуйста, введите новый город:", reply_markup=ReplyKeyboardRemove())
    elif choice == "Изменить описание":
        await state.set_state(SetInfo.updating_description)
        await message.answer("Пожалуйста, введите новое описание:", reply_markup=ReplyKeyboardRemove())
    elif choice == "Отмена":
        menu_command = await re_kb.get_menu_keyboard(user_id)
        await state.clear()
        await message.answer("Редактирование отменено.", reply_markup=menu_command)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.", reply_markup=re_kb.edit_text_options)
        
@call_router.message(SetInfo.updating_name)
async def update_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    user_id = message.from_user.id

    menu_command = await re_kb.get_menu_keyboard(user_id)
    await hf.update_user_field(user_id, 'name', new_name)
    await state.clear()
    await message.answer("Ваше имя успешно обновлено!", reply_markup=menu_command)
    
@call_router.message(SetInfo.updating_age)
async def update_age(message: Message, state: FSMContext):
    new_age = message.text.strip()

    if not new_age.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число).")
        return

    new_age = int(new_age)
    if new_age < 16:
        await message.answer("Возраст должен быть не менее 16 лет.")
        return

    user_id = message.from_user.id

    menu_command = await re_kb.get_menu_keyboard(user_id)
    await hf.update_user_field(user_id, 'age', new_age)
    await state.clear()
    await message.answer("Ваш возраст успешно обновлен!", reply_markup=menu_command)
    
@call_router.message(SetInfo.updating_city)
async def update_city(message: Message, state: FSMContext):
    new_city = message.text.strip()
    user_id = message.from_user.id

    menu_command = await re_kb.get_menu_keyboard()
    await hf.update_user_field(user_id, 'city', new_city)
    await state.clear()
    await message.answer("Ваш город успешно обновлен!", reply_markup=menu_command)

@call_router.message(SetInfo.updating_description)
async def update_description(message: Message, state: FSMContext):
    new_description = message.text.strip()
    user_id = message.from_user.id

    menu_command = await re_kb.get_menu_keyboard(user_id)
    await hf.update_user_field(user_id, 'description', new_description)
    await state.clear()
    await message.answer("Ваше описание успешно обновлено!", reply_markup=menu_command)
    
@call_router.message(F.text == 'Отключить анкету')
async def disable_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Обновляем статус в таблице 'users'
        await cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('Отключено', user_id))
        await conn.commit()
    await conn.close()
    menu_keyboard = await re_kb.get_menu_keyboard(user_id)
    await message.answer("Ваша анкета отключена и больше не будет показываться другим пользователям.", reply_markup=menu_keyboard)
    
@call_router.message(F.text == 'Включить анкету')
async def enable_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Обновляем статус в таблице 'users'
        await cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('Включено', user_id))
        await conn.commit()
    await conn.close()
    menu_keyboard = await re_kb.get_menu_keyboard(user_id)
    await message.answer("Ваша анкета включена и будет показываться другим пользователям.", reply_markup=menu_keyboard)

    
@call_router.message(F.text == 'Отмена')
async def cancel_editing(message: Message, state: FSMContext):
    user_id = message.from_user.id
    menu_command = await re_kb.get_menu_keyboard(user_id)
    await state.clear()
    await message.answer("Редактирование отменено.", reply_markup=menu_command)