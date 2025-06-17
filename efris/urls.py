from django.urls import path
from .views import InvoiceAPIView, landing_page

urlpatterns = [
    path('api/efris/', InvoiceAPIView.as_view(), name='api-invoices'),
    path('', landing_page, name='landing'),
]
