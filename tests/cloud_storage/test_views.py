from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class FileUploadViewTest(APITestCase):
    def setUp(self):
        # 👤 สร้าง User และยืนยันตัวตน
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)

    @patch("cloud_storage.views.upload_to_s3_task.delay")
    def test_file_upload_success(self, mock_celery_task):
        # 🌐 Get the URL using the namespace and name defined in urls.py
        url = reverse("cloud_storage:upload")

        # 📁 Create a simple mock file for testing
        file_content = b"fake image content"
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg", file_content, content_type="image/jpeg"
        )

        data = {"file": uploaded_file}
        response = self.client.post(url, data, format="multipart")

        # 🔍 Assertions to verify correct behavior
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_celery_task.assert_called_once()

    @patch("cloud_storage.views.upload_to_s3_task.delay")
    def test_file_upload_no_file(self, mock_celery_task):
        # 🌐 Get the URL
        url = reverse("cloud_storage:upload")

        # 📁 ส่งข้อมูลว่างเปล่าโดยไม่มีไฟล์แนบ
        data = {}
        response = self.client.post(url, data, format="multipart")

        # 🔍 ตรวจสอบผลลัพธ์ว่าได้ Status 400 และไม่เรียกใช้งาน Celery Task
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No file uploaded")
        mock_celery_task.assert_not_called()
