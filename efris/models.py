from django.db import models



class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50)
    description = models.TextField()
    code = models.CharField(max_length=20)
    request = models.TextField()
    response = models.TextField()
    request_message = models.TextField()
    response_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number
