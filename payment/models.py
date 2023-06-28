from django.db import models

from borrowing.models import Borrowing


class Payment(models.Model):
    STATUS = [
        ("PENDING", "pending"),
        ("PAID", "paid")
    ]
    TYPE = [
        ("PAYMENT", "payment"),
        ("FINE", "fine")
    ]
    status = models.CharField(choices=STATUS, default="pending", max_length=7)
    type = models.CharField(choices=TYPE, max_length=7)
    borrowing = models.ForeignKey(
        Borrowing, related_name="payments", on_delete=models.CASCADE
    )
    session_url = models.TextField()
    session_id = models.TextField()
    money_to_pay = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.borrowing}: {self.status}"
