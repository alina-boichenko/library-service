import datetime

from rest_framework import serializers

from borrowing.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
        )


class BorrowingDetailSerializer(BorrowingListSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user"
        )


class CreateBorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "book",
            "expected_return_date",
        )

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()
        return super().create(validated_data)

    def validate(self, data):
        if data["expected_return_date"] <= datetime.date.today():
            raise serializers.ValidationError(
                "You cannot select an expected return date in the past"
            )
        book = data["book"]
        if book.inventory == 0:
            raise serializers.ValidationError(
                "No books available!"
            )
        return data


class ReturnBorrowedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("actual_return_date",)

    def validate(self, data):
        today = datetime.date.today()
        if data["actual_return_date"] < today:
            raise serializers.ValidationError({
                "actual_return_date":
                "You cannot select an return date in the past."
            })

        borrow = self.instance
        book = borrow.book
        if borrow.actual_return_date:
            raise serializers.ValidationError(
                {"actual_return_date": "You cannot return borrowing twice"}
            )
        book.inventory += 1
        book.save()
        return data
