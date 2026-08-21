import os
import tempfile
import uuid
from unittest.mock import patch

from botocore.exceptions import ClientError
from django.contrib.auth import get_user_model
from django.test import TestCase

from cloud_storage.models import FileMaster, FileStorageLocation
from cloud_storage.tasks import upload_to_s3_task

User = get_user_model()


class CeleryTaskUploadTest(TestCase):

    def setUp(self):
        # 📁 สร้างไฟล์ชั่วคราวบนดิสก์จริงๆ เพื่อให้บล็อก finally ลบได้
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        self.temp_file.close()  # ปิดไฟล์ชั่วคราวก่อนเพื่อให้ task เปิดอ่านได้
        # 🗄️ Create a test record in our test database
        unique_prefix = uuid.uuid4()
        file_master = FileMaster.objects.create(
            file_uuid=unique_prefix,
            original_name="test_file.jpg",
            file_size=100,
        )
        self.location = FileStorageLocation.objects.create(
            file_master=file_master,
            storage_path=self.temp_file.name,
        )

    def tearDown(self):
        # 🧹 ทำความสะอาดลบไฟล์ชั่วคราวหลังเทสเสร็จ (เผื่อกรณีที่ task ยังไม่ได้ลบ)
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    @patch("cloud_storage.tasks.boto3.client")
    def test_upload_to_s3_task_success(self, mock_boto_client):
        # ⚙️ Call the task using the ID of our created record
        upload_to_s3_task(self.location.id)

        # 🔍 Verify boto3 client was initialized
        mock_boto_client.assert_called_once_with("s3")

    @patch("cloud_storage.tasks.boto3.client")
    def test_upload_to_s3_task_does_not_exist(self, mock_boto_client):
        # ตรวจสอบว่าเมื่อส่ง ID ที่ผิด ฟังก์ชันจะ log ข้อความ error ออกมา
        with self.assertLogs("cloud_storage.tasks", level="ERROR") as cm:
            upload_to_s3_task(9999)  # ID ที่ไม่มีจริง

        # ตรวจสอบว่า log มีข้อความที่บ่งบอกถึงความผิดพลาด
        self.assertTrue(any("Failed to upload" in msg for msg in cm.output))

    @patch("cloud_storage.tasks.boto3.client")
    def test_upload_to_s3_task_s3_error(self, mock_boto_client):
        # 🎭 กำหนดให้ boto3 client.upload_fileobj โยน ClientError ออกมา
        mock_s3_instance = mock_boto_client.return_value
        mock_s3_instance.upload_fileobj.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "InternalError"}}, "upload_fileobj"
        )

        # รัน task และตรวจสอบผลลัพธ์
        upload_to_s3_task(self.location.id)

        # 🔍 รีเฟรชข้อมูลจากฐานข้อมูลเพื่อเช็คสถานะ
        self.location.refresh_from_db()
        self.assertEqual(self.location.status, "failed")
        self.assertEqual(self.location.is_active, False)
