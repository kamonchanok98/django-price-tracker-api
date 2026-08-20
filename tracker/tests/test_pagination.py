from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Product

User = get_user_model()


class DynamicPaginationTestCase(APITestCase):

    def setUp(self):
        # 👤 สร้าง User และยืนยันตัวตน
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        # 📦 สร้างสินค้าจำลอง 25 ชิ้นรวดเดียวด้วย bulk_create
        products = [
            Product(
                user=self.user,
                name=f"Product {i}",
                url=f"https://example.com/{i}",
            )
            for i in range(1, 26)
        ]
        Product.objects.bulk_create(products)

    def test_default_pagination(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # 📦 หน้าแรกมี 20 ชิ้น
        self.assertEqual(response.data["total_pages"], 2)  # 📄 รวมทั้งหมดมี 2 หน้า
        self.assertEqual(response.data["count"], 25)  # 📊 สินค้าทั้งหมด 25 ชิ้น
        self.assertEqual(response.data["page_number"], 1)  # 📍 ปัจจุบันอยู่หน้า 1

    def test_custom_limit_offset_pagination(self):
        # 🎯 ส่ง limit=5 และ offset=10
        response = self.client.get("/api/products/?limit=5&offset=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)  # 📦 ดึงมา 5 ชิ้น
        self.assertEqual(response.data["page_number"], 3)  # 📍 อยู่หน้าที่ 3
        self.assertEqual(
            response.data["total_pages"], 5
        )  # 📄 25 ชิ้น หารทีละ 5 = 5 หน้า
        self.assertEqual(response.data["count"], 25)  # 📊 ข้อมูลทั้งหมด 25 ชิ้น

    def test_invalid_pagination_parameters(self):
        # 🎯 ส่ง parameter ที่ผิดพลาดเพื่อทดสอบ try...except
        response = self.client.get("/api/products/?limit=0&offset=invalid")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 20
        )  # กลับไปใช้ default page_size
