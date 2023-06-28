from rest_framework import serializers

from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="borrowing.book.title")
    user = serializers.CharField(source="borrowing.user.email")

    class Meta:
        model = Payment
        fields = (
            "id",
            "book",
            "user",
            "status",
            "type",
            "session_url",
            "session_id",
            "money_to_pay"
        )


class PaymentCreateSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.CharField(source="borrowing.id", read_only=True)

    class Meta:
        model = Payment
        fields = ("borrowing_id",)
