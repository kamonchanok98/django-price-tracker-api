from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cloud_storage.views import FileStatusViewSet, FileUploadView

app_name = "cloud_storage"

router = DefaultRouter()
router.register(r"files", FileStatusViewSet, basename="files")

urlpatterns = [
    path("file_upload/", FileUploadView.as_view(), name="upload"),
    path("", include(router.urls)),
]
