from django.conf import settings
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField(blank=True, null=True)
    actual_return_date = models.DateField(blank=True, null=True)
    book = models.ForeignKey(
        Book,
        related_name="borrowing",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="borrowing",
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"{self.user.email} borrowed the book {self.book.title}"
