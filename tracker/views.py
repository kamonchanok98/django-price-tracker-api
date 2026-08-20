from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.models import Product
from tracker.serializers import PriceHistorySerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 🔗 เพิ่ม select_related('user') เพื่อแก้ N+1 Query
        return Product.objects.filter(user=self.request.user).select_related("user")

    def perform_create(self, serializer):
        # Automatically tie created product to the logged-in user
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """GET /api/products/{id}/history/ - Fetch historical price trend points."""
        product = self.get_object()
        history_qs = product.price_history.all().order_by("-recorded_at")
        serializer = PriceHistorySerializer(history_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
