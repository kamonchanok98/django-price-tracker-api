from django.db import models


# Create your models here.
class FileMaster(models.Model):
    """เก็บข้อมูลไฟล์ในระบบ"""

    class Meta:
        ordering = ["-id"]

    file_uuid = models.UUIDField(unique=True, editable=False)  # ID กลางของไฟล์
    original_name = models.CharField(max_length=50, default="")
    file_size = models.PositiveBigIntegerField(
        help_text="File size in bytes", default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)


class FileStorageLocation(models.Model):
    """เก็บข้อมูลว่าไฟล์นี้ถูกเก็บไว้ที่ไหนบ้าง"""

    class Meta:
        ordering = ["-last_synced"]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("pending", "Pending"),
    ]

    file_master = models.ForeignKey(
        "FileMaster", related_name="locations", on_delete=models.CASCADE
    )
    provider = models.CharField(max_length=20)
    storage_path = models.CharField(max_length=500)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",  # กำหนดค่าเริ่มต้นตอนสร้างข้อมูลใหม่
    )

    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(auto_now=True)
