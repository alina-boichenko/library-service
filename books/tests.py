from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer

BOOK_URL = reverse("books:book-list")


def sample_book(**params):
    defaults = {
        "author": "Tom Pain",
        "cover": "HARD",
        "inventory": 1,
        "daily_fee": "1.00"
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(BOOK_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "new@user.com", "password123A"
        )
        self.client.force_authenticate(self.user)
        self.book_1 = sample_book(title="First book")
        self.book_2 = sample_book(title="Second book")
        self.book_3 = sample_book(title="Third book")

        self.serializer_1 = BookSerializer(self.book_1)
        self.serializer_2 = BookSerializer(self.book_2)
        self.serializer_3 = BookSerializer(self.book_3)

    def test_list_movies(self):
        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_forbidden(self):
        new_book = {
            "title": "New book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 2,
            "daily_fee": 2.00
        }

        response = self.client.post(BOOK_URL, new_book)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminMovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "new@admin.com",
            "password123A",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        new_book = {
            "title": "New book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 2,
            "daily_fee": 2.00
        }
        response = self.client.post(BOOK_URL, new_book)
        book = Book.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in new_book:
            self.assertEqual(new_book[key], getattr(book, key))

    def test_delete_book(self):
        book = sample_book()
        url = reverse("books:book-detail", args=[book.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
