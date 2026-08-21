import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cloud_storage.models import FileMaster, FileStorageLocation

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


class FilesViewsetTest(APITestCase):
    def setUp(self):
        # 👤 สร้าง User และยืนยันตัวตน
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        # 🗄️ Create a test record in our test database
        unique_prefix = uuid.uuid4()
        self.file_master = FileMaster.objects.create(
            user=self.user,
            file_uuid=unique_prefix,
            original_name="test_file.jpg",
            file_size=100,
        )
        self.location = FileStorageLocation.objects.create(
            file_master=self.file_master,
            storage_path="test_file.jpg",
            status="success",
            is_active=True,
        )

    def test_retrieve_file_success(self):
        url = reverse("cloud_storage:files-detail", args=[self.file_master.file_uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["original_name"], self.file_master.original_name)
        self.assertEqual(response.data["file_size"], self.file_master.file_size)

        self.assertEqual(len(response.data["locations"]), 1)
        self.assertEqual(response.data["locations"][0]["status"], "success")
        self.assertEqual(response.data["locations"][0]["is_active"], True)


class FileStatusViewSetTestCase(APITestCase):
    def setUp(self):
        # 1. Create Users (User A & User B to test user isolation)
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="password123"
        )

        # 2. Create File for main user
        self.file_uuid = uuid.uuid4()
        self.file_master = FileMaster.objects.create(
            file_uuid=self.file_uuid,
            user=self.user,
            original_name="example.txt",
        )

        # 3. Create Locations with different status & is_active flags
        # Matching location: status="success" AND is_active=True
        self.matching_location = FileStorageLocation.objects.create(
            file_master=self.file_master,
            status="success",
            is_active=True,
            provider="AWS",
        )

        # Non-matching location (status != success)
        self.failed_location = FileStorageLocation.objects.create(
            file_master=self.file_master,
            status="failed",
            is_active=True,
            provider="GCP",
        )

        # Non-matching location (is_active != True)
        self.inactive_location = FileStorageLocation.objects.create(
            file_master=self.file_master,
            status="success",
            is_active=False,
            provider="Azure",
        )

        # 4. Create File belonging to another user
        self.other_file = FileMaster.objects.create(
            file_uuid=uuid.uuid4(),
            user=self.other_user,
            original_name="other_user_file.txt",
        )

        # Set router base name (adjust 'file-status' to match your urls.py)
        self.list_url = reverse("cloud_storage:files-list")
        self.detail_url = reverse("cloud_storage:files-detail", args=[self.file_uuid])

    def test_unauthenticated_user_access(self):
        """Verify unauthenticated users are blocked."""
        response = self.client.get(self.list_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_list_files_only_returns_user_owned_files(self):
        """Verify list queryset filters by request.user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_uuid"], str(self.file_uuid))

    def test_retrieve_file_status_success_and_prefetch_filtering(self):
        """Verify detail endpoint retrieves file and prefetch only includes success/active locations."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["file_uuid"], str(self.file_uuid))

        # Check prefetch filtering: should only contain matching_location (1 out of 3)
        locations = response.data.get("locations", [])
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]["id"], self.matching_location.id)
        self.assertEqual(locations[0]["status"], "success")

    def test_retrieve_file_not_found_for_other_user(self):
        """Verify a user cannot retrieve files belonging to another user."""
        self.client.force_authenticate(user=self.user)
        other_detail_url = reverse(
            "cloud_storage:files-detail", args=[self.other_file.file_uuid]
        )

        response = self.client.get(other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_non_existent_uuid(self):
        """Verify 404 is returned when querying a random non-existent UUID."""
        self.client.force_authenticate(user=self.user)
        non_existent_url = reverse("cloud_storage:files-detail", args=[uuid.uuid4()])

        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
