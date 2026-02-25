from django.db import models
from django.utils import timezone


class UploadKind(models.TextChoices):
    PRINT = "PRINT", "PRINT"
    FRAME = "FRAME", "FRAME"
    GIF = "GIF", "GIF"
    VIDEO = "VIDEO", "VIDEO"
    ORIGINAL = "ORIGINAL", "ORIGINAL"


class UploadAsset(models.Model):
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE)
    share = models.ForeignKey("mediahub.ShareSession", on_delete=models.CASCADE, related_name="uploads")
    kind = models.CharField(max_length=16, choices=UploadKind.choices)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/", blank=True, null=True)
    storage_backend = models.CharField(max_length=16, default="local")
    object_key = models.CharField(max_length=512, blank=True, default="")
    original_filename = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=128, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["kind", "created_at"])]

    def __str__(self):
        return f"{self.kind}:{self.file.name}"
