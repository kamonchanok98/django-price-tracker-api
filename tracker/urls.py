from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, PriceHistoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'price-history', PriceHistoryViewSet, basename='pricehistory')

urlpatterns = [
    path('', include(router.urls)),
]