from django.urls import include, path

from cloud_storage.views import FileUploadView

app_name = "cloud_storage"

urlpatterns = [
    path("file_upload/", FileUploadView.as_view(), name="upload"),
]
