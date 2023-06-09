from django.db import transaction
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingListSerializer, CreateBorrowingSerializer, BorrowingDetailSerializer


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Borrowing.objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateBorrowingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff is False:
            return Borrowing.objects.filter(user=user)

        return Borrowing.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        return CreateBorrowingSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user_id = self.request.user.id
        book_id = request.data["book"]
        expected_return_date = request.data["expected_return_date"]
        borrowed_book = Book.objects.get(pk=book_id)

        if borrowed_book.inventory != 0:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            Borrowing.objects.create(user_id=user_id, book_id=book_id, expected_return_date=expected_return_date)
            borrowed_book.inventory -= 1
            borrowed_book.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"detail": "No books available"}, status=status.HTTP_400_BAD_REQUEST)
