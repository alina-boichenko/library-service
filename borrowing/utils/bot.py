from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from asgiref.sync import sync_to_async
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from django.conf import settings

from borrowing.management.commands.keyboard import inline_keyboard
from borrowing.management.commands.sqlite_db import (
    get_active_borrowing,
    get_overdue_borrowing
)
from borrowing.management.commands.states import LibraryStates
from user.models import User

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start", "help", "email"], state="*")
async def start(message: types.Message):
    await LibraryStates.START.set()
    if message.text == "/start":
        await bot.send_message(
            message.from_user.id,
            "Hello! Please enter your email for authentication."
        )
    elif message.text == "/help":
        await bot.send_message(
            message.from_user.id,
            "You can use the following commands in @li_bra_ry_bot:\n"
            "/start - to restart the bot \n"
            "/help - for instructions \n"
            "/library - view active or overdue borrowing"
        )
    else:
        await bot.send_message(
            message.from_user.id,
            "Please enter your email again."
        )


@dp.message_handler(state=LibraryStates.START)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)

    if message.text == "/library":
        await bot.send_message(
            message.from_user.id,
            "What would you like to know? "
            "Choose a command!",
            reply_markup=inline_keyboard
        )
    else:

        try:
            user = await sync_to_async(User.objects.get)(email=email)
            user.telegram_id = message.from_user.id
            await sync_to_async(user.save)()
            await bot.send_message(
                message.from_user.id,
                "You are registered! What would you like to know? "
                "Choose a command!",
                reply_markup=inline_keyboard
            )
        except User.DoesNotExist:
            await bot.send_message(
                message.chat.id,
                "Email entered incorrectly. "
                "Please enter the command /email and try again."
            )


@dp.callback_query_handler(
    lambda c: c.data in ["active", "overdue"], state="*"
)
async def process_command(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    command = callback_query.data
    telegram_id = callback_query.from_user.id
    user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)

    if command == "active":
        result = await get_active_borrowing(user.id)
        await bot.send_message(telegram_id, result)

    elif command == "overdue":
        result = await get_overdue_borrowing(user.id)
        await bot.send_message(telegram_id, result)

    else:
        await bot.send_message(
            telegram_id, "I don't understand you. Choose correct command."
        )


async def send_payment_confirmation(telegram_id, book_title, money):
    await bot.send_message(
        telegram_id,
        f"You just successfully paid borrowing book {book_title}."
        f" Paid {money}usd."
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
