from rest_framework import serializers

from accounts.serializers import UserProfileSerializer
from tracker.models import PriceHistory, Product


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ["id", "price", "recorded_at"]
        read_only_fields = ["id", "price", "recorded_at"]


class ProductSerializer(serializers.ModelSerializer):
    # Mark the nested user representation as read-only
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "user",
            "name",
            "url",
            "target_price",
            "current_price",
            "created_at",
        ]
        # Include current_price so users can't manually forge it via POST/PUT
        read_only_fields = ["id", "current_price", "created_at"]
