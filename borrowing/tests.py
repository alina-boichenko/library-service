from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingListSerializer

BORROWING_URL = reverse("borrowing:borrowing-list")


def sample_book(**params):
    defaults = {
        "author": "Ann Holand",
        "cover": "HARD",
        "inventory": 1,
        "daily_fee": "3.00"
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(BORROWING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user_1 = get_user_model().objects.create_user(
            "new@user.com", "password123A", is_staff=True
        )
        self.user_2 = get_user_model().objects.create_user(
            "one@user.com", "password123A"
        )
        self.book_1 = sample_book(title="First book")
        self.book_2 = sample_book(title="Second book")
        self.serializer_1 = BookSerializer(self.book_1)
        self.serializer_2 = BookSerializer(self.book_2)

        self.client.force_authenticate(self.user_1)
        self.borrowed_book_1 = Borrowing.objects.create(
            book=self.book_1,
            user=self.user_1
        )
        self.serializer_borrowed_1 = BorrowingListSerializer(
            self.borrowed_book_1
        )

    def test_list_borrowed_books(self):
        response = self.client.get(BORROWING_URL)
        borrowed_books = Borrowing.objects.filter(user=self.user_1)
        serializer = BorrowingListSerializer(borrowed_books, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_add_borrowed_book_only_to_own_profile(self):
        new_borrowing = {
            "book": self.book_2.id,
            "user": self.user_2.id,
            "expected_return_date": "2023-07-01",
            "actual_return_date": "2023-06-29"
        }
        response = self.client.post(BORROWING_URL, new_borrowing)
        borrowings = Borrowing.objects.filter(user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(borrowings)

    def test_filter_borrowings_by_is_active(self):
        response = self.client.get(BORROWING_URL, {"is_active": "null"})
        self.assertIn(self.serializer_borrowed_1.data, response.data)

    def test_filter_borrowings_by_user_id_for_admin(self):
        response = self.client.get(BORROWING_URL, {"user_id": "2"})
        borrowed_books = Borrowing.objects.filter(user=self.user_2)
        serializer = BorrowingListSerializer(borrowed_books, many=True)
        self.assertEqual(serializer.data, response.data)

    def test_return_book(self):
        url = f"/api/borrowings/{self.borrowed_book_1.pk}/return/"
        data = {
            "actual_return_date": "2023-06-01"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowed_book_1.refresh_from_db()
        self.assertIsNotNone(self.borrowed_book_1.actual_return_date)

        self.book_1.refresh_from_db()
        self.assertEqual(self.book_1.inventory, 2)
