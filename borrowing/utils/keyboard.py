from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

inline_button_active_borrowing = InlineKeyboardButton(
    "My active borrowing", callback_data="active"
)
inline_button_overdue_borrowing = InlineKeyboardButton(
    "My overdue borrowing", callback_data="overdue"
)
inline_keyboard = InlineKeyboardMarkup()
inline_keyboard.add(inline_button_active_borrowing)
inline_keyboard.add(inline_button_overdue_borrowing)
