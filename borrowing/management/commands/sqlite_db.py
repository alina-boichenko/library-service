import os
import sqlite3
from datetime import datetime

from django.conf import settings

db_path = os.path.join(settings.BASE_DIR, "db.sqlite3")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


def get_books(books_id):
    cursor.execute("SELECT * FROM books_book")
    rows = cursor.fetchall()
    books = ""
    column_book_id = 0
    column_title = 1
    column_author = 2
    for book_id in books_id:
        for row in rows:
            if row[column_book_id] == book_id:
                books += row[column_title] + " (" + row[column_author] + ")\n"
    return books


async def get_active_borrowing(user_id: int):
    cursor.execute(
        "SELECT * FROM borrowing_borrowing WHERE user_id=?", (user_id,)
    )
    rows = cursor.fetchall()

    if rows:
        books_id = []
        column_book_id = 4
        for row in rows:
            book_id = row[column_book_id]
            books_id.append(book_id)
        result = "Your active borrowings: \n" + get_books(books_id)
        return result

    else:

        return "You have no active borrowings!"


async def get_overdue_borrowing(user_id: int):
    cursor.execute(
        "SELECT * FROM borrowing_borrowing WHERE user_id=?", (user_id,)
    )
    rows = cursor.fetchall()

    if rows:
        books_id = []
        today = datetime.now()
        column_expected_return = 1
        column_actual_return = 2
        column_book_id = 4
        for row in rows:
            if (
                row[column_actual_return] is None
                and row[column_expected_return] < today.strftime("%Y-%m-%d")
            ):
                book_id = row[column_book_id]
                books_id.append(book_id)
            result = "Your overdue borrowings: \n" + get_books(books_id)
            return result

    else:

        return "You have no overdue borrowing!"
