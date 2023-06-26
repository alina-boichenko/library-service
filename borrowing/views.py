import datetime

import stripe
from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiResponse
)
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.models import Book
from borrowing.management.commands.bot import send_payment_confirmation
from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingListSerializer,
    CreateBorrowingSerializer,
    BorrowingDetailSerializer,
    ReturnBorrowedBookSerializer,
)
from payment.models import Payment
from payment.serializers import PaymentSerializer, PaymentCreateSerializer
from user.models import User

FINE_MULTIPLIER = 2


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

        if self.action == "success_payment":
            return PaymentCreateSerializer

        return CreateBorrowingSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user_id = self.request.user.id
        book_id = request.data["book"]
        expected_return_date = request.data["expected_return_date"]
        borrowed_book = Book.objects.get(pk=book_id)

        if expected_return_date <= str(datetime.date.today()):
            message = "You cannot select an expected return date in the past"
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST
            )

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

    @extend_schema(
        responses=PaymentSerializer
    )
    @action(methods=["POST", "GET"], detail=True, url_path="success")
    def success_payment(self, request, pk=None):
        """
        Create a new Stripe Session, calculate the total price of borrowing and
        create a new payment. User can see only his own payments,
        the admin can see all payments.
        """
        with transaction.atomic():
            stripe.api_key = settings.STRIPE_API_KEY
            host = settings.HOST
            borrowing_id = pk
            borrowing = get_object_or_404(Borrowing, id=pk)
            serializer = self.get_serializer(borrowing, data=request.data)
            serializer.is_valid(raise_exception=True)

            book_title = borrowing.book.title
            borrow_date = borrowing.borrow_date
            daily_fee = borrowing.book.daily_fee
            expected_return_date = borrowing.expected_return_date
            today = datetime.date.today()
            unit_amount = (expected_return_date - borrow_date).days * daily_fee

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "USD",
                            "product_data": {
                                "name": book_title,
                            },
                            "unit_amount": int(unit_amount) * 100,
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "product_id": borrowing_id
                },
                mode="payment",
                success_url=f"{host}{borrowing_id}/success/",
                cancel_url=f"{host}{borrowing_id}/cancel/"
            )

            payment = Payment.objects.create(
                status="PAID",
                type="PAYMENT",
                borrowing=borrowing,
                session_url=session.success_url,
                session_id=session["id"],
                money_to_pay=session["amount_total"]
            )

            if today > expected_return_date:
                fine_day = (today - expected_return_date).days
                fine_pay = fine_day * daily_fee * FINE_MULTIPLIER
                payment.money_to_pay += fine_pay
                payment.type = "FINE"

            payment.save()

            user = User.objects.get(id=self.request.user.id)
            if user.telegram_id:
                async_to_sync(send_payment_confirmation)(
                    user.telegram_id, book_title, payment.money_to_pay
                )

            message = f"Payment for borrowing {book_title} was successful!"
            return Response({"detail": message}, status=status.HTTP_200_OK)

    @extend_schema(
        responses=OpenApiResponse(OpenApiTypes.STR),
    )
    @action(methods=["GET"], detail=True, url_path="cancel")
    def cancel_payment(self, request, pk=None):
        """
        Display message to user that the payment can be completed
        within 24 hours.
        """
        message = "You can pay a bit later, but you must pay within 24 hours"
        return Response({"detail": message}, status=status.HTTP_200_OK)

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
                if borrowing.actual_return_date <= datetime.date.today():
                    message = "You cannot select an return date in the past"
                    return Response(
                        {"detail": message},
                        status=status.HTTP_400_BAD_REQUEST
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
