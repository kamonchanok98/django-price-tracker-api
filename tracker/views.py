from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, PriceHistory
from .serializers import ProductSerializer, PriceHistorySerializer
from .scraper import scrape_and_update_product

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only see and manage their own tracked products
        return Product.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user as product owner
        serializer.save(user=self.request.user)


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PriceHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter price histories belonging to the authenticated user's products
        return PriceHistory.objects.filter(product__user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='scrape')
    def trigger_scrape(self, request, pk=None):
        """Endpoint: POST /api/products/{id}/scrape/"""
        product = self.get_object()
        result = scrape_and_update_product(product)

        if result["success"]:
            return Response({
                "message": "Price updated successfully",
                "current_price": str(result["price"]),
                "target_met": result["target_met"]
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": result["error"]
            }, status=status.HTTP_400_BAD_REQUEST)