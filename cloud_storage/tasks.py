import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from celery import shared_task
from django.conf import settings

from cloud_storage.models import FileStorageLocation

from .models import FileStorageLocation


@shared_task
def upload_to_s3_task(location_id):
    try:
        # ดึงข้อมูล location จาก DB โดยใช้ ID
        location = FileStorageLocation.objects.get(id=location_id)
        local_file_path = location.storage_path

        # ดึงชื่อไฟล์เดิมจาก path ชั่วคราว หรือดึงจาก field ที่เก็บชื่อเดิมไว้
        original_filename = os.path.basename(local_file_path)

        # สร้าง S3 Key
        s3_key = f"uploads/{original_filename}"

        # 4. อัปโหลดขึ้น S3
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        s3_client = boto3.client("s3")
        # สั่งอัปโหลดไฟล์ไปยัง S3
        with open(local_file_path, "rb") as file_obj:
            s3_client.upload_fileobj(file_obj, bucket_name, s3_key)
            print("successs")

        # อัปเดตสถานะเมื่ออัปโหลดสำเร็จ
        location.status = "pending"
        location.storage_path = s3_key  # อัปเดต path ให้เป็น S3 Key จริง
        location.save()

    except (
        FileStorageLocation.DoesNotExist,
        BotoCoreError,
        ClientError,
        Exception,
    ) as e:
        # พิมพ์ Error ออกมาดูใน Log ของ Celery Worker
        print(f"--- S3 UPLOAD ERROR ---: {str(e)}")
        # หากเกิดปัญหา ให้อัปเดตสถานะเป็น failed
        if "location" in locals():
            location.status = "failed"
            location.is_active = False
            location.save()
    finally:
        # ลบไฟล์ชั่วคราวบน Local Disk เพื่อไม่ให้ดิสก์เต็ม
        if "local_file_path" in locals() and os.path.exists(local_file_path):
            os.remove(local_file_path)
