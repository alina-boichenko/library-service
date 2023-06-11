from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingListSerializer,
    CreateBorrowingSerializer,
    BorrowingDetailSerializer,
    ReturnBorrowedBookSerializer,
)


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
        queryset = self.queryset

        if user.is_staff is False:
            queryset.filter(user=user)

        if user.is_staff:
            user_id = self.request.query_params.get("user_id")

            if user_id:
                queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")

        if is_active:
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "return_book":
            return ReturnBorrowedBookSerializer

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
            Borrowing.objects.create(
                user_id=user_id,
                book_id=book_id,
                expected_return_date=expected_return_date
            )
            borrowed_book.inventory -= 1
            borrowed_book.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"detail": "No books available"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=["POST"], detail=True, url_path="return")
    def return_book(self, request, pk=None):
        with transaction.atomic():
            borrowing = self.get_object()

            if not borrowing.actual_return_date:
                serializer = self.get_serializer(borrowing, data=request.data)
                serializer.is_valid(raise_exception=True)
                borrowing.actual_return_date = serializer.validated_data.get(
                    "actual_return_date"
                )
                borrowing.save()

                book_id = borrowing.book_id
                book = get_object_or_404(Book, id=book_id)
                book.inventory += 1
                book.save()

                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response({"detail": "You cannot return borrowing twice"})

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=str,
                description="Filter by active borrowings (still not returned) "
                            "(ex. ?is_active=null)"
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                description="Parameter for admin users, filter by user id"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
