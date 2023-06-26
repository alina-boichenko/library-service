import datetime
import os
import sys

from telebot import TeleBot, types
from django.conf import settings
from borrowing.models import Borrowing
from user.models import User
import django

sys.path.append("library_service/")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_service.settings')
django.setup()

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
bot = TeleBot(token=TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start"])
@bot.message_handler(content_types=["text"])
def get_email(message):
    telegram_id = message.chat.id
    if User.objects.get(telegram_id=telegram_id):
        message_reply(message)
    else:
        bot.send_message(
            message.chat.id,
            "Hello! Please enter your email for authentication."
        )
        bot.register_next_step_handler(message, choice_button)


@bot.message_handler(content_types=["text"])
def choice_button(message):
    email = message.text
    if User.objects.filter(email=email):
        user = User.objects.get(email=email)
        user.telegram_id = message.chat.id
        user.save()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        active_borrowing = types.KeyboardButton("My active borrowing")
        overdue = types.KeyboardButton("Borrowing are overdue")
        markup.row(active_borrowing, overdue)

        bot.send_message(
            message.chat.id,
            "You you are authenticated! Choose the next action:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, message_reply)

    else:
        bot.send_message(
            message.chat.id,
            "Email entered incorrectly. Use the /start command to try again."
        )


@bot.message_handler(content_types=["text"])
def message_reply(message):
    user = User.objects.get(telegram_id=message.chat.id)

    if message.text == "My active borrowing":
        result = Borrowing.objects.filter(
            user=user.id, actual_return_date__isnull=True
        )

        if result:
            for borrowing in result:
                bot.send_message(message.chat.id, borrowing)

        else:
            bot.send_message(message.chat.id, "You have no active borrowing.")

    if message.text == "Borrowing are overdue":
        today = datetime.datetime.now()
        result = Borrowing.objects.filter(
            user=user.id,
            actual_return_date__isnull=True,
            expected_return_date__lt=today
        )

        if result:
            for borrowing in result:
                bot.send_message(message.chat.id, borrowing)

        else:
            bot.send_message(message.chat.id, "You have no overdue borrowing.")

    else:
        bot.send_message(
            message.chat.id, "I don't understand you. Choose correct command."
        )


def send_payment_confirmation(chat_id):
    message = "Your payment has been received!"
    bot.send_message(chat_id=chat_id, text=message)


bot.infinity_polling()
