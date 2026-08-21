from rest_framework import serializers

from cloud_storage.models import FileMaster, FileStorageLocation


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class FileStorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorageLocation
        fields = [
            "id",
            "provider",
            "storage_path",
            "status",
            "is_active",
            "last_synced",
        ]
        read_only_fields = fields


class FileMasterSerializer(serializers.ModelSerializer):
    locations = FileStorageLocationSerializer(many=True, read_only=True)

    class Meta:
        model = FileMaster
        fields = [
            "id",
            "file_uuid",
            "original_name",
            "file_size",
            "created_at",
            "locations",
        ]
        read_only_fields = fields
