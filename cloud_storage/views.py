import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from cloud_storage.models import FileMaster, FileStorageLocation
from cloud_storage.serializers import FileUploadSerializer
from cloud_storage.tasks import upload_to_s3_task

temp_storage = FileSystemStorage(location="/tmp/my_temp_files")


class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = FileUploadSerializer

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=400)

        # 1. บันทึกไฟล์ไว้ใน Local Storage ชั่วคราว
        unique_prefix = uuid.uuid4()
        unique_filename = f"{unique_prefix}_{file_obj.name}"
        saved_name = temp_storage.save(unique_filename, file_obj)
        full_temp_path = temp_storage.path(saved_name)

        # 2. สร้าง Record ใน DB เก็บ path ชั่วคราว และสถานะเป็น 'pending'
        with transaction.atomic():
            file_master = FileMaster.objects.create(
                file_uuid=unique_prefix,
                original_name=file_obj.name,
                file_size=file_obj.size,
            )
            location = FileStorageLocation.objects.create(
                file_master=file_master,
                provider="S3",
                storage_path=full_temp_path,
                status="pending",
            )

        # 3. เรียก Task โดยส่งไปแค่ ID
        upload_to_s3_task.delay(location.id)

        return Response({"message": "Upload queued", "location_id": location.id})
