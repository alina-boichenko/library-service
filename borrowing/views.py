from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.permissions import IsAdminOrReadOnly
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
    permission_classes = (IsAuthenticated, IsAdminOrReadOnly)
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
