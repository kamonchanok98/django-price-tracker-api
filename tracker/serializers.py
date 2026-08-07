from rest_framework import serializers
from .models import Product, PriceHistory

class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'price', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']


class ProductSerializer(serializers.ModelSerializer):
    # Includes recent price history records in product response
    price_history = PriceHistorySerializer(many=True, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Product
        fields = ['id', 'user', 'name', 'url', 'image_url', 'target_price', 'created_at', 'updated_at', 'price_history']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'price_history']