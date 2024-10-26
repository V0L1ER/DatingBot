from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def look_profile(user_id):
    look = InlineKeyboardBuilder()
    look.add(InlineKeyboardButton(text="Посмотреть профиль", callback_data=f'look/{user_id}'))
    return look.as_markup()