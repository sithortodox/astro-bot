from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("numerology"))
async def cmd_numerology(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        "\U0001f52e Используй меню для нумерологического анализа.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f52e Нумерология", callback_data="menu:numerology")]
        ])
    )
