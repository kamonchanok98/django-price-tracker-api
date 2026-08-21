from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tracker.views import ProductViewSet

app_name = "tracker"

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
