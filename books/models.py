from django.db import models


class Book(models.Model):
    COVER_TYPE = [
        ("HARD", "Hard"),
        ("SOFT", "Soft")
    ]
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=255)
    cover = models.CharField(choices=COVER_TYPE, max_length=4)
    inventory = models.PositiveIntegerField(verbose_name="number of books available")
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.title} ({self.author})"
