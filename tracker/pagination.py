from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DynamicPagination(PageNumberPagination):
    page_size = 20  # ⚙️ ค่าเริ่มต้น 20 รายการต่อหน้า
    page_size_query_param = "limit"  # ⚙️ อนุญาตให้ผู้ใช้กำหนด ?limit= เองได้
    max_page_size = 100  # 🛡️ ป้องกันการใส่ limit มหาศาล

    def paginate_queryset(self, queryset, request, view=None):
        offset = request.query_params.get("offset")
        limit = request.query_params.get("limit") or self.page_size

        # 🔄 ถ้าผู้ใช้ส่ง ?offset= มา ให้แปลงเป็นเลขหน้า ?page=
        if offset is not None:
            try:
                offset_val = int(offset)
                limit_val = int(limit)

                # คำนวณเลขหน้าจาก offset
                page_num = (offset_val // limit_val) + 1

                # จำลอง query_params ใหม่ให้ DRF เข้าใจเป็นระบบ page
                request.query_params._mutable = True
                request.query_params[self.page_query_param] = page_num
            except (ValueError, ZeroDivisionError):
                pass

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("page_number", self.page.number),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
