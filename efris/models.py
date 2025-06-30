from django.db import models

class InvoiceRecord(models.Model):
    tin = models.CharField(max_length=20)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice for TIN: {self.tin} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
